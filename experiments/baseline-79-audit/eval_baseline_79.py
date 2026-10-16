"""Offline audit: 79-class SPOTER V2 baseline (PyTorch vs ONNX).

Answers three questions with measured numbers rather than assumptions:
  1. Does the exported ONNX model agree numerically with the PyTorch checkpoint?
  2. What is the model's own top-1 accuracy on the held-out `val` split
     (training-time preprocessing: full-length sequence + padding mask)?
  3. What does the same model predict when the input is prepared exactly the way
     the browser prepares it (fixed 60-frame window, no attention mask)?

Read-only with respect to model assets: nothing is written except the JSON report.

Usage:
    .venv_pilot/Scripts/python.exe experiments/baseline-79-audit/eval_baseline_79.py
"""
import json
import os
import sys
from collections import defaultdict

import numpy as np
import onnxruntime as ort
import torch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(ROOT, 'ai', 'sign-recognition', 'models'))

from spoter import Spoter  # noqa: E402

MANIFEST = os.path.join(ROOT, 'ai', 'sign-recognition', 'data', 'asl100_training_manifest.csv')
FEATURES_DIR = os.path.join(ROOT, 'ai', 'sign-recognition', 'data', 'dataset_extracted')
MAPPING = os.path.join(ROOT, 'ai', 'sign-recognition', 'data', 'class_index_mapping.json')
SCALARS = os.path.join(ROOT, 'ai', 'sign-recognition', 'models', 'spoter_v2_groupnorm_scalars.json')
CKPT = os.path.join(ROOT, 'ai', 'sign-recognition', 'checkpoints', 'spoter_v2_groupnorm_best_val_acc.pt')
ONNX = os.path.join(ROOT, 'ai', 'sign-recognition', 'checkpoints', 'spoter_v2_model.onnx')
OUT = os.path.join(os.path.dirname(__file__), 'baseline_79_offline_results.json')

SEQ_LEN = 60
DIM = 366
LH = range(0, 63)
RH = range(63, 126)
POSE_XYZ = [126 + i * 5 + j for i in range(33) for j in range(3)]
FACE = range(291, 366)


