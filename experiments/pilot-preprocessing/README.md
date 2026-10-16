# Pilot Preprocessing Experiment

Read-only isolated experiment for the Google Drive research pilot.
**DO NOT promote to `ai/sign-recognition/` without formal review.**

---

## Purpose

Process 15 pilot videos (3 per class, 5 classes) using the **production V2 feature contract**:
- 10 fps temporal sampling (matching `tools/extract_full_dataset.py`)
- MediaPipe Holistic + crop-fallback for landmark extraction (binary-identical to production)
- 366-dimensional feature vector per frame: `[lh×63, rh×63, pose×165, face×75]`
- Shoulder-center / shoulder-distance normalization (same as production)

This experiment does **not** train a model, modify the vocabulary, or touch production datasets.

---

## Pilot Class Map

| Canonical Class | ASL ID    | class_index (in V2 mapping) |
|:----------------|:----------|:---------------------------:|
| HELLO           | ASL\_001  | 0                           |
| THANK-YOU       | ASL\_005  | 4                           |
| HELP            | ASL\_007  | 5                           |
| YES             | ASL\_011  | 9                           |
| NO              | ASL\_012  | 10                          |

> Class indices come from `ai/sign-recognition/data/class_index_mapping.json` — do not change them.

---

## Files

| File | Role |
|:-----|:-----|
| `pilot_extract.py` | Main extraction script |
| `pilot_manifest_TEMPLATE.csv` | Template manifest — copy and fill in your actual filenames |
| `features/` | Created by the script; holds `.npy` and `_meta.json` per video |

---

## Step-by-Step Instructions

### 1. Download pilot videos from Google Drive

Place the 15 `.mp4` files (3 per class) in a folder, e.g. `D:\pilot_videos\`.

### 2. Copy and edit the manifest

```powershell
Copy-Item experiments\pilot-preprocessing\pilot_manifest_TEMPLATE.csv experiments\pilot-preprocessing\pilot_manifest.csv
```

Edit `pilot_manifest.csv` in any text editor — replace the template filenames (e.g. `HELLO_001.mp4`) with your actual video filenames.
Preserve the header: `video_file,canonical_name,asl_id,class_index`.

### 3. Install dependencies (if not already present)

```powershell
pip install mediapipe opencv-python numpy
```

Mediapipe version used in production: `mediapipe` (the `mp.solutions.holistic` API).

### 4. Dry-run to validate inputs

```powershell
python experiments/pilot-preprocessing/pilot_extract.py `
    --video_dir D:\pilot_videos `
    --manifest  experiments/pilot-preprocessing/pilot_manifest.csv `
    --dry_run
```

Expected output: confirms all 15 video files are found and class names are valid. **Exits without extracting features.**

### 5. Run extraction

```powershell
python experiments/pilot-preprocessing/pilot_extract.py `
    --video_dir D:\pilot_videos `
    --manifest  experiments/pilot-preprocessing/pilot_manifest.csv `
    --output_dir experiments/pilot-preprocessing/features
```

Expected outputs per video:
- `features/<stem>_features.npy` — shape `(N, 366)`, `float32`
- `features/<stem>_meta.json`   — sequence length, NaN/Inf counts, provenance

### 6. Read the extraction report

After completion:
```
experiments/pilot-preprocessing/features/extraction_report.json
```

Check:
- `failed` list is empty
- `total_nans` and `total_infs` are 0
- `feature_dimension` is `366`

---

## What to verify manually

1. **Sequence length** — typical ASL Citizen sign videos yield 12–30 frames at 10 fps. If `seq_len < 5`, the video is likely corrupt or too short.
2. **NaN / Inf counts** — should be 0. Non-zero means the pose anchor (shoulder) was not detected for some frames; this is recoverable (zeros are left in place, matching production behaviour).
3. **Feature dimension** — must be exactly 366. The script hard-fails if this is wrong.
4. **V2 scalars** — the script verifies `ai/sign-recognition/models/spoter_v2_groupnorm_scalars.json` exists and is well-formed. The scalars are **not baked into the `.npy` files** (production applies them at batch-time in `apply_scaling()`).

---

## What happens next (after manual review)

1. Review `extraction_report.json` and inspect a few `.npy` files to confirm shapes.
2. Decide whether to run inference against the existing 79-class SPOTER V2 model for a zero-shot probe.
3. Any fine-tuning or new training is a **separate decision** requiring a formal implementation plan.
