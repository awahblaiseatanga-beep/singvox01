"""
experiments/pilot-preprocessing/pilot_extract.py

Isolated experimental preprocessing for the Google Drive research pilot.
Processes 15 pilot videos (3 per class) across 5 frozen classes:
    HELLO (ASL_001), THANK-YOU (ASL_005), HELP (ASL_007), YES (ASL_011), NO (ASL_012)

Pipeline Contract (identical to production tools/extract_full_dataset.py):
- Sampling: all frames decoded at native FPS then subsampled to 10 fps
- Extraction: MediaPipe Holistic (holistic) + crop-fallback (Hands) — binary-identical logic
- Feature dimension: 366 (21*3 left hand + 21*3 right hand + 33*5 pose + 25*3 face)
- Concatenation order: [lh.flatten(), rh.flatten(), pose.flatten(), face.flatten()]
- Landmark normalization: shoulder-center / shoulder-distance (identical to production)
- Output per video: <video_stem>_features.npy  (shape: [N, 366], float32)
                    <video_stem>_meta.json       (provenance + diagnostics)
- V2 group-norm scaling: applied only in-memory for verification; NOT baked into npy files
  (production dataloaders call apply_scaling() at batch-time)

This experiment DOES NOT:
    - Touch the production model, vocabulary, inference pipeline, or dataset splits.
    - Write into ai/sign-recognition/data/dataset_extracted.
    - Start model training.
    - Modify class_index_mapping.json or the frozen ASL-100 vocabulary.

DO_NOT_MERGE: this file is isolated to experiments/. Do not promote to ai/ without review.

Usage:
    python experiments/pilot-preprocessing/pilot_extract.py \
        --video_dir <path_to_pilot_video_folder> \
        --manifest experiments/pilot-preprocessing/pilot_manifest.csv \
        --output_dir experiments/pilot-preprocessing/features \
        [--dry_run]

Arguments:
    --video_dir    Folder containing the 15 pilot mp4 files (required).
    --manifest     Path to pilot_manifest.csv (see format below) (required).
    --output_dir   Where to write .npy and .meta.json files (default: experiments/pilot-preprocessing/features).
    --dry_run      Validate inputs only; do not run MediaPipe or write features.
"""

import os
import sys
import csv
import json
import argparse
import traceback
import numpy as np

# === Dependency checks ===
try:
    import cv2
except ImportError:
    print("BLOCKER: opencv-python is not installed. Run: pip install opencv-python", file=sys.stderr)
    sys.exit(1)

try:
    import mediapipe as mp
except ImportError:
    print("BLOCKER: mediapipe is not installed. Run: pip install mediapipe", file=sys.stderr)
    sys.exit(1)

# ─── Constants (must not be changed) ────────────────────────────────────────
EXPECTED_FEATURE_DIM = 366          # contract with SPOTER V2
FACE_INDICES = list(range(25))      # same 25 face landmarks as production
FPS_TARGET = 10                     # same as tools/extract_full_dataset.py

# Frozen 5-class pilot vocabulary (subset of frozen ASL-100, class_index_mapping.json)
PILOT_CLASS_MAP = {
    "HELLO":    {"asl_id": "ASL_001", "class_index": 0},
    "THANK-YOU":{"asl_id": "ASL_005", "class_index": 4},
    "HELP":     {"asl_id": "ASL_007", "class_index": 5},
    "YES":      {"asl_id": "ASL_011", "class_index": 9},
    "NO":       {"asl_id": "ASL_012", "class_index": 10},
}

# ─── V2 Group-Norm scalars (read from repository file; not embedded) ────────
SCALARS_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "..", "..", "ai", "sign-recognition", "models", "spoter_v2_groupnorm_scalars.json"
))

# ─── Production index ranges (must stay in sync with train_spoter_v2.py) ────
def get_xyz_indices():
    lh_idx       = list(range(0, 63))
    rh_idx       = list(range(63, 126))
    pose_xyz_idx = [126 + i * 5 + j for i in range(33) for j in range(3)]
    face_idx     = list(range(291, 366))
    return lh_idx, rh_idx, pose_xyz_idx, face_idx


