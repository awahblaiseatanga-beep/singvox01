"""
Targeted extraction for 923 manifest entries missing .npy feature files.
Uses the IDENTICAL pipeline as tools/extract_full_dataset.py:
  - MediaPipe Holistic primary detection
  - Crop-based hands fallback
  - 10 FPS frame sampling
  - 366-D feature vector
  - Shoulder-centered normalization
Outputs: *_features.npy and *_meta.json to ai/sign-recognition/data/dataset_extracted/
"""
import os
import csv
import json
import numpy as np
import time
import multiprocessing
from pathlib import Path
from collections import defaultdict

VIDEO_DIR = r"D:\ASL_Citizen\ASL_Citizen\videos"
OUTPUT_DIR = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
MANIFEST = r"d:\Singvox\Singvox\experiments\spoter_v3\manifests\spoter_v3_matched_manifest.csv"

def extract_frames_10fps(video_path):
    import cv2
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = 30
    frame_interval = max(1, int(round(fps / 10.0)))
    frames = []
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        if count % frame_interval == 0:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        count += 1
    cap.release()
    return frames

def normalize_landmarks(pose_33, left_21, right_21, face_25):
    p_out = pose_33.copy(); l_out = left_21.copy()
    r_out = right_21.copy(); f_out = face_25.copy()
    if np.sum(pose_33) == 0: return p_out, l_out, r_out, f_out
    s_left = pose_33[11][:3]; s_right = pose_33[12][:3]
    if np.sum(s_left) == 0 or np.sum(s_right) == 0: return p_out, l_out, r_out, f_out
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
    if not pose_landmarks: return None
    wrist_idx = 15 if hand_type == "Left" else 16
    elbow_idx = 13 if hand_type == "Left" else 14
    wrist = pose_landmarks.landmark[wrist_idx]
    elbow = pose_landmarks.landmark[elbow_idx]
    if wrist.visibility < 0.1 or wrist.presence < 0.1: return None
    w_x, w_y = int(wrist.x * img_w), int(wrist.y * img_h)
    margin = int(max(img_w, img_h) * 0.15)
    if elbow.visibility >= 0.1 and elbow.presence >= 0.1:
        e_x, e_y = int(elbow.x * img_w), int(elbow.y * img_h)
        dist = np.sqrt((w_x - e_x)**2 + (w_y - e_y)**2)
        margin = max(int(dist * 1.5), int(max(img_w, img_h) * 0.1))
    x_min, x_max = max(0, w_x - margin), min(img_w, w_x + margin)
    y_min, y_max = max(0, w_y - margin), min(img_h, w_y + margin)
    if x_max - x_min < 10 or y_max - y_min < 10: return None
    return (x_min, y_min, x_max, y_max)

def extract_hand_from_crop(landmarks, x_min, y_min, x_max, y_max, img_w, img_h):
    arr = np.zeros((21, 3))
    if landmarks:
        crop_w = x_max - x_min; crop_h = y_max - y_min
        for i, lm in enumerate(landmarks.landmark):
            arr[i] = [((lm.x * crop_w) + x_min) / img_w, ((lm.y * crop_h) + y_min) / img_h, lm.z * (crop_w / img_w)]
        return arr, True
    return arr, False

