"""Sensitivity check: does the 79-class baseline care about hand slot assignment?

The browser writes the MediaPipe "Left" hand into the canonical rightHand block
(canonicalSlotForMediaPipeLabel). If that convention disagrees with the training
capture, live features are effectively handedness-swapped. This measures how
much that would cost, plus how much a full horizontal mirror would cost.
"""
import json
import os
import sys

import numpy as np
import onnxruntime as ort

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eval_baseline_79 import (FEATURES_DIR, MANIFEST, ONNX, load_mapping, load_scalars, scale)  # noqa: E402

SEQ_LEN, DIM = 60, 366
POSE_STRIDE, POSE_OFF = 5, 126


def swap_hands(seq):
    out = seq.copy()
    out[:, 0:63] = seq[:, 63:126]
    out[:, 63:126] = seq[:, 0:63]
    return out


def mirror(seq):
    """Horizontal mirror: negate x everywhere, swap hands, swap pose 11/12."""
    out = seq.copy()
    # hands: x at index 3k, for k in 0..20
    lh = out[:, 0:63].reshape(-1, 21, 3)
    rh = out[:, 63:126].reshape(-1, 21, 3)
    lh[:, :, 0] *= -1
    rh[:, :, 0] *= -1
    out[:, 0:63] = rh.reshape(-1, 63)
    out[:, 63:126] = lh.reshape(-1, 63)
    pose = out[:, POSE_OFF:291].reshape(-1, 33, 5)
    pose[:, :, 0] *= -1
    tmp = pose[:, 11, :].copy()
    pose[:, 11, :] = pose[:, 12, :]
    pose[:, 12, :] = tmp
    face = out[:, 291:366].reshape(-1, 25, 3)
    face[:, :, 0] *= -1
    return out


def pad_right(seq):
    out = np.zeros((SEQ_LEN, DIM), dtype=np.float32)
    n = min(seq.shape[0], SEQ_LEN)
    out[SEQ_LEN - n:] = seq[seq.shape[0] - n:]
    return out


def main():
    by_asl, by_index = load_mapping()
    scalars = load_scalars()
    sess = ort.InferenceSession(ONNX, providers=['CPUExecutionProvider'])
    iname = sess.get_inputs()[0].name

    rows = []
    with open(MANIFEST, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split(',')
        for line in f:
            if line.strip():
                rows.append(dict(zip(header, line.strip().split(','))))

    variants = {'identity': lambda s: s, 'hand_swap': swap_hands, 'full_mirror': mirror}
    hits = {k: 0 for k in variants}
    n = 0
    per_class_flip = {}
    for r in rows:
        if r['source_split'] != 'val' or r['asl_id'] not in by_asl:
            continue
        path = os.path.join(FEATURES_DIR, r['video_file'].replace('.mp4', '') + '_features.npy')
        if not os.path.exists(path):
            continue
        seq = scale(np.load(path).astype(np.float32), scalars)
        idx = by_asl[r['asl_id']]
        n += 1
        for k, fn in variants.items():
            logits = sess.run(None, {iname: pad_right(fn(seq))[None]})[0][0]
            if int(np.argmax(logits)) == idx:
                hits[k] += 1
        if int(np.argmax(sess.run(None, {iname: pad_right(swap_hands(seq))[None]})[0][0])) == idx:
            pass
    result = {'val_samples': n, 'accuracy': {k: hits[k] / n for k in variants}}
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'handedness_results.json'), 'w') as f:
        json.dump(result, f, indent=2)
    for k, v in result['accuracy'].items():
        print(f'{k:12s} top1 = {v*100:.2f}%')


if __name__ == '__main__':
    main()
