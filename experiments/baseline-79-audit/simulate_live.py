"""Reproduce the live browser recognition path offline.

The browser never sees a trimmed clip. It sees a continuous camera stream and
runs inference on the most recent 60 buffered frames (pushed every 125 ms).
This script rebuilds that path from recorded clips:

    [hold first frame x N]  +  clip frames  +  [hold last frame x N]

streamed one frame at a time into a 60-frame FIFO at the training sampling rate
(10 fps), with the app's TemporalStabilizer applied to each prediction.

Outputs, per class: does the subject's own clip ever commit, to what label, and
with what evidence. This is the honest measure of "can the 79-class baseline
recognise this sign in a live setting".

Usage:
    .venv_pilot/Scripts/python.exe experiments/baseline-79-audit/simulate_live.py [--pilot] [--classes HELLO,YES,NO] [--limit N]
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np
import onnxruntime as ort

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eval_baseline_79 import (FEATURES_DIR, MANIFEST, load_mapping, load_scalars, scale)  # noqa: E402

PILOT_ONNX = os.path.join(ROOT, 'web', 'public', 'spoter_pilot.onnx')
BASELINE_ONNX = os.path.join(ROOT, 'ai', 'sign-recognition', 'checkpoints', 'spoter_v2_model.onnx')
SEQ_LEN, DIM = 60, 366
PILOT_CLASSES = ['HELLO', 'YES', 'NO']

# Mirrors web/src/lib/temporalStabilizer.ts
PILOT_STABILIZER = dict(minimumCommitEvidence=0.65, minimumStableEvidence=0.40, dropThreshold=0.25,
                        minimumConfidence=0.20)
BASELINE_STABILIZER = dict(minimumCommitEvidence=0.25, minimumStableEvidence=0.15, dropThreshold=0.10,
                           minimumConfidence=0.05)
BASE = dict(windowMs=2000, maxObservations=60, minimumConfidence=0.2, minimumStableEvidence=0.4,
            minimumCommitEvidence=0.65, minimumStableObservations=2, minimumCommitObservations=3,
            minimumStableDurationMs=400, transitionMargin=0.15, dropThreshold=0.25)


class Stabilizer:
    def __init__(self, overrides):
        self.cfg = {**BASE, **overrides}
        self.buffer = []
        self.stable = None
        self.last_ts = -1
        self.last_committed = None

    def process(self, name, confidence, ts):
        assert ts >= self.last_ts
        self.last_ts = ts
        self.buffer.append((name, confidence, ts))
        cutoff = ts - self.cfg['windowMs']
        self.buffer = [p for p in self.buffer if p[2] >= cutoff][-self.cfg['maxObservations']:]
        total = 0.0
        scores = defaultdict(float)
        for n, c, t in self.buffer:
            w = 1.0 - ((ts - t) / self.cfg['windowMs'])
            total += w
            if c >= self.cfg['minimumConfidence']:
                scores[n] += c * w
        for n in list(scores):
            scores[n] = scores[n] / total if total > 0 else 0.0
        best, highest = None, 0.0
        for n, e in scores.items():
            if e > highest:
                best, highest = n, e
        duration = ts - self.buffer[0][2] if self.buffer else 0
        obs = len(self.buffer)
        commit = None
        if self.stable and scores.get(self.stable, 0) < self.cfg['dropThreshold']:
            self.stable = None
            self.last_committed = None
        if self.stable:
            cur = scores.get(self.stable, 0)
            if best and best != self.stable:
                if (scores[best] >= self.cfg['minimumStableEvidence']
                        and scores[best] > cur + self.cfg['transitionMargin']
                        and obs >= self.cfg['minimumStableObservations']
                        and duration >= self.cfg['minimumStableDurationMs']):
                    self.stable = best
        else:
            if (best and highest >= self.cfg['minimumStableEvidence']
                    and obs >= self.cfg['minimumStableObservations']
                    and duration >= self.cfg['minimumStableDurationMs']):
                self.stable = best
        evidence = 0.0
        if self.stable:
            evidence = scores.get(self.stable, 0)
            if evidence >= self.cfg['minimumCommitEvidence'] and obs >= self.cfg['minimumCommitObservations']:
                if self.stable != self.last_committed:
                    commit = self.stable
                    self.last_committed = self.stable
        return commit, self.stable, evidence, highest


def softmax(x):
    m = np.max(x)
    e = np.exp(x - m)
    return e / e.sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pilot', action='store_true', help='also simulate the 3-class pilot')
    ap.add_argument('--classes', default='', help='comma separated canonical names (default: all val classes)')
    ap.add_argument('--limit', type=int, default=0, help='max samples per class (0 = all)')
    ap.add_argument('--hold', type=int, default=45, help='neutral frames held before/after the clip')
    ap.add_argument('--out', default='live_simulation_results.json')
    args = ap.parse_args()

    by_asl, by_index = load_mapping()
    scalars = load_scalars()
    base_sess = ort.InferenceSession(BASELINE_ONNX, providers=['CPUExecutionProvider'])
    base_in = base_sess.get_inputs()[0].name
    pilot_sess = ort.InferenceSession(PILOT_ONNX, providers=['CPUExecutionProvider']) if args.pilot else None
    pilot_in = pilot_sess.get_inputs()[0].name if pilot_sess else None

    rows = []
    with open(MANIFEST, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split(',')
        for line in f:
            if line.strip():
                rows.append(dict(zip(header, line.strip().split(','))))

    wanted = [c for c in args.classes.split(',') if c] if args.classes else None
    per_class = defaultdict(lambda: {'clips': 0, 'committed': 0, 'committed_correct': 0,
                                     'committed_wrong': 0, 'no_commit': 0,
                                     'wrong_labels': Counter(), 'max_conf': 0.0,
                                     'pilot_committed_correct': 0, 'pilot_clips': 0})
    details = []

    for r in rows:
        if r['source_split'] != 'val':
            continue
        name = r['canonical_name']
        if name not in by_index.values():
            continue
        if wanted and name not in wanted:
            continue
        path = os.path.join(FEATURES_DIR, r['video_file'].replace('.mp4', '') + '_features.npy')
        if not os.path.exists(path):
            continue
        if args.limit and per_class[name]['clips'] >= args.limit:
            continue
        seq = scale(np.load(path).astype(np.float32), scalars)
        T = seq.shape[0]
        hold = args.hold
        stream = np.concatenate([np.repeat(seq[:1], hold, axis=0), seq, np.repeat(seq[-1:], hold, axis=0)])

        stab = Stabilizer(BASELINE_STABILIZER)
        pilot_stab = Stabilizer(PILOT_STABILIZER) if args.pilot else None
        buf = np.zeros((SEQ_LEN, DIM), dtype=np.float32)
        commits, pilot_commits, top_conf = [], [], 0.0
        for t, frame in enumerate(stream):
            buf = np.roll(buf, -1, axis=0)
            buf[-1] = frame
            ts = t * 100  # 10 fps, the sampling rate the training data was extracted at
            conf = softmax(base_sess.run(None, {base_in: buf[None]})[0][0])
            top = int(np.argmax(conf))
            top_conf = max(top_conf, float(conf[top]))
            commit, _, _, _ = stab.process(by_index[top], float(conf[top]), ts)
            if commit:
                commits.append(commit)
            if pilot_stab is not None:
                p_conf = softmax(pilot_sess.run(None, {pilot_in: buf[None]})[0][0])
                pt = int(np.argmax(p_conf))
                p_commit, _, _, _ = pilot_stab.process(PILOT_CLASSES[pt], float(p_conf[pt]), ts)
                if p_commit:
                    pilot_commits.append(p_commit)

        pc = per_class[name]
        pc['clips'] += 1
        pc['max_conf'] = max(pc['max_conf'], top_conf)
        if commits:
            pc['committed'] += 1
            if name in commits:
                pc['committed_correct'] += 1
            else:
                pc['committed_wrong'] += 1
                pc['wrong_labels'].update(commits)
        else:
            pc['no_commit'] += 1
        if args.pilot:
            pc['pilot_clips'] += 1
            if name in pilot_commits:
                pc['pilot_committed_correct'] += 1
        details.append({'file': r['video_file'], 'true': name, 'frames': int(T),
                        'commits': commits[:8], 'top_confidence': round(top_conf, 4),
                        'pilot_commits': pilot_commits[:8]})

    out = {
        'config': {'hold_frames': args.hold, 'fps': 10, 'seq_len': SEQ_LEN,
                   'baseline_stabilizer': BASELINE_STABILIZER},
        'per_class': {k: {**v, 'wrong_labels': dict(v['wrong_labels'])} for k, v in sorted(per_class.items())},
        'totals': {
            'classes': len(per_class),
            'clips': sum(v['clips'] for v in per_class.values()),
            'committed_correct': sum(v['committed_correct'] for v in per_class.values()),
            'committed_wrong': sum(v['committed_wrong'] for v in per_class.values()),
            'no_commit': sum(v['no_commit'] for v in per_class.values()),
        },
        'details': details,
    }
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), args.out), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)

    print(json.dumps(out['totals'], indent=2))
    for k, v in out['per_class'].items():
        print(f"  {k:11s} clips={v['clips']:2d} correct={v['committed_correct']:2d} "
              f"wrong={v['committed_wrong']:2d} none={v['no_commit']:2d} "
              f"maxconf={v['max_conf']:.3f} wrong_labels={dict(v['wrong_labels'])}")
    print('->', args.out)


if __name__ == '__main__':
    main()