# ─── Production landmark normalization (binary-identical to extract_full_dataset.py) ─
def normalize_landmarks(pose_33, left_21, right_21, face_25):
    p_out = pose_33.copy()
    l_out = left_21.copy()
    r_out = right_21.copy()
    f_out = face_25.copy()
    if np.sum(pose_33) == 0:
        return p_out, l_out, r_out, f_out

    s_left  = pose_33[11][:3]
    s_right = pose_33[12][:3]
    if np.sum(s_left) == 0 or np.sum(s_right) == 0:
        return p_out, l_out, r_out, f_out

    center_x = (s_left[0] + s_right[0]) / 2.0
    center_y = (s_left[1] + s_right[1]) / 2.0
    dist  = np.sqrt(np.sum((s_left - s_right) ** 2))
    scale = dist if dist > 0.01 else 1.0

    def norm_array(arr):
        out = arr.copy()
        for i in range(out.shape[0]):
            if np.sum(out[i, :3]) != 0:
                out[i, 0] = (out[i, 0] - center_x) / scale
                out[i, 1] = (out[i, 1] - center_y) / scale
                out[i, 2] =  out[i, 2]              / scale
        return out

    return norm_array(p_out), norm_array(l_out), norm_array(r_out), norm_array(f_out)


# ─── Production crop-fallback helpers (from extract_full_dataset.py) ─────────
def get_crop_bounds(pose_landmarks, img_h, img_w, hand_type):
    if not pose_landmarks:
        return None
    wrist_idx = 15 if hand_type == "Left" else 16
    elbow_idx = 13 if hand_type == "Left" else 14
    wrist = pose_landmarks.landmark[wrist_idx]
    elbow = pose_landmarks.landmark[elbow_idx]
    if wrist.visibility < 0.1 or wrist.presence < 0.1:
        return None
    w_x, w_y = int(wrist.x * img_w), int(wrist.y * img_h)
    margin = int(max(img_w, img_h) * 0.15)
    if elbow.visibility >= 0.1 and elbow.presence >= 0.1:
        e_x, e_y = int(elbow.x * img_w), int(elbow.y * img_h)
        dist   = np.sqrt((w_x - e_x) ** 2 + (w_y - e_y) ** 2)
        margin = max(int(dist * 1.5), int(max(img_w, img_h) * 0.1))
    x_min, x_max = max(0, w_x - margin), min(img_w, w_x + margin)
    y_min, y_max = max(0, w_y - margin), min(img_h, w_y + margin)
    if x_max - x_min < 10 or y_max - y_min < 10:
        return None
    return (x_min, y_min, x_max, y_max)


def extract_hand_from_crop(landmarks, x_min, y_min, x_max, y_max, img_w, img_h):
    arr = np.zeros((21, 3))
    if landmarks:
        crop_w = x_max - x_min
        crop_h = y_max - y_min
        for i, lm in enumerate(landmarks.landmark):
            arr[i] = [
                ((lm.x * crop_w) + x_min) / img_w,
                ((lm.y * crop_h) + y_min) / img_h,
                lm.z * (crop_w / img_w),
            ]
        return arr, True
    return arr, False


