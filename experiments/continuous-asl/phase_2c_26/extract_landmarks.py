import os
import sys
import glob
import time
import shutil
import json
import cv2
import numpy as np
from pathlib import Path
from multiprocessing import Pool, cpu_count
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

BASE_DIR = Path(r"d:\Singvox\Singvox")
VIDEO_DIR = BASE_DIR / "data" / "continuous_how2sign_val" / "videos"
OUT_FEAT_DIR = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_26" / "features"
OLD_FEAT_DIR = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_22" / "features"
EXP_DIR = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_26"
STATS_PATH = EXP_DIR / "extraction_stats.json"

MP_MODELS = BASE_DIR / "mediapipe_models"

def normalize_landmarks(pose_33, left_21, right_21, face_25):
    p_out = pose_33.copy()
    l_out = left_21.copy()
    r_out = right_21.copy()
    f_out = face_25.copy()
    
    if np.sum(pose_33) == 0:
        return p_out, l_out, r_out, f_out

    s_left = pose_33[11][:3] 
    s_right = pose_33[12][:3]
    if np.sum(s_left) == 0 or np.sum(s_right) == 0:
        return p_out, l_out, r_out, f_out
        
    center_x = (s_left[0] + s_right[0]) / 2.0
    center_y = (s_left[1] + s_right[1]) / 2.0
    dist = np.sqrt(np.sum((s_left - s_right)**2))
    scale = dist if dist > 0.01 else 1.0

    def norm_array(arr):
        out = arr.copy()
        for i in range(out.shape[0]):
            if np.sum(out[i, :3]) != 0:
                out[i, 0] = (out[i, 0] - center_x) / scale
                out[i, 1] = (out[i, 1] - center_y) / scale
                out[i, 2] = out[i, 2] / scale
        return out
        
    return norm_array(p_out), norm_array(l_out), norm_array(r_out), norm_array(f_out)

# Worker initializer
worker_landmarkers = {}

def init_worker():
    pose_opts = vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(MP_MODELS / "pose_landmarker.task")),
        running_mode=vision.RunningMode.IMAGE
    )
    face_opts = vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(MP_MODELS / "face_landmarker.task")),
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1
    )
    hand_opts = vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(MP_MODELS / "hand_landmarker.task")),
        running_mode=vision.RunningMode.IMAGE,
        num_hands=2
    )

    worker_landmarkers['pose'] = vision.PoseLandmarker.create_from_options(pose_opts)
    worker_landmarkers['face'] = vision.FaceLandmarker.create_from_options(face_opts)
    worker_landmarkers['hand'] = vision.HandLandmarker.create_from_options(hand_opts)

def process_single_video(vpath_str):
    vpath = Path(vpath_str)
    stem = vpath.stem
    target_npy = OUT_FEAT_DIR / f"{stem}.npy"
    
    if target_npy.exists():
        try:
            arr = np.load(target_npy)
            return {
                "stem": stem,
                "status": "cached",
                "frames": arr.shape[0],
                "nan_inf": int(np.isnan(arr).any() or np.isinf(arr).any()),
                "missing_lh": int(np.all(arr[:, :63] == 0)),
                "missing_rh": int(np.all(arr[:, 63:126] == 0))
            }
        except Exception:
            pass

    p_lm = worker_landmarkers['pose']
    f_lm = worker_landmarkers['face']
    h_lm = worker_landmarkers['hand']

    cap = cv2.VideoCapture(str(vpath))
    seq = []
    has_nan_inf = False
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        f_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=f_rgb)
        
        p_res = p_lm.detect(mp_img)
        f_res = f_lm.detect(mp_img)
        h_res = h_lm.detect(mp_img)
        
        pose_33 = np.zeros((33, 5))
        if p_res.pose_landmarks and len(p_res.pose_landmarks) > 0:
            for i, lm in enumerate(p_res.pose_landmarks[0]):
                pose_33[i] = [lm.x, lm.y, lm.z, lm.visibility, lm.presence]
                
        face_25 = np.zeros((25, 3))
        if f_res.face_landmarks and len(f_res.face_landmarks) > 0:
            for i in range(25):
                lm = f_res.face_landmarks[0][i]
                face_25[i] = [lm.x, lm.y, lm.z]
                
        lh_arr = np.zeros((21, 3))
        rh_arr = np.zeros((21, 3))
        if h_res.hand_landmarks:
            for idx_h, handedness in enumerate(h_res.handedness):
                label = handedness[0].category_name
                target = rh_arr if label == "Right" else lh_arr 
                for i, lm in enumerate(h_res.hand_landmarks[idx_h]):
                    target[i] = [lm.x, lm.y, lm.z]
                    
        p, l, r, f = normalize_landmarks(pose_33, lh_arr, rh_arr, face_25)
        feat = np.concatenate([l.flatten(), r.flatten(), p.flatten(), f.flatten()]).astype(np.float32)
        if np.isnan(feat).any() or np.isinf(feat).any():
            has_nan_inf = True
        seq.append(feat)
        
    cap.release()
    
    if len(seq) > 0:
        arr = np.array(seq, dtype=np.float32)
        np.save(target_npy, arr)
        return {
            "stem": stem,
            "status": "extracted",
            "frames": len(seq),
            "nan_inf": int(has_nan_inf),
            "missing_lh": int(np.all(arr[:, :63] == 0)),
            "missing_rh": int(np.all(arr[:, 63:126] == 0))
        }
    else:
        return {
            "stem": stem,
            "status": "failed",
            "frames": 0,
            "nan_inf": 0,
            "missing_lh": 0,
            "missing_rh": 0
        }