def process_video(item):
    try:
        import mediapipe as mp
        import cv2
    except ImportError as e:
        return {"vid": item["video_file"], "success": False, "error": str(e)}

    vid_id = item["video_file"]
    asl_id = item["asl_id"]
    canon = item["canonical_name"]
    part = item["participant_id"]
    source_gloss = item["source_gloss"]
    split_key = item["source_split"]

    base_name = os.path.splitext(vid_id)[0]
    out_npy = os.path.join(OUTPUT_DIR, f"{base_name}_features.npy")
    out_meta = os.path.join(OUTPUT_DIR, f"{base_name}_meta.json")

    # Skip if already extracted
    if os.path.exists(out_npy) and os.path.exists(out_meta):
        try:
            arr = np.load(out_npy)
            if len(arr) > 0 and arr.shape[-1] == 366:
                return {"vid": vid_id, "success": True, "error": None, "skipped": True,
                        "nans": 0, "infs": 0, "seq_len": len(arr), "split": split_key, "part": part, "canon": canon}
        except:
            pass

    v_path = os.path.join(VIDEO_DIR, vid_id)
    if not os.path.exists(v_path):
        return {"vid": vid_id, "success": False, "error": "Source video not found"}

    frames = extract_frames_10fps(v_path)
    if not frames:
        return {"vid": vid_id, "success": False, "error": "No frames extracted"}

    mp_holistic = mp.solutions.holistic
    mp_hands = mp.solutions.hands
    holistic = mp_holistic.Holistic(static_image_mode=False, min_detection_confidence=0.5)
    hands_detector = mp_hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.4)
    face_idx = list(range(25))
    seq_features = []
    seq_provenance = []
    nan_c = 0; inf_c = 0

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
                    res_hands = hands_detector.process(frame[y1:y2, x1:x2])
                    if res_hands.multi_hand_landmarks:
                        for idx, h in enumerate(res_hands.multi_handedness):
                            if ("Right" if h.classification[0].label == "Left" else "Left") == "Left":
                                lh_active, _ = extract_hand_from_crop(res_hands.multi_hand_landmarks[idx], x1, y1, x2, y2, img_w, img_h)
                                l_prov = "hands_fallback_crop"
                                break

            if rh_val:
                r_prov = "holistic"
            else:
                cb = get_crop_bounds(res_holistic.pose_landmarks, img_h, img_w, "Right")
                if cb:
                    x1, y1, x2, y2 = cb
                    res_hands = hands_detector.process(frame[y1:y2, x1:x2])
                    if res_hands.multi_hand_landmarks:
                        for idx, h in enumerate(res_hands.multi_handedness):
                            if ("Right" if h.classification[0].label == "Left" else "Left") == "Right":
                                rh_active, _ = extract_hand_from_crop(res_hands.multi_hand_landmarks[idx], x1, y1, x2, y2, img_w, img_h)
                                r_prov = "hands_fallback_crop"
                                break

            pose_33 = np.zeros((33, 5))
            if res_holistic.pose_landmarks:
                for i, lm in enumerate(res_holistic.pose_landmarks.landmark):
                    pose_33[i] = [lm.x, lm.y, lm.z, lm.visibility, lm.presence]

            face_25 = np.zeros((25, 3))
            if res_holistic.face_landmarks:
                for i_out, i_in in enumerate(face_idx):
                    lm = res_holistic.face_landmarks.landmark[i_in]
                    face_25[i_out] = [lm.x, lm.y, lm.z]

            p_n, l_n, r_n, f_n = normalize_landmarks(pose_33, lh_active, rh_active, face_25)
            feature = np.concatenate([l_n.flatten(), r_n.flatten(), p_n.flatten(), f_n.flatten()])
            nan_c += int(np.isnan(feature).sum())
            inf_c += int(np.isinf(feature).sum())
            seq_features.append(feature)
            seq_provenance.append({"left": l_prov, "right": r_prov})
    except Exception as e:
        return {"vid": vid_id, "success": False, "error": f"Crash: {str(e)}"}
    finally:
        holistic.close()
        hands_detector.close()

    if len(seq_features) == 0:
        return {"vid": vid_id, "success": False, "error": "Output length 0"}

    try:
        np.save(out_npy, np.array(seq_features, dtype=np.float32))
        meta = {"video_file": vid_id, "asl_id": asl_id, "canonical_name": canon,
                "source_gloss": source_gloss, "participant_id": part, "source_split": split_key,
                "sequence_length": len(seq_features), "feature_dimension": 366,
                "fps_target": 10, "provenance": seq_provenance}
        with open(out_meta, 'w') as f:
            json.dump(meta, f, indent=2)
    except Exception as e:
        return {"vid": vid_id, "success": False, "error": f"Write failed: {str(e)}"}

    return {"vid": vid_id, "success": True, "error": None, "skipped": False,
            "nans": nan_c, "infs": inf_c, "seq_len": len(seq_features),
            "split": split_key, "part": part, "canon": canon}

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load manifest
    with open(MANIFEST, 'r', encoding='utf-8') as f:
        all_rows = list(csv.DictReader(f))

    # Find the missing ones
    npy_files = {p.name for p in Path(OUTPUT_DIR).glob('*_features.npy')}
    missing_rows = []
    for r in all_rows:
        base = Path(r['video_file']).stem
        if f'{base}_features.npy' not in npy_files:
            missing_rows.append(r)

    print(f"Total manifest rows: {len(all_rows)}")
    print(f"Already extracted: {len(npy_files)}")
    print(f"Need extraction: {len(missing_rows)}")

    if not missing_rows:
        print("Nothing to extract — all feature files present.")
        return

    t0 = time.time()
    num_workers = max(1, min(multiprocessing.cpu_count() - 1, 4))
    print(f"Extracting on {num_workers} workers...")

    with multiprocessing.Pool(num_workers, maxtasksperchild=5) as pool:
        results = pool.map(process_video, missing_rows)

    elapsed = time.time() - t0
    success = [r for r in results if r['success'] and not r.get('skipped')]
    failed = [r for r in results if not r['success']]

    print(f"\n=== Extraction Complete ({elapsed:.1f}s) ===")
    print(f"  Extracted: {len(success)}")
    print(f"  Failed:    {len(failed)}")
    total_nan = sum(r.get('nans', 0) for r in success)
    total_inf = sum(r.get('infs', 0) for r in success)
    print(f"  NaN count: {total_nan}")
    print(f"  Inf count: {total_inf}")

    if failed:
        print("\nFailed videos:")
        for r in failed[:20]:
            print(f"  {r['vid']}: {r['error']}")

    # Write extraction report
    report_path = Path(r"d:\Singvox\Singvox\experiments\spoter_v3\reports\extraction_supplement_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump({"elapsed_seconds": round(elapsed, 2), "extracted": len(success),
                   "failed": len(failed), "nan_count": total_nan, "inf_count": total_inf,
                   "failed_list": [{"vid": r['vid'], "error": r['error']} for r in failed]}, f, indent=2)
    print(f"\nReport saved to {report_path}")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
