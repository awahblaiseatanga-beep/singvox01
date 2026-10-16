"""Direct pilot-vs-baseline comparison on identical inputs.

Both models are fed the exact same preprocessed feature sequences so the only
variable is the model. Two input constructions are used per sample:

  full  - the whole recorded clip (variable length), zero-padded to 60 frames
  slide - the live browser pattern: a 60-frame FIFO window advanced one frame
          at a time at 10 fps (the rate the training data was extracted at)

Results are per-sign top-1 accuracy plus the number of clips where the correct
class is ever the argmax inside the live window.
"""
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
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pilot_vs_baseline_results.json')


def load(onnx_path):
    """onnxruntime-node style load is not available here; use python ORT."""
    sess = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
    return sess, sess.get_inputs()[0].name


def pad_to_60(seq):
    out = np.zeros((SEQ_LEN, DIM), dtype=np.float32)
    n = min(seq.shape[0], SEQ_LEN)
    out[SEQ_LEN - n:] = seq[seq.shape[0] - n:]
    return out


def main():
    by_asl, by_index = load_mapping()
    scalars = load_scalars()

    pilot, pilot_in = load(PILOT_ONNX)
    baseline, base_in = load(BASELINE_ONNX)

    meta = {
        'pilot': {'input': [str(d) for d in pilot.get_inputs()[0].shape],
                  'output': [str(d) for d in pilot.get_outputs()[0].shape]},
        'baseline': {'input': [str(d) for d in baseline.get_inputs()[0].shape],
                     'output': [str(d) for d in baseline.get_outputs()[0].shape]},
    }

    rows = []
    with open(MANIFEST, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split(',')
        for line in f:
            if line.strip():
                rows.append(dict(zip(header, line.strip().split(','))))

    report = {'models': meta, 'signs': {}}
    for sign in PILOT_CLASSES:
        entries = [r for r in rows if r['canonical_name'] == sign
                   and os.path.exists(os.path.join(FEATURES_DIR,
                                                   r['video_file'].replace('.mp4', '') + '_features.npy'))]
        per = {'val': defaultdict(int), 'train': defaultdict(int), 'window_true_present': 0,
               'n': 0, 'details': []}
        for r in entries:
            split = r['source_split']
            if split not in ('val', 'train'):
                continue
            path = os.path.join(FEATURES_DIR, r['video_file'].replace('.mp4', '') + '_features.npy')
            seq = scale(np.load(path).astype(np.float32), scalars)
            T = seq.shape[0]
            per['n'] += 1

            # full-clip style input (whole clip right-aligned in a 60-frame tensor)
            full = pad_to_60(seq)
            p_logits = pilot.run(None, {pilot_in: full[None]})[0][0]
            b_logits = baseline.run(None, {base_in: full[None]})[0][0]
            p_full = PILOT_CLASSES[int(np.argmax(p_logits))]
            b_full = by_index[int(np.argmax(b_logits))]

            # live window style: 60-frame FIFO advanced one frame at a time
            win_preds_pilot, win_preds_base = [], []
            buf = np.zeros((SEQ_LEN, DIM), dtype=np.float32)
            for t in range(T):
                buf = np.roll(buf, -1, axis=0)
                buf[-1] = seq[t]
                if t < SEQ_LEN - 1:
                    continue  # browser only infers once the buffer is full
                lp = pilot.run(None, {pilot_in: buf[None]})[0][0]
                lb = baseline.run(None, {base_in: buf[None]})[0][0]
                win_preds_pilot.append(PILOT_CLASSES[int(np.argmax(lp))])
                win_preds_base.append(by_index[int(np.argmax(lb))])
            p_win = Counter(win_preds_pilot).most_common(1)[0][0] if win_preds_pilot else None
            b_win = Counter(win_preds_base).most_common(1)[0][0] if win_preds_base else None
            if sign in win_preds_base:
                per['window_true_present'] += 1

            per[split]['n'] += 1
            per[split]['pilot_full'] += int(p_full == sign)
            per[split]['baseline_full'] += int(b_full == sign)
            per[split]['baseline_window'] += int(b_win == sign)
            if win_preds_pilot:
                per[split]['pilot_window'] += int(p_win == sign)
            per['details'].append({
                'file': r['video_file'], 'split': split, 'frames': int(T),
                'pilot_full': p_full, 'baseline_full': b_full,
                'pilot_window_top': p_win, 'baseline_window_top': b_win,
                'baseline_window_true_present': bool(sign in win_preds_base),
            })
        report['signs'][sign] = {
            'total_samples': per['n'],
            'window_true_present': per['window_true_present'],
            'val': {k: v for k, v in per['val'].items() if k != 'details'},
            'train': {k: v for k, v in per['train'].items() if k != 'details'},
            'details': per['details'],
        }

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print('pilot   ', meta['pilot'])
    print('baseline', meta['baseline'])
    for sign, d in report['signs'].items():
        print(f"\n{sign}: {d['total_samples']} samples; baseline-window ever-correct on "
              f"{d['window_true_present']} clips")
        for split in ('val', 'train'):
            s = d[split]
            n = max(1, s.get('n', 0))
            print(f"  {split:5s} n={s.get('n',0):3d}  pilot_full={s.get('pilot_full',0)/n*100:5.1f}%  "
                  f"baseline_full={s.get('baseline_full',0)/n*100:5.1f}%  "
                  f"pilot_window={s.get('pilot_window',0)/n*100:5.1f}%  "
                  f"baseline_window={s.get('baseline_window',0)/n*100:5.1f}%")
    print('\nreport ->', os.path.relpath(OUT, ROOT).replace('\\', '/'))


if __name__ == '__main__':
    main()
