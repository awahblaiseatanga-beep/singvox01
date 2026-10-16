import os
import csv
import collections
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SANDBOX_CSV_PATH = BASE_DIR / "data" / "sandbox_continuous" / "how2sign_sample" / "how2sign_val.csv"
FEATURES_DIR = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_22" / "features"
OUT_DIR = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_24"

def generate_splits():
    available_features = set()
    if FEATURES_DIR.exists():
        for f in FEATURES_DIR.glob("*.npy"):
            available_features.add(f.stem)
            
    video_groups = collections.defaultdict(list)
    seen_ids = set()
    
    with open(SANDBOX_CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            sentence_name = row.get("SENTENCE_NAME", "").strip()
            video_id = row.get("VIDEO_ID", "").strip()
            
            if sentence_name in available_features and sentence_name not in seen_ids:
                seen_ids.add(sentence_name)
                video_groups[video_id].append(row)
                
    video_ids = sorted(list(video_groups.keys()))
    print(f"Total Video IDs Found: {len(video_ids)}")
    
    train_ids = video_ids[:3]
    val_ids = [video_ids[3]] if len(video_ids) > 3 else []
    test_ids = [video_ids[4]] if len(video_ids) > 4 else []
    
    for split_name, ids in zip(["train", "val", "test"], [train_ids, val_ids, test_ids]):
        split_path = OUT_DIR / f"{split_name}.csv"
        rows = []
        for vid in ids:
            rows.extend(video_groups[vid])
            
        with open(split_path, 'w', encoding='utf-8', newline='') as f:
            if not rows: continue
            writer = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter='\t')
            writer.writeheader()
            writer.writerows(rows)
            
        print(f"Split '{split_name}': {len(rows)} sentences across {len(ids)} video sessions.")
        
if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generate_splits()
