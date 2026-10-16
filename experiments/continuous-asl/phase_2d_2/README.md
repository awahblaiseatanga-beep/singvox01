# Phase 2D.2 — Cloud Inference Proof of Concept

Runs the [`mamounyosef/sign-language-bridge`](https://huggingface.co/mamounyosef/sign-language-bridge)
RSLoRA adapter on Qwen/Qwen3-VL-2B-Instruct on a cloud GPU and evaluates
whether its translations depend meaningfully on the ASL video content.

**Inference only. No training, fine-tuning, or weight modification.**

---

## Prerequisites

- A RunPod (or equivalent) account with an RTX 4090 or A100 pod (~$0.34–1.24/hr)
- The 8 verified How2Sign clips and their captions (`matched_sample_clips.json`)
- `HF_TOKEN` as an environment variable if required (this model is public — likely not needed)

---

## Files

```
experiments/continuous-asl/phase_2d_2/
├── README.md                    # This file
├── evaluate.py                  # Cloud inference script (GPU required)
└── results.json                 # Written after cloud run
```

Additional files uploaded to cloud instance from Phase 2D.1:
- `signer_cropper.py` — author's MediaPipe signer crop
- `matched_sample_clips.json` — 8 verified clips with captions

---

## Cloud Setup & Execution

```bash
# 1. Create a RunPod pod: RTX 4090 (24 GB), 20 GB ephemeral disk
# 2. Upload evaluate.py, signer_cropper.py, matched_sample_clips.json
# 3. Upload the 8 .mp4 clips to ~/phase_2d_2/clips/

# Install dependencies
pip install transformers==4.49.0 peft==0.18.1 accelerate \
    qwen-vl-utils opencv-python mediapipe sacrebleu

# Fix clip paths in JSON to match cloud layout
python -c "
import json, pathlib
clips = json.load(open('matched_sample_clips.json'))
for c in clips:
    c['path'] = 'clips/' + pathlib.Path(c['path']).name
json.dump(clips, open('matched_sample_clips.json','w'), indent=2)
"

# Run 8-clip pilot
python evaluate.py --clips_json matched_sample_clips.json --max_clips 8 --output_dir ./output

# Expand to 20 clips only if pilot shows credible video-dependence:
python evaluate.py --clips_json matched_sample_clips.json --max_clips 8 --expand --output_dir ./output

# 4. Download results.json
# 5. TERMINATE the pod immediately after download
```

---

## What Is Tested

| Condition | What It Measures |
|---|---|
| A. Original video | Baseline translation quality |
| B. Shuffled frames (same clip) | Temporal dependence of output |
| C. Original vs. mismatched reference BLEU | Whether model actually follows the specific clip |

---

## Hard Cost Limit

Maximum session: **2 hours**. Estimated actual cost: **< $0.70** (RTX 4090, per-second billing).
The pod must be terminated manually immediately after `results.json` is downloaded.

---

## Decision Criteria

| Verdict | Condition |
|---|---|
| **GO** | BLEU-1 ≥ 20%, shuffled identity < 50%, matched win rate ≥ 60% |
| **CONDITIONAL GO** | BLEU-1 ≥ 10% or matched win rate ≥ 50% |
| **NO-GO** | Below all thresholds |