# ─── 10-fps frame extraction (identical to extract_full_dataset.py) ───────────
def extract_frames_10fps(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return [], "Cannot open video"
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30
    frame_interval = max(1, int(round(fps / FPS_TARGET)))
    frames = []
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if count % frame_interval == 0:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        count += 1
    cap.release()
    if not frames:
        return [], "Video decoded but produced 0 frames"
    return frames, None


# ─── Single-video extraction ──────────────────────────────────────────────────
def process_single_video(video_path, canonical_name, asl_id, class_index, output_dir, dry_run=False):
    """
    Run V2-identical extraction on one video.
    Returns a result dict describing success/failure and diagnostics.
    Writes:
        <output_dir>/<stem>_features.npy  — shape (N, 366), float32
        <output_dir>/<stem>_meta.json
    """
    vid_id  = os.path.basename(video_path)
    stem    = os.path.splitext(vid_id)[0]
    out_npy = os.path.join(output_dir, f"{stem}_features.npy")
    out_meta = os.path.join(output_dir, f"{stem}_meta.json")

    # ── Pre-flight checks ────────────────────────────────────────────────────
    if not os.path.exists(video_path):
        return {"vid": vid_id, "success": False, "error": "File not found on disk"}

    if not vid_id.lower().endswith(".mp4"):
        return {"vid": vid_id, "success": False, "error": "Non-mp4 file — extension not supported"}

    if canonical_name not in PILOT_CLASS_MAP:
        return {"vid": vid_id, "success": False,
                "error": f"canonical_name '{canonical_name}' not in PILOT_CLASS_MAP — not a pilot class"}

    if dry_run:
        return {"vid": vid_id, "success": True, "error": None, "dry_run": True,
                "seq_len": "—", "nans": "—", "infs": "—", "canonical_name": canonical_name,
                "class_index": class_index, "asl_id": asl_id}

    # ── Frame extraction ─────────────────────────────────────────────────────
    frames, frame_err = extract_frames_10fps(video_path)
    if frame_err:
        return {"vid": vid_id, "success": False, "error": f"Frame extraction: {frame_err}"}
    if len(frames) < 5:
        return {"vid": vid_id, "success": False,
                "error": f"Too few frames after 10-fps sampling ({len(frames)} < 5). "
                         "Video may be corrupt or shorter than 0.5 s."}

    # ── Landmark extraction (identical to production) ────────────────────────
    mp_holistic = mp.solutions.holistic
    mp_hands    = mp.solutions.hands
    holistic        = mp_holistic.Holistic(static_image_mode=False, min_detection_confidence=0.5)
    hands_detector  = mp_hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.4)

    seq_features  = []
    seq_provenance = []
    nan_c = 0
    inf_c = 0

    try:
        for frame in frames:
            img_h, img_w, _ = frame.shape
            res_holistic = holistic.process(frame)

            def extract_hand_full(landmarks):
                arr = np.zeros((21, 3))
                if landmarks:
                    for i, lm in enumerate(landmarks.landmark):
                        arr[i] = [lm.x, lm.y, lm.z]
                    return arr, True
                return arr, False

            lh_hol, lh_val = extract_hand_full(res_holistic.left_hand_landmarks)
            rh_hol, rh_val = extract_hand_full(res_holistic.right_hand_landmarks)
            lh_active, rh_active = lh_hol, rh_hol
            l_prov, r_prov = "missing", "missing"

            if lh_val:
                l_prov = "holistic"
            else:
                cb = get_crop_bounds(res_holistic.pose_landmarks, img_h, img_w, "Left")
                if cb:
                    x1, y1, x2, y2 = cb
                    res_h = hands_detector.process(frame[y1:y2, x1:x2])
                    if res_h.multi_hand_landmarks:
                        for idx, h in enumerate(res_h.multi_handedness):
                            true_label = "Right" if h.classification[0].label == "Left" else "Left"
                            if true_label == "Left":
                                lh_active, _ = extract_hand_from_crop(
                                    res_h.multi_hand_landmarks[idx], x1, y1, x2, y2, img_w, img_h)
                                l_prov = "hands_fallback_crop"
                                break

            if rh_val:
                r_prov = "holistic"
            else:
                cb = get_crop_bounds(res_holistic.pose_landmarks, img_h, img_w, "Right")
                if cb:
                    x1, y1, x2, y2 = cb
                    res_h = hands_detector.process(frame[y1:y2, x1:x2])
                    if res_h.multi_hand_landmarks:
                        for idx, h in enumerate(res_h.multi_handedness):
                            true_label = "Right" if h.classification[0].label == "Left" else "Left"
                            if true_label == "Right":
                                rh_active, _ = extract_hand_from_crop(
                                    res_h.multi_hand_landmarks[idx], x1, y1, x2, y2, img_w, img_h)
                                r_prov = "hands_fallback_crop"
                                break

            pose_33 = np.zeros((33, 5))
            if res_holistic.pose_landmarks:
                for i, lm in enumerate(res_holistic.pose_landmarks.landmark):
                    pose_33[i] = [lm.x, lm.y, lm.z, lm.visibility, lm.presence]

            face_25 = np.zeros((25, 3))
            if res_holistic.face_landmarks:
                for i_out, i_in in enumerate(FACE_INDICES):
                    face_25[i_out] = [
                        res_holistic.face_landmarks.landmark[i_in].x,
                        res_holistic.face_landmarks.landmark[i_in].y,
                        res_holistic.face_landmarks.landmark[i_in].z,
                    ]

            p_n, l_n, r_n, f_n = normalize_landmarks(pose_33, lh_active, rh_active, face_25)
            feature = np.concatenate([l_n.flatten(), r_n.flatten(), p_n.flatten(), f_n.flatten()])

            # ── Dimension guard ───────────────────────────────────────────────
            if feature.shape[0] != EXPECTED_FEATURE_DIM:
                return {"vid": vid_id, "success": False,
                        "error": f"Feature dimension mismatch: got {feature.shape[0]}, expected {EXPECTED_FEATURE_DIM}"}

            nan_c += int(np.isnan(feature).sum())
            inf_c += int(np.isinf(feature).sum())
            seq_features.append(feature)
            seq_provenance.append({"left": l_prov, "right": r_prov})

    except Exception as e:
        return {"vid": vid_id, "success": False, "error": f"Crash during frame loop: {traceback.format_exc(limit=3)}"}
    finally:
        holistic.close()
        hands_detector.close()

    if len(seq_features) == 0:
        return {"vid": vid_id, "success": False, "error": "Extraction produced 0 feature vectors"}

    arr = np.array(seq_features, dtype=np.float32)

    # ── NaN / Inf guard ───────────────────────────────────────────────────────
    if nan_c > 0 or inf_c > 0:
        print(f"  WARNING [{vid_id}]: {nan_c} NaN, {inf_c} Inf values in extracted features.")

    # ── Write outputs ─────────────────────────────────────────────────────────
    os.makedirs(output_dir, exist_ok=True)
    try:
        np.save(out_npy, arr)
        meta = {
            "video_file":       vid_id,
            "asl_id":           asl_id,
            "canonical_name":   canonical_name,
            "class_index":      class_index,
            "sequence_length":  len(seq_features),
            "feature_dimension": EXPECTED_FEATURE_DIM,
            "fps_target":       FPS_TARGET,
            "nans":             nan_c,
            "infs":             inf_c,
            "provenance":       seq_provenance,
            "extraction_source": "experiments/pilot-preprocessing/pilot_extract.py",
            "pipeline_reference": "tools/extract_full_dataset.py",
        }
        with open(out_meta, "w") as f:
            json.dump(meta, f, indent=2)
    except Exception as e:
        return {"vid": vid_id, "success": False, "error": f"Failed writing output: {e}"}

    return {
        "vid": vid_id, "success": True, "error": None,
        "seq_len": len(seq_features), "nans": nan_c, "infs": inf_c,
        "canonical_name": canonical_name, "class_index": class_index, "asl_id": asl_id,
    }


