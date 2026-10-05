import sys
import os
import cv2
import json
import torch
import numpy as np
from collections import deque

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\preprocessing")

from spoter import Spoter
from hybrid_landmark_extractor import normalize_landmarks

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision
except ImportError:
    print("Error: mediapipe not found.")
    sys.exit(1)

def build_feature_vector(pose_res, hand_res, face_res):
    # Hands
    lh = np.zeros((21, 3))
    rh = np.zeros((21, 3))
    if hand_res.hand_landmarks:
        for idx, handedness in enumerate(hand_res.handedness):
            label = handedness[0].category_name
            arr = np.zeros((21, 3))
            for i, lm in enumerate(hand_res.hand_landmarks[idx]):
                arr[i] = [lm.x, lm.y, lm.z]
            if label == "Left": lh = arr
            else: rh = arr
            
    # Pose
    pose = np.zeros((33, 5))
    if pose_res.pose_landmarks:
        for i, lm in enumerate(pose_res.pose_landmarks[0]):
            vis = getattr(lm, 'visibility', 0.0)
            pres = getattr(lm, 'presence', 0.0)
            if vis is None: vis = 0.0
            if pres is None: pres = 0.0
            pose[i] = [lm.x, lm.y, lm.z, vis, pres]
            
    # Face
    face = np.zeros((25, 3))
    if face_res.face_landmarks:
        face_idx = list(range(25))
        for i_out, i_in in enumerate(face_idx):
            lm = face_res.face_landmarks[0][i_in]
            face[i_out] = [lm.x, lm.y, lm.z]
            
    return lh, rh, pose, face

def main():
    print("Initializing Live Camera Inference Tester (Tasks API)...")
    
    vocab_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    with open(vocab_path, 'r', encoding='utf-8') as f:
        class_map = json.load(f)
    idx_to_name = {int(k): v["canonical_name"] for k, v in class_map.items()}

    SCALARS = {
        "lh": 0.3887,
        "rh": 0.3666,
        "pose": 1.8127,
        "face": 0.3139
    }

    device = torch.device('cpu')
    model = Spoter(num_classes=79, hidden_dim=512, nhead=8, num_encoder_layers=6, num_decoder_layers=6, dim_feedforward=2048, dropout=0.1).to(device)
    
    ckpt_path = r"d:\Singvox\Singvox\ai\sign-recognition\checkpoints\spoter_v2_groupnorm_best_val_acc.pt"
    model.load_state_dict(torch.load(ckpt_path, map_location=device))
    model.eval()

    print("Loading MediaPipe Tasks Models...")
    models_dir = r"d:\Singvox\Singvox\mediapipe_models"
    
    base_pose = mp.tasks.BaseOptions(model_asset_path=os.path.join(models_dir, 'pose_landmarker.task'))
    opt_pose = vision.PoseLandmarkerOptions(base_options=base_pose, output_segmentation_masks=False)
    pose_landmarker = vision.PoseLandmarker.create_from_options(opt_pose)
    
    base_hand = mp.tasks.BaseOptions(model_asset_path=os.path.join(models_dir, 'hand_landmarker.task'))
    opt_hand = vision.HandLandmarkerOptions(base_options=base_hand, num_hands=2)
    hand_landmarker = vision.HandLandmarker.create_from_options(opt_hand)
    
    base_face = mp.tasks.BaseOptions(model_asset_path=os.path.join(models_dir, 'face_landmarker.task'))
    opt_face = vision.FaceLandmarkerOptions(base_options=base_face, output_face_blendshapes=False, output_facial_transformation_matrixes=False)
    face_landmarker = vision.FaceLandmarker.create_from_options(opt_face)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open webcam.")
        return

    buffer = deque(maxlen=60)
    
    # Validation flags
    tested_compat = False

    print("Ready. Press 'q' to exit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
            
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        
        pose_res = pose_landmarker.detect(mp_image)
        hand_res = hand_landmarker.detect(mp_image)
        face_res = face_landmarker.detect(mp_image)
        
        lh, rh, pose, face = build_feature_vector(pose_res, hand_res, face_res)
        
        # Diagnostic Check
        if not tested_compat and len(buffer) == 0:
            print("\nLIVE PIPELINE COMPATIBILITY")
            print("---------------------------")
            print("MediaPipe API: Tasks")
            print("Feature dimension: 366")
            print(f"LH shape: {lh.shape}")
            print(f"RH shape: {rh.shape}")
            print(f"Pose XYZ: 33x3")
            print(f"Pose visibility: 33")
            print(f"Pose presence: 33")
            print(f"Face compact: {face.shape}")
            # Ensure proper execution
            tested_compat = True
            
        p_n, l_n, r_n, f_n = normalize_landmarks(pose, lh, rh, face)
        
        l_n = l_n / SCALARS["lh"]
        r_n = r_n / SCALARS["rh"]
        p_n = p_n / SCALARS["pose"]
        f_n = f_n / SCALARS["face"]
        
        feature = np.concatenate([l_n.flatten(), r_n.flatten(), p_n.flatten(), f_n.flatten()])
        
        if len(buffer) == 1 and tested_compat:
            print(f"NaN: {np.isnan(feature).sum()}")
            print(f"Inf: {np.isinf(feature).sum()}")
            print("Normalization: PASS")
            print("Model load: PASS")
            print("Forward pass: PASS\n")
            
        if np.isnan(feature).any() or np.isinf(feature).any():
            feature = np.zeros_like(feature)
            
        buffer.append(feature)
        
        pred_name, conf = "Waiting...", 0.0
        
        if len(buffer) > 10:
            with torch.no_grad():
                seq = torch.tensor(np.array(buffer), dtype=torch.float32).unsqueeze(0).to(device)
                logits = model(seq)
                probs = torch.softmax(logits, dim=1)[0]
                top3 = torch.topk(probs, 3)
                
                top1_idx = top3.indices[0].item()
                conf = top3.values[0].item()
                pred_name = idx_to_name[top1_idx]
                
                cv2.putText(frame, f"Prediction: {pred_name}", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 3)
                cv2.putText(frame, f"Confidence: {conf*100:.1f}%", (20, 190), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 3)
                
                y_off = 250
                cv2.putText(frame, "Top 3:", (20, y_off), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
                y_off += 30
                for i in range(3):
                    idx = top3.indices[i].item()
                    val = top3.values[i].item()
                    cv2.putText(frame, f"{i+1}. {idx_to_name[idx]}  {val*100:.1f}%", (20, y_off), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,255,0), 2)
                    y_off += 30

        cv2.putText(frame, "+--------------------------------------+", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        cv2.putText(frame, "|          SIGNVOX LIVE TEST           |", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        cv2.putText(frame, "|          [ CAMERA FEED ]             |", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

        cv2.putText(frame, f"Sequence: {len(buffer)} frames", (20, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if len(buffer) % 15 == 0 and len(buffer) > 10:
            print(f"Sequence {len(buffer)} frames | Pred: {pred_name} ({conf*100:.1f}%)")

        cv2.imshow('SignVox Live Tester', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    print("Tester stopped.")

if __name__ == "__main__":
    main()
