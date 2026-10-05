import os
import cv2
import csv
import json
import argparse
import random
import time
import mediapipe as mp
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description="SignVox FRESH Hand Pipeline Diagnostic")
    parser.add_argument("--splits", type=str, nargs='+', default=[
        r"D:\ASL_Citizen\ASL_Citizen\splits\train.csv",
        r"D:\ASL_Citizen\ASL_Citizen\splits\val.csv",
        r"D:\ASL_Citizen\ASL_Citizen\splits\test.csv"
    ], help="Path to split CSVs")
    parser.add_argument("--video_dir", type=str, default=r"D:\ASL_Citizen\ASL_Citizen\videos", help="Directory containing the video files")
    parser.add_argument("--vocab_json", type=str, default=r"docs\ai-ml\asl100_vocabulary.json", help="Path to frozen vocabulary JSON")
    parser.add_argument("--sample_size", type=int, default=50, help="Number of videos to sample")
    parser.add_argument("--frames_per_video", type=int, default=5, help="Number of frames to sample per video")
    parser.add_argument("--output_json", type=str, default="hand_pipeline_results.json", help="Output JSON path")
    parser.add_argument("--output_md", type=str, default=r"docs\ai-ml\hand_pipeline_comparison.md", help="Output Markdown report path")
    return parser.parse_args()

def load_asl100_glosses(vocab_json):
    if not os.path.exists(vocab_json):
        print(f"Watch out: {vocab_json} not found. Cannot filter to ASL-100 glosses.")
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
            print(f"Warning: {split_file} not found.")
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
    selected = random.sample(videos, sample_count)
    return selected

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