# ─── Verification: check V2 scalars are loadable ────────────────────────────
def load_v2_scalars():
    if not os.path.exists(SCALARS_PATH):
        raise FileNotFoundError(
            f"V2 scalars not found at {SCALARS_PATH}. "
            "Cannot verify normalization. "
            "Do NOT move or delete ai/sign-recognition/models/spoter_v2_groupnorm_scalars.json."
        )
    with open(SCALARS_PATH, "r") as f:
        scalars = json.load(f)
    required_keys = {"left_hand", "right_hand", "pose_xyz", "face"}
    missing = required_keys - set(scalars.keys())
    if missing:
        raise ValueError(f"V2 scalars file is malformed — missing keys: {missing}")
    return scalars


# ─── CLI ─────────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Isolated V2-compatible feature extraction for 5-class pilot videos"
    )
    parser.add_argument("--video_dir", required=True,
                        help="Folder containing the 15 pilot .mp4 video files")
    parser.add_argument("--manifest", required=True,
                        help="Path to pilot_manifest.csv")
    parser.add_argument("--output_dir",
                        default=os.path.join(os.path.dirname(__file__), "features"),
                        help="Output directory for .npy and .meta.json files")
    parser.add_argument("--dry_run", action="store_true",
                        help="Validate inputs only; do not extract features")
    return parser.parse_args()


