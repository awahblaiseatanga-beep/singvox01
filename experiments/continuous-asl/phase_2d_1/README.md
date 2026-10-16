# Phase 2D.1 — Pretrained Continuous ASL Translation Feasibility

Feasibility evaluation of [`mamounyosef/sign-language-bridge`](https://huggingface.co/mamounyosef/sign-language-bridge),
an RSLoRA adapter fine-tuned on `Qwen/Qwen3-VL-2B-Instruct` for continuous ASL-to-English translation.

---

## Status

**Decision: NO-GO (Local Execution) / CONDITIONAL GO (Cloud GPU Only)**

Current local machine has no GPU and only ~3.8 GB available RAM, making loading of
the 4.73 GB base model + adapter infeasible. Cloud GPU execution is required for
any live inference attempt.

---

## Directory Layout

```
experiments/continuous-asl/phase_2d_1/
├── README.md                    # This file
├── env_audit.py                 # Step 1: Machine & environment audit
├── inspect_model_card.py        # Step 2: Fetch HF model card & README
├── check_adapter_and_base.py    # Step 2: Verify adapter_config.json and HF file tree
├── inspect_pipeline.py          # Step 2: Base model weights and GitHub pipeline tree
├── fetch_author_scripts.py      # Step 2: Download author's official testing scripts
├── match_local_clips.py         # Step 3: Match local How2Sign videos with captions
├── test_cropper.py              # Step 3: Verify author's SignerCropper on local clips
├── evaluate.py                  # Steps 4-6: Main evaluation + feasibility decision
├── results.json                 # Machine-readable evaluation results
├── adapter_config.json          # Fetched from HF: adapter RSLoRA configuration
├── HF_README.md                 # Author's Hugging Face model card
├── GITHUB_README.md             # Author's GitHub README (full technical details)
├── matched_sample_clips.json    # 100 matched local How2Sign clips with captions
├── qwen3vl_testing.py           # Author's official test script (fetched from GitHub)
├── vram_feasibility_test.py     # Author's VRAM feasibility test (fetched from GitHub)
├── signer_cropper.py            # Author's pose-guided signer cropper (fetched from GitHub)
└── models/
    └── pose_landmarker_lite.task  # MediaPipe pose landmark model (auto-downloaded)
```

---

## Exact Setup & Reproduction Commands

```powershell
# All commands must be run from the repository root: d:\Singvox\Singvox

# Step 1: Run environment audit
.venv\Scripts\python.exe experiments/continuous-asl/phase_2d_1/env_audit.py

# Step 2: Inspect model card and adapter
.venv\Scripts\python.exe experiments/continuous-asl/phase_2d_1/inspect_model_card.py
.venv\Scripts\python.exe experiments/continuous-asl/phase_2d_1/check_adapter_and_base.py

# Step 3: Match local clips with captions
.venv\Scripts\python.exe experiments/continuous-asl/phase_2d_1/match_local_clips.py

# Step 4-6: Run full evaluation (preprocessing audit + feasibility decision)
.venv\Scripts\python.exe experiments/continuous-asl/phase_2d_1/evaluate.py
```

---

## Dependencies

Fully isolated from the main SingVox environment. Requires only:
- `opencv-python` (cv2 5.0.0) — already present in `.venv`
- `mediapipe` (0.10.35) — already present in `.venv`

**NOT required** (cloud execution only):
- `transformers`, `peft`, `accelerate` — available on Modal/RunPod A100 images
- `qwen_vl_utils` — install via `pip install qwen-vl-utils`

---

## Hardware Requirements for Live Inference

| Resource | Required | Current Machine | Gap |
| :--- | :--- | :--- | :--- |
| GPU VRAM | ≥ 8 GB | 0 GB (CPU only) | **Missing** |
| System RAM | ≥ 12 GB free | 3.81 GB available | **Insufficient** |
| Disk | ≥ 5 GB free | 122.65 GB | OK |
| CUDA | ≥ 11.8 | Not available | **Missing** |

**Recommended Cloud Target:** Modal with A100-40GB or RTX 4090 (~$1.50–2.50/hr)

---

## Published Model Performance (Author-Reported, How2Sign 944-clip test set)

| Metric | Value |
| :--- | :--- |
| BLEU-1 | 19.76 |
| BLEU-4 | **1.64** |
| WER (%) | **112.51** |
| chrF | 17.42 |
| ROUGE-L | 10.43 |
| Distinct-2 | 0.103 |
| Perplexity | 16.28 |

WER > 100% indicates more word errors than reference words (severe insertions/substitutions).
BLEU-4 of 1.64 is identical to Phase 2C.27 (1.66) and Phase 2C.29 (1.64).

---

## Critical Notes

1. **Do not modify production code.** All work is isolated to this directory.
2. **Do not fine-tune during this phase.** Test published adapter first.
3. **Do not claim success because the model loads.** Fluent English ≠ accurate translation.
4. Live inference tests must be run on a cloud GPU instance.
   See `results.json` for the full machine-readable summary.