def run_diagnostic():
    args = parse_args()
    
    mp_holistic = mp.solutions.holistic
    mp_hands = mp.solutions.hands
    
    valid_glosses = load_asl100_glosses(args.vocab_json)
    selected_videos = load_and_sample_manifest(args.splits, args.sample_size, valid_glosses)
    
    stats = {
        "holistic": {"left": 0, "right": 0, "either": 0, "both": 0, "time_ms": 0.0},
        "hands": {"left": 0, "right": 0, "either": 0, "both": 0, "time_ms": 0.0},
        "total_frames_analyzed": 0,
        "total_videos_analyzed": 0,
        "unique_signers": 0,
        "per_video": []
    }
    
    if not selected_videos:
        print("No videos selected. Ensure the ASL Citizen splits exist.")
        
    holistic = mp_holistic.Holistic(static_image_mode=True, min_detection_confidence=0.5)
    hands = mp_hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.5)
    
    unique_signers_set = set()
    
    for row in selected_videos:
        vid_id = row.get('Video file')
        signer = row.get('Participant ID')
        video_path = os.path.join(args.video_dir, vid_id)
            
        if not os.path.exists(video_path):
            continue
            
        frames = extract_frames(video_path, args.frames_per_video)
        if not frames:
            continue
            
        stats["total_videos_analyzed"] += 1
        unique_signers_set.add(signer)
        
        vid_stats = {"video": vid_id, "frames": len(frames), "hol_either": 0, "han_either": 0}
        
        for frame in frames:
            stats["total_frames_analyzed"] += 1
            
            # Run Holistic
            t0 = time.time()
            holistic_results = holistic.process(frame)
            t1 = time.time()
            stats["holistic"]["time_ms"] += (t1 - t0) * 1000
            
            hol_left = holistic_results.left_hand_landmarks is not None
            hol_right = holistic_results.right_hand_landmarks is not None
            
            # Run Hands
            t0 = time.time()
            hands_results = hands.process(frame)
            t1 = time.time()
            stats["hands"]["time_ms"] += (t1 - t0) * 1000
            
            han_left = False
            han_right = False
            if hands_results.multi_handedness:
                for handedness in hands_results.multi_handedness:
                    label = handedness.classification[0].label
                    if label == "Left": han_left = True
                    if label == "Right": han_right = True
                    
            # Tally Holistic
            if hol_left: stats["holistic"]["left"] += 1
            if hol_right: stats["holistic"]["right"] += 1
            if hol_left or hol_right: 
                stats["holistic"]["either"] += 1
                vid_stats["hol_either"] += 1
            if hol_left and hol_right: stats["holistic"]["both"] += 1
            
            # Tally Hands
            if han_left: stats["hands"]["left"] += 1
            if han_right: stats["hands"]["right"] += 1
            if han_left or han_right: 
                stats["hands"]["either"] += 1
                vid_stats["han_either"] += 1
            if han_left and han_right: stats["hands"]["both"] += 1
            
        stats["per_video"].append(vid_stats)
                
    holistic.close()
    hands.close()
    
    stats["unique_signers"] = len(unique_signers_set)
    
    os.makedirs(os.path.dirname(os.path.abspath(args.output_json)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.output_md)), exist_ok=True)
    
    with open(args.output_json, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
        
    avg_hol_time = stats["holistic"]["time_ms"] / max(1, stats["total_frames_analyzed"])
    avg_han_time = stats["hands"]["time_ms"] / max(1, stats["total_frames_analyzed"])
        
    report = f"""# FRESH DIAGNOSTIC SAMPLE: Hand Pipeline Comparison

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Environment:** Python 3.12.14, MediaPipe 0.10.21, OpenCV 4.11.0, NumPy 1.26.4
**Dataset Source:** ASL Citizen Official Dataset
**Split Files Used:** {', '.join([os.path.basename(p) for p in args.splits])}

*WARNING: This is a FRESH independently drafted test sweep. This data is explicitly NOT the historical 2,606-video subset extracted upstream.*

## Methodology
- **Sampling:** Random pull from official split pools constrained to mapped ASL-100 canonical gloss aliases.
- **Sample Size Target:** {args.sample_size} videos
- **Actual Analyzed:** {stats['total_videos_analyzed']} videos
- **Frames per Video:** {args.frames_per_video}
- **Unique Signers:** {stats['unique_signers']}
- **Total Frames Evaluated:** {stats['total_frames_analyzed']}

## Configurations
- **MediaPipe Holistic:** static_image_mode=True, min_detection_confidence=0.5
- **MediaPipe Hands:** static_image_mode=True, max_num_hands=2, min_detection_confidence=0.5

## Important Caveat
DETECTION IS NOT RECALL. Detector bounding counts do NOT equate to "ground-truth visibility" inside the spatial signing volume. 
A detector flagging `False` could be a true visual occlusion or a bounding model miss. These metrics measure strictly how often the algorithms assert they see a hand.

## Aggregate Results

| Metric | Holistic Detection Rate | Dedicated Hands Detection Rate |
| --- | --- | --- |
| **Left Hand** | {stats['holistic']['left']} detections | {stats['hands']['left']} detections |
| **Right Hand** | {stats['holistic']['right']} detections | {stats['hands']['right']} detections |
| **Either Hand** | {stats['holistic']['either']} detections | {stats['hands']['either']} detections |
| **Both Hands** | {stats['holistic']['both']} detections | {stats['hands']['both']} detections |
| **Avg MS / Frame** | {avg_hol_time:.2f} ms | {avg_han_time:.2f} ms |

## Interpreting Differences
The raw frame-checks demonstrate relative performance boundaries in strict static environments. MediaPipe Hands naturally processes faster without parsing body/pose graphs, while Holistic inherently ties vectors securely to shoulder/elbow mapping hierarchies. Evaluation points towards testing processing tradeoffs versus density gains if Hands asserts higher trigger volume under motion blur profiles.
"""
    with open(args.output_md, 'w', encoding='utf-8') as f:
        f.write(report)
        
    print(f"Diagnostic completed successfully! See report at: {args.output_md}")

if __name__ == "__main__":
    run_diagnostic()