def load_mapping():
    with open(MAPPING, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    by_asl = {}
    by_index = {}
    for key, data in raw.items():
        by_asl[data['asl_id']] = int(data['class_index'])
        by_index[int(data['class_index'])] = data['canonical_name']
    return by_asl, by_index


def load_scalars():
    with open(SCALARS, 'r', encoding='utf-8') as f:
        return json.load(f)


def scale(seq, scalars):
    """Exact training-time group scaling (train_spoter_v2.apply_scaling)."""
    out = np.array(seq, dtype=np.float32, copy=True)
    out[:, list(LH)] /= float(scalars['left_hand'])
    out[:, list(RH)] /= float(scalars['right_hand'])
    out[:, POSE_XYZ] /= float(scalars['pose_xyz'])
    out[:, list(FACE)] /= float(scalars['face'])
    return out


def softmax(logits):
    m = np.max(logits)
    e = np.exp(logits - m)
    return e / e.sum()


def main():
    by_asl, by_index = load_mapping()
    scalars = load_scalars()

    rows = []
    with open(MANIFEST, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split(',')
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            rows.append(dict(zip(header, parts)))

    torch_model = Spoter(num_classes=79, hidden_dim=512, nhead=8, num_encoder_layers=6,
                         num_decoder_layers=6, dim_feedforward=2048, dropout=0.1)
    torch_model.load_state_dict(torch.load(CKPT, map_location='cpu', weights_only=True))
    torch_model.eval()

    sess = ort.InferenceSession(ONNX, providers=['CPUExecutionProvider'])
    input_name = sess.get_inputs()[0].name
    onnx_input_dims = sess.get_inputs()[0].shape
    onnx_output_dims = sess.get_outputs()[0].shape

    results = {
        'onnx_input_dims': [str(d) for d in onnx_input_dims],
        'onnx_output_dims': [str(d) for d in onnx_output_dims],
        'onnx_output_length': int(sess.get_outputs()[0].shape[-1]),
        'checkpoint': os.path.relpath(CKPT, ROOT).replace('\\', '/'),
        'onnx': os.path.relpath(ONNX, ROOT).replace('\\', '/'),
        'scalars': scalars,
        'windows': {},
        'parity': {},
    }

    for split in ('val', 'train'):
        split_rows = [r for r in rows if r['source_split'] == split]
        known = [r for r in split_rows if r['asl_id'] in by_asl
                 and os.path.exists(os.path.join(FEATURES_DIR, r['video_file'].replace('.mp4', '') + '_features.npy'))]
        correct = defaultdict(int)
        total = defaultdict(int)
        browser_correct = defaultdict(int)
        browser_total = defaultdict(int)
        one_frame_agree = 0
        max_abs_diffs = []
        samples = []
        for r in known:
            path = os.path.join(FEATURES_DIR, r['video_file'].replace('.mp4', '') + '_features.npy')
            raw = np.load(path).astype(np.float32)
            if raw.ndim != 2 or raw.shape[1] != DIM:
                continue
            idx = by_asl[r['asl_id']]
            name = by_index[idx]
            scaled = scale(raw, scalars)
            T = scaled.shape[0]

            # --- training-time path: full length + padding mask ---
            padded = np.zeros((1, T, DIM), dtype=np.float32)
            padded[0, :T] = scaled
            mask = np.ones((1, T), dtype=bool)
            with torch.no_grad():
                pt_logits_train = torch_model(torch.from_numpy(padded),
                                              attention_mask=torch.from_numpy(mask)).numpy()[0]

            # --- browser-time path: fixed 60-frame window, no mask ---
            window = make_window(scaled, T)
            with torch.no_grad():
                pt_logits_win = torch_model(torch.from_numpy(window[None, :, :])).numpy()[0]
            onnx_logits_win = sess.run(None, {input_name: window[None, :, :]})[0][0]

            pt_top = int(np.argmax(pt_logits_train))
            pt_win_top = int(np.argmax(pt_logits_win))
            onnx_win_top = int(np.argmax(onnx_logits_win))

            total[name] += 1
            if pt_top == idx:
                correct[name] += 1
            browser_total[name] += 1
            if onnx_win_top == idx:
                browser_correct[name] += 1
            if pt_win_top == onnx_win_top:
                one_frame_agree += 1
            max_abs_diffs.append(float(np.max(np.abs(pt_logits_win - onnx_logits_win))))

            samples.append({
                'file': r['video_file'],
                'true_index': idx,
                'true_name': name,
                'torch_fullseq_top1': pt_top,
                'torch_fullseq_top1_name': by_index.get(pt_top),
                'onnx_60win_top1': onnx_win_top,
                'onnx_60win_top1_name': by_index.get(onnx_win_top),
                'onnx_60win_confidence': float(softmax(onnx_logits_win)[onnx_win_top]),
                'onnx_60win_correct': bool(onnx_win_top == idx),
                'onnx_60win_top5': [[by_index.get(int(i)), float(softmax(onnx_logits_win)[i])]
                                    for i in np.argsort(-onnx_logits_win)[:5]],
                'frames': int(T),
            })

        results['windows'][split] = {
            'samples': len(known),
            'torch_fullseq_top1_acc': sum(correct.values()) / max(1, sum(total.values())),
            'onnx_60frame_top1_acc': sum(browser_correct.values()) / max(1, sum(browser_total.values())),
            'per_class': {n: {'support': total[n],
                              'torch_fullseq_correct': correct[n],
                              'onnx_60frame_correct': browser_correct[n]}
                          for n in sorted(total)},
            'argmax_agreement_torch_vs_onnx_60frame': one_frame_agree / max(1, len(known)),
            'max_abs_logit_diff_60frame': max(max_abs_diffs) if max_abs_diffs else None,
        }
        results['parity'][split] = samples

    # Focused trace: competition signs under the exact browser path.
    focus = {}
    for sign in ('HELLO', 'YES', 'NO'):
        entries = [s for s in results['parity']['val'] if s['true_name'] == sign]
        focus[sign] = {
            'val_samples': len(entries),
            'onnx_60frame_correct': sum(1 for s in entries if s['onnx_60win_correct']),
            'onnx_60frame_predictions': [s['onnx_60win_top1_name'] for s in entries],
            'details': entries,
        }
    results['competition_signs_val_60frame'] = focus

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print('ONNX input', results['onnx_input_dims'], 'output', results['onnx_output_dims'])
    for split in ('val', 'train'):
        w = results['windows'][split]
        print(f"[{split}] n={w['samples']} torch(full-seq+mask) top1={w['torch_fullseq_top1_acc']*100:.2f}%  "
              f"onnx(60-frame,no mask) top1={w['onnx_60frame_top1_acc']*100:.2f}%  "
              f"argmax agreement={w['argmax_agreement_torch_vs_onnx_60frame']*100:.1f}%  "
              f"max_logit_diff={w['max_abs_logit_diff_60frame']:.2e}")
    for sign, data in results['competition_signs_val_60frame'].items():
        print(f"  {sign}: {data['onnx_60frame_correct']}/{data['val_samples']} "
              f"(browser path) predicted as {data['onnx_60frame_predictions']}")
    print('report written to', os.path.relpath(OUT, ROOT).replace('\\', '/'))


def make_window(scaled, T):
    """Replicates the browser buffer: 60 frames, zero-padded at the front if short,
    centred on the middle of the recording when longer (same convention as the
    existing web/src/tests traces)."""
    out = np.zeros((SEQ_LEN, DIM), dtype=np.float32)
    if T >= SEQ_LEN:
        start = max(0, T // 2 - SEQ_LEN // 2)
        out[:] = scaled[start:start + SEQ_LEN]
    else:
        out[SEQ_LEN - T:] = scaled
    return out


if __name__ == '__main__':
    main()
