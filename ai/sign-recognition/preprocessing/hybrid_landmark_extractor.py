import os
import cv2
import csv
import json
import numpy as np
import time
from datetime import datetime
import sys
import argparse
import random

try:
    import mediapipe as mp
except ImportError:
    print("DEPENDENCY ERROR: mediapipe not installed.", file=sys.stderr)
    sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description="SignVox Hybrid Extraction Crop Fallback")
    parser.add_argument("--splits", type=str, nargs='+', default=[
        r"D:\ASL_Citizen\ASL_Citizen\splits\train.csv",
        r"D:\ASL_Citizen\ASL_Citizen\splits\val.csv",
        r"D:\ASL_Citizen\ASL_Citizen\splits\test.csv"
    ])
    parser.add_argument("--video_dir", type=str, default=r"D:\ASL_Citizen\ASL_Citizen\videos")
    parser.add_argument("--vocab_json", type=str, default=r"docs\ai-ml\asl100_vocabulary.json")
    parser.add_argument("--sample_size", type=int, default=20)
    parser.add_argument("--frames_per_video", type=int, default=5)
    return parser.parse_args()

def load_asl100_glosses(vocab_json):
    if not os.path.exists(vocab_json):
        return set()
    valid_glosses = set()
    with open(vocab_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for c in data.get("classes", []):
            valid_glosses.add(c["name"].upper())
            for alias in c.get("aliases", []):
                valid_glosses.add(alias.upper())
    return valid_glosses

def load_and_sample_manifest(splits, sample_size, valid_glosses):
    videos = []
    for split_file in splits:
        if not os.path.exists(split_file):
            continue
        with open(split_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vid = row.get('Video file')
                part = row.get('Participant ID')
                gloss = row.get('Gloss', '').upper()
                if vid and part:
                    if not valid_glosses or gloss in valid_glosses:
                        videos.append(row)
    if not videos:
        return []
    sample_count = min(sample_size, len(videos))
    return random.sample(videos, sample_count)

def extract_frames(video_path, num_frames):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames = []
    if total_frames > 0:
        indices = [int(i * total_frames / num_frames) for i in range(num_frames)]
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    return frames

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
        dist = np.sqrt((w_x - e_x)**2 + (w_y - e_y)**2)
        margin = int(dist * 1.5) 
        margin = max(margin, int(max(img_w, img_h) * 0.1)) 
        
    x_min = max(0, w_x - margin)
    x_max = min(img_w, w_x + margin)
    y_min = max(0, w_y - margin)
    y_max = min(img_h, w_y + margin)
    
    if x_max - x_min < 10 or y_max - y_min < 10:
        return None
        
    return (x_min, y_min, x_max, y_max)

def extract_hand_from_crop(landmarks, x_min, y_min, x_max, y_max, img_w, img_h):
    arr = np.zeros((21, 3))
    is_present = False
    if landmarks:
        is_present = True
        crop_w = x_max - x_min
        crop_h = y_max - y_min
        for i, lm in enumerate(landmarks.landmark):
            x_full_norm = ((lm.x * crop_w) + x_min) / img_w
            y_full_norm = ((lm.y * crop_h) + y_min) / img_h
            z_full_norm = lm.z * (crop_w / img_w)
            arr[i] = [x_full_norm, y_full_norm, z_full_norm]
    return arr, is_present

def run_hybrid_extraction():
    args = parse_args()
    
    if not os.path.exists(args.video_dir):
        print(f"Error: {args.video_dir} not found.")
        sys.exit(1)

    mp_holistic = mp.solutions.holistic
    mp_hands = mp.solutions.hands
    
    holistic = mp_holistic.Holistic(static_image_mode=False, min_detection_confidence=0.5)
    hands_detector = mp_hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.4)

    stats = {
        "total_frames": 0,
        "holistic_left_accepted": 0,
        "holistic_right_accepted": 0,
        "left_fallback_invoked": 0,
        "right_fallback_invoked": 0,
        "left_recovered": 0,
        "right_recovered": 0,
        "left_still_missing": 0,
        "right_still_missing": 0,
        "both_hands_missing": 0,
        "left_anchor_available": 0,
        "right_anchor_available": 0,
        "left_hands_detected": 0,
        "right_hands_detected": 0,
        "nan_count": 0,
        "inf_count": 0,
        "holistic_time_ms": 0.0,
        "hybrid_time_ms": 0.0,
        "videos_processed": 0
    }

    face_idx = list(range(25))
    os.makedirs(r"d:\Singvox\Singvox\output\hybrid_extracted", exist_ok=True)
    
    valid_glosses = load_asl100_glosses(args.vocab_json)
    selected_videos = load_and_sample_manifest(args.splits, args.sample_size, valid_glosses)
    unique_signers_set = set()
    
    for row in selected_videos:
        vid_id = row.get('Video file')
        signer = row.get('Participant ID')
        v_path = os.path.join(args.video_dir, vid_id)
        if not os.path.exists(v_path): continue
        frames = extract_frames(v_path, args.frames_per_video)
        if not frames: continue
        
        unique_signers_set.add(signer)
        for frame in frames:
            stats["total_frames"] += 1
            img_h, img_w, _ = frame.shape
            
            t0 = time.time()
            res_holistic = holistic.process(frame)
            t_hol = time.time() - t0
            stats["holistic_time_ms"] += t_hol * 1000
            t_hybrid = t_hol
            
            def extract_hand_full(landmarks):
                arr = np.zeros((21, 3))
                if landmarks:
                    for i, lm in enumerate(landmarks.landmark):
                        arr[i] = [lm.x, lm.y, lm.z]
                    return arr, True
                return arr, False

            lh_hol, lh_hol_val = extract_hand_full(res_holistic.left_hand_landmarks)
            rh_hol, rh_hol_val = extract_hand_full(res_holistic.right_hand_landmarks)
            
            lh_active = lh_hol
            rh_active = rh_hol
            l_src, r_src = "missing", "missing"
            
            if lh_hol_val: 
                l_src = "holistic"
                stats["holistic_left_accepted"] += 1
            else: 
                stats["left_fallback_invoked"] += 1
                
            if rh_hol_val: 
                r_src = "holistic"
                stats["holistic_right_accepted"] += 1
            else: 
                stats["right_fallback_invoked"] += 1
                
            if not lh_hol_val:
                crop_bounds = get_crop_bounds(res_holistic.pose_landmarks, img_h, img_w, "Left")
                if crop_bounds:
                    stats["left_anchor_available"] += 1
                    x1, y1, x2, y2 = crop_bounds
                    crop_img = frame[y1:y2, x1:x2]
                    t0_h = time.time()
                    res_hands = hands_detector.process(crop_img)
                    t_hybrid += (time.time() - t0_h)
                    if res_hands.multi_hand_landmarks:
                        stats["left_hands_detected"] += 1
                        for idx, h in enumerate(res_hands.multi_handedness):
                            true_label = "Right" if h.classification[0].label == "Left" else "Left"
                            if true_label == "Left":
                                arr, _ = extract_hand_from_crop(res_hands.multi_hand_landmarks[idx], x1, y1, x2, y2, img_w, img_h)
                                lh_active = arr
                                l_src = "hands_fallback_crop"
                                break

            if not rh_hol_val:
                crop_bounds = get_crop_bounds(res_holistic.pose_landmarks, img_h, img_w, "Right")
                if crop_bounds:
                    stats["right_anchor_available"] += 1
                    x1, y1, x2, y2 = crop_bounds
                    crop_img = frame[y1:y2, x1:x2]
                    t0_h = time.time()
                    res_hands = hands_detector.process(crop_img)
                    t_hybrid += (time.time() - t0_h)
                    if res_hands.multi_hand_landmarks:
                        stats["right_hands_detected"] += 1
                        for idx, h in enumerate(res_hands.multi_handedness):
                            true_label = "Right" if h.classification[0].label == "Left" else "Left"
                            if true_label == "Right":
                                arr, _ = extract_hand_from_crop(res_hands.multi_hand_landmarks[idx], x1, y1, x2, y2, img_w, img_h)
                                rh_active = arr
                                r_src = "hands_fallback_crop"
                                break

            stats["hybrid_time_ms"] += t_hybrid * 1000
            
            if l_src == "hands_fallback_crop": stats["left_recovered"] += 1
            if l_src == "missing": stats["left_still_missing"] += 1
            if r_src == "hands_fallback_crop": stats["right_recovered"] += 1
            if r_src == "missing": stats["right_still_missing"] += 1
            if l_src == "missing" and r_src == "missing": stats["both_hands_missing"] += 1

            pose_33 = np.zeros((33, 5))
            if res_holistic.pose_landmarks:
                for i, lm in enumerate(res_holistic.pose_landmarks.landmark):
                    pose_33[i] = [lm.x, lm.y, lm.z, lm.visibility, lm.presence]
                    
            face_25 = np.zeros((25, 3))
            if res_holistic.face_landmarks:
                for i_out, i_in in enumerate(face_idx):
                    face_25[i_out] = [res_holistic.face_landmarks.landmark[i_in].x, res_holistic.face_landmarks.landmark[i_in].y, res_holistic.face_landmarks.landmark[i_in].z]
                    
            p_n, l_n, r_n, f_n = normalize_landmarks(pose_33, lh_active, rh_active, face_25)
            
            feature = np.concatenate([l_n.flatten(), r_n.flatten(), p_n.flatten(), f_n.flatten()])
            stats["nan_count"] += int(np.isnan(feature).sum())
            stats["inf_count"] += int(np.isinf(feature).sum())
            
        stats["videos_processed"] += 1
        
    holistic.close()
    hands_detector.close()
    
    print("\n--- CLI VALIDATION SUMMARY ---")
    print(f"Total Videos Processed: {stats['videos_processed']}")
    print(f"Unique Signers: {len(unique_signers_set)}")
    print(f"Total Frames: {stats['total_frames']}")
    print(f"Output Feature Dimension: 366-D")
    print(f"NaN Count: {stats['nan_count']}")
    print(f"Inf Count: {stats['inf_count']}")
    
    print("\n[Holistic Anchor]")
    print(f"- Holistic Left Present: {stats['holistic_left_accepted']}")
    print(f"- Holistic Right Present: {stats['holistic_right_accepted']}")
    
    print(f"\n[Provenance]")
    print(f"- Holistic Hand Count Target: {stats['holistic_left_accepted'] + stats['holistic_right_accepted']}")
    print(f"- Crop Fallback Target: {stats['left_recovered'] + stats['right_recovered']}")
    print(f"- Missing: {stats['left_still_missing'] + stats['right_still_missing']}")
    
    print(f"\n[Missing Status]")
    print(f"- Left Still Missing: {stats['left_still_missing']}")
    print(f"- Right Still Missing: {stats['right_still_missing']}")
    print(f"- Both Missing: {stats['both_hands_missing']}")

    print("\n[Granular Fallback Outcomes]")
    print(f"- Left Fallback Invoked: {stats['left_fallback_invoked']}")
    print(f"  -> NO_ANCHOR: {stats['left_fallback_invoked'] - stats['left_anchor_available']}")
    print(f"  -> ANCHOR_BUT_HANDS_FAILED: {stats['left_anchor_available'] - stats['left_recovered']}")
    print(f"  -> RECOVERED: {stats['left_recovered']}")
    print(f"  * Valid anchors: {stats['left_anchor_available']}")
    print(f"  * Detections (Raw inside crop): {stats['left_hands_detected']}")
    
    print(f"\n- Right Fallback Invoked: {stats['right_fallback_invoked']}")
    print(f"  -> NO_ANCHOR: {stats['right_fallback_invoked'] - stats['right_anchor_available']}")
    print(f"  -> ANCHOR_BUT_HANDS_FAILED: {stats['right_anchor_available'] - stats['right_recovered']}")
    print(f"  -> RECOVERED: {stats['right_recovered']}")
    print(f"  * Valid anchors: {stats['right_anchor_available']}")
    print(f"  * Detections (Raw inside crop): {stats['right_hands_detected']}")
    
    print(f"\n[Timing]")
    print(f"- Total Processing Time (ms): {stats['hybrid_time_ms']:.2f}")

    with open(r"d:\Singvox\Singvox\docs\ai-ml\hybrid_fallback_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)

if __name__ == "__main__":
    run_hybrid_extraction()
