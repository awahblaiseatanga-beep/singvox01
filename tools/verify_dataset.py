import os
import json
import csv
import numpy as np
import random

def verify_dataset():
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping_dict = json.load(f)
        
    asl_to_index = {
        data["asl_id"]: data["class_index"] 
        for key, data in mapping_dict.items()
    }
    
    # 1. Verification of class index bounds
    indices = list(asl_to_index.values())
    assert min(indices) == 0 and max(indices) == 78, "Labels must range from 0 to 78"
    assert len(set(indices)) == 79, "Every class index must map to exactly one ASL class"
    
    splits = {"train": [], "val": [], "test": []}
    seen_videos = set()
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = list(csv.DictReader(f))
        
    for row in reader:
        base_name = os.path.splitext(row['video_file'])[0]
        npy_path = os.path.join(features_dir, f"{base_name}_features.npy")
        
        # 2. No missing sequence files
        assert os.path.exists(npy_path), f"Missing sequence file: {npy_path}"
        assert row['video_file'] not in seen_videos, f"Duplicate row: {row['video_file']}"
        seen_videos.add(row['video_file'])
        
        splits[row['source_split']].append({
            "video_file": row['video_file'],
            "npy_path": npy_path,
            "class_index": asl_to_index[row['asl_id']]
        })
        
    # Check for split leakage (they should be disjoint)
    assert len(set(x["video_file"] for x in splits["train"]).intersection(set(x["video_file"] for x in splits["val"]))) == 0
    assert len(set(x["video_file"] for x in splits["train"]).intersection(set(x["video_file"] for x in splits["test"]))) == 0
    assert len(set(x["video_file"] for x in splits["val"]).intersection(set(x["video_file"] for x in splits["test"]))) == 0
    
    random.seed(42)
    np.random.seed(42)
    
    report = {}
    
    # Batch size 8
    for split_name, items in splits.items():
        # Deterministic sort then shuffle
        items.sort(key=lambda x: x["video_file"])
        random.shuffle(items)
        
        batch = items[:8]
        lengths = []
        labels = []
        nan_inf_found = False
        
        for item in batch:
            seq = np.load(item['npy_path'])
            lengths.append(len(seq))
            labels.append(item['class_index'])
            if np.isnan(seq).any() or np.isinf(seq).any():
                nan_inf_found = True
                
        assert not nan_inf_found, "NaN or Inf found in sequences"
        
        max_len = max(lengths)
        report[split_name] = {
            "batch_size": len(batch),
            "padded_tensor_shape": [len(batch), max_len, 366],
            "mask_shape": [len(batch), max_len],
            "original_sequence_lengths": lengths,
            "feature_dimension": 366,
            "labels": labels,
            "class_index_bounds": [min(labels), max(labels)]
        }
        
    print(json.dumps(report, indent=2))
    print("Verification Passed Successfully!")

if __name__ == "__main__":
    verify_dataset()
