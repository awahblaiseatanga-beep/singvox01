import os
import sys
import json
import csv
import time
from pathlib import Path
import cv2
import numpy as np

# Ensure root is in path
ROOT_DIR = Path(r"d:\Singvox\Singvox")
sys.path.append(str(ROOT_DIR / "ai" / "sign-recognition" / "preprocessing"))

import mediapipe as mp
from hybrid_landmark_extractor import normalize_landmarks, get_crop_bounds, extract_hand_from_crop

MANIFEST_PATH = ROOT_DIR / "experiments" / "spoter_v3" / "manifests" / "spoter_v3_matched_manifest.csv"
VIDEO_DIR = Path(r"D:\ASL_Citizen\ASL_Citizen\videos")
AUDIT_JSON_PATH = ROOT_DIR / "experiments" / "spoter_v3" / "stage_b_landmark_audit.json"

def audit_landmark_pipeline(sample_count=10):
    print(f"Loading manifest from {MANIFEST_PATH}...")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    
    # Pick a balanced sample of classes (some old, some newly matched)
    selected = []
    classes_seen = set()
    for r in rows:
        c = r["canonical_name"]
        if c not in classes_seen:
            v_path = VIDEO_DIR / r["video_file"]
            if v_path.exists():
                selected.append(r)
                classes_seen.add(c)
                if len(selected) >= sample_count:
                    break
                    
    print(f"Selected {len(selected)} videos across {len(classes_seen)} distinct classes for landmark verification.")
    
    mp_holistic = mp.solutions.holistic
    mp_hands = mp.solutions.hands
    
    holistic = mp_holistic.Holistic(static_image_mode=False, min_detection_confidence=0.5)
    hands_detector = mp_hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.4)
    face_idx = list(range(25))
    
    results = []
    total_frames = 0
    total_nan = 0
    total_inf = 0
    
    for idx, row in enumerate(selected):
        v_name = row["video_file"]
        v_path = VIDEO_DIR / v_name
        cap = cv2.VideoCapture(str(v_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Sample frames up to 30 frames
        sample_indices = [int(i * frame_count / min(frame_count, 30)) for i in range(min(frame_count, 30))]
        
        frames_features = []
        t0 = time.time()
        
        for f_idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
            
            img_h, img_w, _ = frame.shape
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res_holistic = holistic.process(frame_rgb)
            
            # Left & right hand extraction
            def extract_hand_full(landmarks):
                arr = np.zeros((21, 3))
                if landmarks:
                    for i, lm in enumerate(landmarks.landmark):
                        arr[i] = [lm.x, lm.y, lm.z]
                    return arr, True
                return arr, False

            lh_active, lh_val = extract_hand_full(res_holistic.left_hand_landmarks)
            rh_active, rh_val = extract_hand_full(res_holistic.right_hand_landmarks)
            
            # Fallback for left
            if not lh_val:
                crop = get_crop_bounds(res_holistic.pose_landmarks, img_h, img_w, "Left")
                if crop:
                    x1, y1, x2, y2 = crop
                    crop_img = frame_rgb[y1:y2, x1:x2]
                    res_h = hands_detector.process(crop_img)
                    if res_h.multi_hand_landmarks:
                        for h_i, h in enumerate(res_h.multi_handedness):
                            true_label = "Right" if h.classification[0].label == "Left" else "Left"
                            if true_label == "Left":
                                arr, _ = extract_hand_from_crop(res_h.multi_hand_landmarks[h_i], x1, y1, x2, y2, img_w, img_h)
                                lh_active = arr
                                break
                                
            # Fallback for right
            if not rh_val:
                crop = get_crop_bounds(res_holistic.pose_landmarks, img_h, img_w, "Right")
                if crop:
                    x1, y1, x2, y2 = crop
                    crop_img = frame_rgb[y1:y2, x1:x2]
                    res_h = hands_detector.process(crop_img)
                    if res_h.multi_hand_landmarks:
                        for h_i, h in enumerate(res_h.multi_handedness):
                            true_label = "Right" if h.classification[0].label == "Left" else "Left"
                            if true_label == "Right":
                                arr, _ = extract_hand_from_crop(res_h.multi_hand_landmarks[h_i], x1, y1, x2, y2, img_w, img_h)
                                rh_active = arr
                                break
                                
            pose_33 = np.zeros((33, 5))
            if res_holistic.pose_landmarks:
                for p_i, lm in enumerate(res_holistic.pose_landmarks.landmark):
                    pose_33[p_i] = [lm.x, lm.y, lm.z, lm.visibility, lm.presence]
                    
            face_25 = np.zeros((25, 3))
            if res_holistic.face_landmarks:
                for i_out, i_in in enumerate(face_idx):
                    face_25[i_out] = [res_holistic.face_landmarks.landmark[i_in].x,
                                      res_holistic.face_landmarks.landmark[i_in].y,
                                      res_holistic.face_landmarks.landmark[i_in].z]
                                      
            p_n, l_n, r_n, f_n = normalize_landmarks(pose_33, lh_active, rh_active, face_25)
            feat = np.concatenate([l_n.flatten(), r_n.flatten(), p_n.flatten(), f_n.flatten()]).astype(np.float32)
            frames_features.append(feat)
            
        cap.release()
        duration_ms = (time.time() - t0) * 1000
        
        feat_matrix = np.array(frames_features)
        nans = int(np.isnan(feat_matrix).sum())
        infs = int(np.isinf(feat_matrix).sum())
        total_frames += len(frames_features)
        total_nan += nans
        total_inf += infs
        
        entry = {
            "video_file": v_name,
            "asl_id": row["asl_id"],
            "canonical_name": row["canonical_name"],
            "source_split": row["source_split"],
            "participant_id": row["participant_id"],
            "num_sampled_frames": len(frames_features),
            "feature_dim": feat_matrix.shape[1] if len(frames_features) > 0 else 0,
            "nan_count": nans,
            "inf_count": infs,
            "duration_ms": round(duration_ms, 2)
        }
        results.append(entry)
        print(f"[{idx+1}/{len(selected)}] {row['canonical_name']} ({v_name}): {len(frames_features)} frames, dim={entry['feature_dim']}, NaNs={nans}, Infs={infs}, time={entry['duration_ms']}ms")
        
    holistic.close()
    hands_detector.close()
    
    summary = {
        "videos_audited": len(results),
        "total_frames_audited": total_frames,
        "feature_dimension_verified": 366,
        "all_dimensions_valid": all(r["feature_dim"] == 366 for r in results),
        "total_nan_count": total_nan,
        "total_inf_count": total_inf,
        "status": "PASSED" if (total_nan == 0 and total_inf == 0 and all(r["feature_dim"] == 366 for r in results)) else "FAILED",
        "details": results
    }
    
    with open(AUDIT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    print("\n--- STAGE B LANDMARK AUDIT SUMMARY ---")
    print(f"Status: {summary['status']}")
    print(f"Videos Audited: {summary['videos_audited']}")
    print(f"Total Frames: {summary['total_frames_audited']}")
    print(f"Feature Dimension: 366-D (All valid: {summary['all_dimensions_valid']})")
    print(f"Total NaNs: {total_nan}, Total Infs: {total_inf}")
    print(f"Saved audit results to {AUDIT_JSON_PATH}")

if __name__ == "__main__":
    audit_landmark_pipeline(10)