def main():
    args = parse_args()
    print("=" * 60)
    print("PILOT PREPROCESSING — V2 FEATURE EXTRACTION EXPERIMENT")
    print("=" * 60)
    print(f"  Video dir   : {args.video_dir}")
    print(f"  Manifest    : {args.manifest}")
    print(f"  Output dir  : {args.output_dir}")
    print(f"  Dry run     : {args.dry_run}")
    print(f"  Feature dim : {EXPECTED_FEATURE_DIM}")
    print(f"  FPS target  : {FPS_TARGET}")

    # ── Load V2 scalars (proves pipeline connection; not used to transform npy) ──
    try:
        scalars = load_v2_scalars()
        print(f"\n  V2 scalars  : FOUND at {SCALARS_PATH}")
        print(f"    left_hand={scalars['left_hand']:.6f}  right_hand={scalars['right_hand']:.6f}")
        print(f"    pose_xyz={scalars['pose_xyz']:.6f}   face={scalars['face']:.6f}")
    except (FileNotFoundError, ValueError) as e:
        print(f"\nBLOCKER: {e}", file=sys.stderr)
        sys.exit(1)

    # ── Read manifest ──────────────────────────────────────────────────────────
    if not os.path.exists(args.manifest):
        print(f"\nBLOCKER: Manifest not found: {args.manifest}", file=sys.stderr)
        print("  Create it using the schema in experiments/pilot-preprocessing/pilot_manifest_TEMPLATE.csv")
        sys.exit(1)

    rows = []
    with open(args.manifest, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required_cols = {"video_file", "canonical_name", "asl_id", "class_index"}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            missing_col = required_cols - set(reader.fieldnames or [])
            print(f"\nBLOCKER: Manifest missing required columns: {missing_col}", file=sys.stderr)
            sys.exit(1)
        for row in reader:
            rows.append(row)

    if not rows:
        print("\nBLOCKER: Manifest is empty.", file=sys.stderr)
        sys.exit(1)

    print(f"\n  Manifest rows loaded: {len(rows)}")

    # ── Validate row-level class names ────────────────────────────────────────
    unknown = [r["canonical_name"] for r in rows if r["canonical_name"] not in PILOT_CLASS_MAP]
    if unknown:
        print(f"\nBLOCKER: Unknown class names in manifest: {set(unknown)}", file=sys.stderr)
        print(f"  Valid pilot classes: {list(PILOT_CLASS_MAP.keys())}")
        sys.exit(1)

    # ── Validate all video files exist before running extractor ───────────────
    print("\n--- Pre-flight: checking all video files exist ---")
    missing_videos = []
    for row in rows:
        vpath = os.path.join(args.video_dir, row["video_file"])
        if not os.path.exists(vpath):
            missing_videos.append(row["video_file"])
            print(f"  MISSING: {row['video_file']}")
        else:
            print(f"  OK     : {row['video_file']}")
    if missing_videos:
        print(f"\nBLOCKER: {len(missing_videos)} video file(s) are missing. "
              "Provide them in --video_dir before running.", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print("\nDry run complete. All input files validated. "
              "Re-run without --dry_run to extract features.")
        return

    # ── Extraction ────────────────────────────────────────────────────────────
    print(f"\n--- Extracting features into: {args.output_dir} ---")
    os.makedirs(args.output_dir, exist_ok=True)

    results = []
    for row in rows:
        video_path = os.path.join(args.video_dir, row["video_file"])
        print(f"  Processing: {row['video_file']} ({row['canonical_name']}, class_index={row['class_index']}) ...",
              end=" ", flush=True)
        result = process_single_video(
            video_path=video_path,
            canonical_name=row["canonical_name"],
            asl_id=row["asl_id"],
            class_index=int(row["class_index"]),
            output_dir=args.output_dir,
            dry_run=False,
        )
        status = "OK" if result["success"] else f"FAILED — {result['error']}"
        print(status)
        results.append(result)

    # ── Summary ───────────────────────────────────────────────────────────────
    success = [r for r in results if r["success"]]
    failed  = [r for r in results if not r["success"]]

    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"  Total processed : {len(results)}")
    print(f"  Succeeded       : {len(success)}")
    print(f"  Failed          : {len(failed)}")

    if failed:
        print("\n  FAILURES:")
        for r in failed:
            print(f"    [{r['vid']}]: {r['error']}")

    if success:
        seq_lens = [r["seq_len"] for r in success]
        total_nans = sum(r["nans"] for r in success)
        total_infs = sum(r["infs"] for r in success)
        print(f"\n  Sequence length range : {min(seq_lens)} – {max(seq_lens)} frames")
        print(f"  Total NaN values      : {total_nans}")
        print(f"  Total Inf values      : {total_infs}")
        print(f"  Feature dimension     : {EXPECTED_FEATURE_DIM}")

        # ── Dimension integrity check on written files ────────────────────────
        print("\n--- Post-extraction dimension verification ---")
        dim_errors = []
        for r in success:
            stem = os.path.splitext(r["vid"])[0]
            npy_path = os.path.join(args.output_dir, f"{stem}_features.npy")
            arr = np.load(npy_path)
            if arr.ndim != 2 or arr.shape[1] != EXPECTED_FEATURE_DIM:
                dim_errors.append(f"{r['vid']}: shape={arr.shape}")
            else:
                print(f"  OK: {r['vid']} → shape={arr.shape}")
        if dim_errors:
            print("\nDIMENSION ERRORS (DO NOT USE THESE FILES FOR TRAINING):")
            for e in dim_errors:
                print(f"  {e}")
        else:
            print("\n  All extracted features pass 366-D dimension check.")

    # ── Write experiment report ───────────────────────────────────────────────
    report_path = os.path.join(args.output_dir, "extraction_report.json")
    with open(report_path, "w") as f:
        json.dump({
            "total": len(results),
            "succeeded": len(success),
            "failed": len(failed),
            "failures": [{"vid": r["vid"], "error": r["error"]} for r in failed],
            "sequence_lengths": {r["vid"]: r["seq_len"] for r in success},
            "total_nans": sum(r["nans"] for r in success),
            "total_infs": sum(r["infs"] for r in success),
            "feature_dimension": EXPECTED_FEATURE_DIM,
            "fps_target": FPS_TARGET,
            "v2_scalars_path": SCALARS_PATH,
            "isolation_note": "DO_NOT_MERGE without review",
        }, f, indent=2)
    print(f"\n  Experiment report written: {report_path}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
