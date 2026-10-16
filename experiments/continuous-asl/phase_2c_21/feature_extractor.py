import os
import sys
import glob
import cv2
import csv
import json
import numpy as np
import time

try:
    import mediapipe as mp
except ImportError:
    print("DEPENDENCY ERROR: mediapipe not installed.", file=sys.stderr)
    sys.exit(1)

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\preprocessing")
from hybrid_landmark_extractor import (
    normalize_landmarks,
    get_crop_bounds,
    extract_hand_from_crop
)

def run_extraction():
    sandbox_dir = r"d:\Singvox\Singvox\data\sandbox_continuous\how2sign_sample"
    out_dir = r"d:\Singvox\Singvox\experiments\continuous-asl\phase_2c_21\features"
    os.makedirs(out_dir, exist_ok=True)

    csv_path = os.path.join(sandbox_dir, "how2sign_val.csv")
    annotations = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            annotations[row['SENTENCE_NAME']] = row

    mp_holistic = mp.solutions.holistic
    mp_hands = mp.solutions.hands
    
    holistic = mp_holistic.Holistic(static_image_mode=False, min_detection_confidence=0.5)
    hands_detector = mp_hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.4)

    face_idx = list(range(25))
    
    mp4_files = glob.glob(os.path.join(sandbox_dir, "*.mp4"))
    print(f"Discovered {len(mp4_files)} mp4 files.")

    stats = {
        "videos_processed": 0,
        "videos_failed": 0,
        "total_frames": 0,
        "extracted_shapes": {}
    }

    t_start = time.time()

    for idx, video_path in enumerate(mp4_files):
        vid_basename = os.path.splitext(os.path.basename(video_path))[0]
        # match annotation
        annot_id = vid_basename.replace('-1-rgb_front', '')
        if annot_id not in annotations and vid_basename not in annotations:
            print(f"Skipping {vid_basename}: No translation found.")
            continue
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            stats['videos_failed'] += 1
            print(f"Skipping {vid_basename}: cv2 failed to open.")
            continue

        sequence_features = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            stats["total_frames"] += 1
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_h, img_w, _ = frame_rgb.shape
            
            res_holistic = holistic.process(frame_rgb)
            
            def extract_hand_full(landmarks):
                arr = np.zeros((21, 3))
                if landmarks:
                    for i, lm in enumerate(landmarks.landmark):
                        arr[i] = [lm.x, lm.y, lm.z]
                    return arr, True
                return arr, False

            lh_active, lh_valid = extract_hand_full(res_holistic.left_hand_landmarks)
            rh_active, rh_valid = extract_hand_full(res_holistic.right_hand_landmarks)
            
            if not lh_valid:
                crop = get_crop_bounds(res_holistic.pose_landmarks, img_h, img_w, "Left")
                if crop:
                    x1, y1, x2, y2 = crop
                    c_img = frame_rgb[y1:y2, x1:x2]
                    res_hands = hands_detector.process(c_img)
                    if res_hands.multi_hand_landmarks:
                        for h_idx, h in enumerate(res_hands.multi_handedness):
                            if h.classification[0].label == "Right": # left in real
                                arr, _ = extract_hand_from_crop(res_hands.multi_hand_landmarks[h_idx], x1, y1, x2, y2, img_w, img_h)
                                lh_active = arr
                                break

            if not rh_valid:
                crop = get_crop_bounds(res_holistic.pose_landmarks, img_h, img_w, "Right")
                if crop:
                    x1, y1, x2, y2 = crop
                    c_img = frame_rgb[y1:y2, x1:x2]
                    res_hands = hands_detector.process(c_img)
                    if res_hands.multi_hand_landmarks:
                        for h_idx, h in enumerate(res_hands.multi_handedness):
                            if h.classification[0].label == "Left": 
                                arr, _ = extract_hand_from_crop(res_hands.multi_hand_landmarks[h_idx], x1, y1, x2, y2, img_w, img_h)
                                rh_active = arr
                                break

            pose_33 = np.zeros((33, 5))
            if res_holistic.pose_landmarks:
                for i_lm, lm in enumerate(res_holistic.pose_landmarks.landmark):
                    pose_33[i_lm] = [lm.x, lm.y, lm.z, lm.visibility, lm.presence]
                    
            face_25 = np.zeros((25, 3))
            if res_holistic.face_landmarks:
                for i_out, i_in in enumerate(face_idx):
                    lm = res_holistic.face_landmarks.landmark[i_in]
                    face_25[i_out] = [lm.x, lm.y, lm.z]
                    
            p_n, l_n, r_n, f_n = normalize_landmarks(pose_33, lh_active, rh_active, face_25)
            feature = np.concatenate([l_n.flatten(), r_n.flatten(), p_n.flatten(), f_n.flatten()])
            sequence_features.append(feature)
            
        cap.release()
        
        if len(sequence_features) > 0:
            seq_array = np.array(sequence_features, dtype=np.float32)
            np.save(os.path.join(out_dir, f"{vid_basename}.npy"), seq_array)
            stats["extracted_shapes"][vid_basename] = seq_array.shape
            stats["videos_processed"] += 1
            
        if (idx+1) % 10 == 0:
            print(f"Processed {idx+1}/{len(mp4_files)} videos...")

    holistic.close()
    hands_detector.close()

    t_end = time.time()
    
    with open(os.path.join(out_dir, "extraction_stats.json"), "w") as f:
        json.dump(stats, f, indent=2)

    print("\n--- EXTRACTION COMPLETE ---")
    print(f"Total processed safely: {stats['videos_processed']}")
    print(f"Total frames converted: {stats['total_frames']}")
    print(f"Failed decodes: {stats['videos_failed']}")
    print(f"Operation time: {t_end - t_start:.2f}s")
    
if __name__ == "__main__":
    run_extraction()
