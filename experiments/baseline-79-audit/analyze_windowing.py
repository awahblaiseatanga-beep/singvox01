"""Follow-up: isolate why the browser-time 60-frame path loses ~33 points of top-1.

Compares four input constructions on the same held-out `val` split:
  A. full clip, variable length, WITH padding mask   (training-time path)
  B. full clip, variable length, NO mask             (what the ONNX export bakes in)
  C. centre 60-frame window, no mask                 (browser path today)
  D. clip temporally resampled to 60 frames, no mask (browser path if it
                                                      matched training coverage)

Also reports clip-length statistics, and simulates the live sliding-window +
TemporalStabilizer path over a few competition-sign clips.
"""
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np
import onnxruntime as ort
import torch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(ROOT, 'ai', 'sign-recognition', 'models'))

from spoter import Spoter  # noqa: E402
from eval_baseline_79 import (FEATURES_DIR, MANIFEST, ONNX, CKPT, SCALARS, load_mapping,
                              load_scalars, scale)  # noqa: E402

SEQ_LEN, DIM = 60, 366
OUT = os.path.join(os.path.dirname(__file__), 'baseline_79_windowing_results.json')


def centre_window(scaled, T):
    out = np.zeros((SEQ_LEN, DIM), dtype=np.float32)
    if T >= SEQ_LEN:
        start = max(0, T // 2 - SEQ_LEN // 2)
        out[:] = scaled[start:start + SEQ_LEN]
    else:
        out[SEQ_LEN - T:] = scaled
    return out


def resample(scaled, T, length=SEQ_LEN):
    idx = np.linspace(0, T - 1, length)
    lo = np.floor(idx).astype(int)
    hi = np.minimum(lo + 1, T - 1)
    frac = (idx - lo)[:, None]
    return (scaled[lo] * (1 - frac) + scaled[hi] * frac).astype(np.float32)


def main():
    by_asl, by_index = load_mapping()
    scalars = load_scalars()

    rows = []
    with open(MANIFEST, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split(',')
        for line in f:
            if line.strip():
                rows.append(dict(zip(header, line.strip().split(','))))

    torch_model = Spoter(num_classes=79, hidden_dim=512, nhead=8, num_encoder_layers=6,
                         num_decoder_layers=6, dim_feedforward=2048, dropout=0.1)
    torch_model.load_state_dict(torch.load(CKPT, map_location='cpu', weights_only=True))
    torch_model.eval()
    sess = ort.InferenceSession(ONNX, providers=['CPUExecutionProvider'])
    iname = sess.get_inputs()[0].name

    def pt(x, mask=None):
        with torch.no_grad():
            m = torch.from_numpy(mask) if mask is not None else None
            return torch_model(torch.from_numpy(x), attention_mask=m).numpy()[0]

    def onnx(x):
        return sess.run(None, {iname: x})[0][0]

    lengths = []
    acc = {'A_fullseq_masked_pt': [], 'B_fullseq_nomask_pt': [], 'C_centre60_onnx': [],
           'D_resample60_onnx': []}
    per_class_c = defaultdict(lambda: [0, 0])
    per_class_d = defaultdict(lambda: [0, 0])
    per_class_a = defaultdict(lambda: [0, 0])
    wins = {'C_centre60_onnx': [], 'D_resample60_onnx': []}

    val_rows = [r for r in rows if r['source_split'] == 'val' and r['asl_id'] in by_asl]
    print('rows', len(rows), 'val_rows', len(val_rows), 'features_dir', FEATURES_DIR, flush=True)
    for r in val_rows:
        path = os.path.join(FEATURES_DIR, r['video_file'].replace('.mp4', '') + '_features.npy')
        if not os.path.exists(path):
            continue
        raw = np.load(path).astype(np.float32)
        if raw.ndim != 2 or raw.shape[1] != DIM:
            continue
        idx = by_asl[r['asl_id']]
        name = by_index[idx]
        scaled = scale(raw, scalars)
        T = scaled.shape[0]
        lengths.append(T)

        padded = np.zeros((1, T, DIM), dtype=np.float32)
        padded[0] = scaled
        logits_a = pt(padded, np.ones((1, T), dtype=bool))
        logits_b = pt(padded)
        c = centre_window(scaled, T)[None]
        logits_c = onnx(c)
        d = resample(scaled, T)[None]
        logits_d = onnx(d)

        acc['A_fullseq_masked_pt'].append(int(np.argmax(logits_a) == idx))
        acc['B_fullseq_nomask_pt'].append(int(np.argmax(logits_b) == idx))
        acc['C_centre60_onnx'].append(int(np.argmax(logits_c) == idx))
        acc['D_resample60_onnx'].append(int(np.argmax(logits_d) == idx))
        wins['C_centre60_onnx'].append(float(np.max(logits_c)))
        wins['D_resample60_onnx'].append(float(np.max(logits_d)))

        ok_c = int(np.argmax(logits_c) == idx)
        ok_d = int(np.argmax(logits_d) == idx)
        per_class_c[name][0] += ok_c
        per_class_c[name][1] += 1
        per_class_d[name][0] += ok_d
        per_class_d[name][1] += 1
        per_class_a[name][0] += int(np.argmax(logits_a) == idx)
        per_class_a[name][1] += 1

    lengths = np.array(lengths)
    report = {
        'val_samples': int(len(lengths)),
        'clip_frames': {
            'min': int(lengths.min()), 'p25': int(np.percentile(lengths, 25)),
            'median': int(np.median(lengths)), 'p75': int(np.percentile(lengths, 75)),
            'max': int(lengths.max()),
            'count_eq_60': int((lengths == 60).sum()),
            'count_lt_60': int((lengths < 60).sum()),
            'count_gt_60': int((lengths > 60).sum()),
        },
        'accuracy': {k: sum(v) / len(v) for k, v in acc.items()},
        'per_class_C_centre60': {n: f'{c}/{t}' for n, (c, t) in sorted(per_class_c.items())},
        'per_class_D_resample60': {n: f'{c}/{t}' for n, (c, t) in sorted(per_class_d.items())},
        'per_class_A_trainpath': {n: f'{c}/{t}' for n, (c, t) in sorted(per_class_a.items())},
    }

    # --- live sliding-window + stabilizer simulation on competition signs ---
    sim = {}
    for sign in ('HELLO', 'YES', 'NO'):
        entries = [r for r in val_rows if r['canonical_name'] == sign]
        details = []
        for r in entries[:6]:
            path = os.path.join(FEATURES_DIR, r['video_file'].replace('.mp4', '') + '_features.npy')
            if not os.path.exists(path):
                continue
            raw = scale(np.load(path).astype(np.float32), scalars)
            T = raw.shape[0]
            preds = []
            for end in range(1, T + 1):
                start = max(0, end - SEQ_LEN)
                win = raw[start:end]
                buf = np.zeros((1, SEQ_LEN, DIM), dtype=np.float32)
                buf[0, SEQ_LEN - win.shape[0]:] = win
                p = sess.run(None, {iname: buf})[0][0]
                preds.append(by_index[int(np.argmax(p))])
            top = Counter(preds).most_common(3)
            details.append({'file': r['video_file'], 'frames': int(T),
                            'dominant': top,
                            'contains_true': sign in preds})
        sim[sign] = details
    report['live_sliding_window_simulation'] = sim

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print('val n =', report['val_samples'])
    print('clip frames:', report['clip_frames'])
    for k, v in report['accuracy'].items():
        print(f'  {k}: {v*100:.2f}%')
    for sign, d in sim.items():
        for e in d:
            print(f'  {sign} {e["file"]} ({e["frames"]}f) dominant={e["dominant"]} true_present={e["contains_true"]}')
    print('report -> experiments/baseline-79-audit/baseline_79_windowing_results.json')


if __name__ == '__main__':
    main()