def run_pipeline():
    OUT_FEAT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Reuse existing Phase 2C.22 features
    print("Step 1: Reusing existing Phase 2C.22 features if available...")
    reused = 0
    if OLD_FEAT_DIR.exists():
        for old_npy in OLD_FEAT_DIR.glob("*.npy"):
            target = OUT_FEAT_DIR / old_npy.name
            if not target.exists():
                shutil.copy2(old_npy, target)
                reused += 1
            else:
                reused += 1
    print(f"Reused/Cached {reused} feature arrays from Phase 2C.22.")
    
    # 2. Get list of video files ordered by split: val -> test -> train
    import csv
    manifest_csv = EXP_DIR / "dataset_manifest.csv"
    if manifest_csv.exists():
        with open(manifest_csv, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        val_stems = [r["SENTENCE_NAME"] for r in rows if r["SPLIT"] == "val"]
        test_stems = [r["SENTENCE_NAME"] for r in rows if r["SPLIT"] == "test"]
        train_stems = [r["SENTENCE_NAME"] for r in rows if r["SPLIT"] == "train"]
        ordered_stems = val_stems + test_stems + train_stems
        all_videos = [VIDEO_DIR / f"{s}.mp4" for s in ordered_stems if (VIDEO_DIR / f"{s}.mp4").exists()]
    else:
        all_videos = sorted(list(VIDEO_DIR.glob("*.mp4")))
    print(f"Total video clips to process: {len(all_videos)}")
    
    tasks = [str(v) for v in all_videos]
    num_workers = max(1, cpu_count() - 1)
    print(f"Starting landmark extraction with {num_workers} parallel workers...")
    
    t0 = time.time()
    results = []
    completed = 0
    
    with Pool(processes=num_workers, initializer=init_worker) as pool:
        for res in pool.imap_unordered(process_single_video, tasks, chunksize=5):
            results.append(res)
            completed += 1
            if completed % 100 == 0 or completed == len(tasks):
                elapsed = time.time() - t0
                fps_est = sum(r["frames"] for r in results) / max(0.1, elapsed)
                print(f"Progress: [{completed}/{len(tasks)}] clips (Elapsed: {elapsed:.1f}s, {fps_est:.1f} frames/s)")
                
    elapsed_total = time.time() - t0
    
    # Analyze summary stats
    extracted_count = sum(1 for r in results if r["status"] in ["extracted", "cached"])
    failed_count = sum(1 for r in results if r["status"] == "failed")
    nan_inf_count = sum(r["nan_inf"] for r in results)
    missing_lh_count = sum(r["missing_lh"] for r in results)
    missing_rh_count = sum(r["missing_rh"] for r in results)
    lengths = [r["frames"] for r in results if r["frames"] > 0]
    total_frames = sum(lengths)
    
    stats = {
        "total_videos": len(all_videos),
        "successfully_extracted": extracted_count,
        "failed_extractions": failed_count,
        "total_frames": total_frames,
        "elapsed_seconds": round(elapsed_total, 2),
        "nan_infinity_sequences": nan_inf_count,
        "completely_missing_left_hand_clips": missing_lh_count,
        "completely_missing_right_hand_clips": missing_rh_count,
        "sequence_length_stats": {
            "min": int(np.min(lengths)) if lengths else 0,
            "max": int(np.max(lengths)) if lengths else 0,
            "mean": round(float(np.mean(lengths)), 2) if lengths else 0,
            "median": round(float(np.median(lengths)), 2) if lengths else 0
        }
    }
    
    with open(STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        
    print("\nExtraction Summary:")
    print(f"  Total Clips: {stats['total_videos']}")
    print(f"  Successfully Extracted: {stats['successfully_extracted']}")
    print(f"  Failed: {stats['failed_extractions']}")
    print(f"  Total Frames: {stats['total_frames']}")
    print(f"  Elapsed Time: {stats['elapsed_seconds']}s")
    print(f"  NaN / Inf Sequences: {stats['nan_infinity_sequences']}")
    print(f"  Sequence Length: Min={stats['sequence_length_stats']['min']}, Max={stats['sequence_length_stats']['max']}, Mean={stats['sequence_length_stats']['mean']}, Median={stats['sequence_length_stats']['median']}")
    print(f"Saved extraction stats to {STATS_PATH}")

if __name__ == "__main__":
    run_pipeline()
