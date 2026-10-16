import os
import csv
import json
import random
from pathlib import Path
import numpy as np

BASE_DIR = Path(r"d:\Singvox\Singvox")
EXP_DIR = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_26"
FEAT_DIR = EXP_DIR / "features"
MANIFEST_PATH = EXP_DIR / "dataset_manifest.csv"
METRICS_PATH = EXP_DIR / "dataset_metrics.json"
REPORT_DATA_PATH = EXP_DIR / "verification_audit_summary.json"

def verify_dataset_integrity():
    print("Step 1: Loading manifest and checking feature arrays...")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Total rows in manifest: {len(rows)}")
    
    total_samples = len(rows)
    existing_feats = []
    missing_feats = []
    
    corrupt_arrays = []
    nan_inf_arrays = []
    shape_mismatches = []
    
    num_frames_list = []
    lh_missing_count = 0
    rh_missing_count = 0
    both_hands_missing_count = 0
    
    split_stats = {"train": [], "val": [], "test": []}
    
    for r in rows:
        stem = r["SENTENCE_NAME"]
        split = r["SPLIT"]
        fpath = FEAT_DIR / f"{stem}.npy"
        
        if not fpath.exists():
            missing_feats.append(stem)
            continue
            
        existing_feats.append(stem)
        split_stats[split].append(stem)
        
        try:
            arr = np.load(fpath)
        except Exception as e:
            corrupt_arrays.append((stem, str(e)))
            continue
            
        if arr.ndim != 2 or arr.shape[1] != 366:
            shape_mismatches.append((stem, list(arr.shape)))
            continue
            
        if np.isnan(arr).any() or np.isinf(arr).any():
            nan_inf_arrays.append(stem)
            
        t = arr.shape[0]
        num_frames_list.append(t)
        
        lh_missing = bool(np.all(arr[:, :63] == 0))
        rh_missing = bool(np.all(arr[:, 63:126] == 0))
        
        if lh_missing:
            lh_missing_count += 1
        if rh_missing:
            rh_missing_count += 1
        if lh_missing and rh_missing:
            both_hands_missing_count += 1
            
    print(f"\nFeature Array Status:")
    print(f"  Total Clips in Manifest: {total_samples}")
    print(f"  Feature Files Present: {len(existing_feats)}")
    print(f"  Feature Files Pending/Missing: {len(missing_feats)}")
    print(f"  Corrupt Files: {len(corrupt_arrays)}")
    print(f"  Shape Mismatches (!= [T, 366]): {len(shape_mismatches)}")
    print(f"  NaN / Inf Sequences: {len(nan_inf_arrays)}")
    
    if num_frames_list:
        print(f"\nExtracted Sequence Lengths (Frames):")
        print(f"  Min: {np.min(num_frames_list)}")
        print(f"  Max: {np.max(num_frames_list)}")
        print(f"  Mean: {np.mean(num_frames_list):.1f}")
        print(f"  Median: {np.median(num_frames_list):.1f}")
        print(f"  Total Frames Audited: {sum(num_frames_list)}")
        
        print(f"\nHand Landmark Tracking Statistics:")
        print(f"  Left Hand Completely Absent: {lh_missing_count} ({lh_missing_count/len(existing_feats)*100:.1f}%)")
        print(f"  Right Hand Completely Absent: {rh_missing_count} ({rh_missing_count/len(existing_feats)*100:.1f}%)")
        print(f"  Both Hands Completely Absent: {both_hands_missing_count} ({both_hands_missing_count/len(existing_feats)*100:.1f}%)")
        
    audit_summary = {
        "manifest_total": total_samples,
        "features_present": len(existing_feats),
        "features_pending": len(missing_feats),
        "features_corrupt": len(corrupt_arrays),
        "features_shape_mismatch": len(shape_mismatches),
        "features_nan_inf": len(nan_inf_arrays),
        "sequence_frames": {
            "min": int(np.min(num_frames_list)) if num_frames_list else 0,
            "max": int(np.max(num_frames_list)) if num_frames_list else 0,
            "mean": round(float(np.mean(num_frames_list)), 2) if num_frames_list else 0,
            "median": round(float(np.median(num_frames_list)), 2) if num_frames_list else 0,
            "total_frames": int(sum(num_frames_list)) if num_frames_list else 0
        },
        "missing_hand_rates": {
            "left_hand_absent_count": lh_missing_count,
            "left_hand_absent_pct": round(lh_missing_count / max(1, len(existing_feats)) * 100, 2),
            "right_hand_absent_count": rh_missing_count,
            "right_hand_absent_pct": round(rh_missing_count / max(1, len(existing_feats)) * 100, 2),
            "both_hands_absent_count": both_hands_missing_count,
            "both_hands_absent_pct": round(both_hands_missing_count / max(1, len(existing_feats)) * 100, 2)
        },
        "split_counts_extracted": {
            "train": len(split_stats["train"]),
            "val": len(split_stats["val"]),
            "test": len(split_stats["test"])
        }
    }
    
    with open(REPORT_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)
    print(f"Saved audit summary to {REPORT_DATA_PATH}")

if __name__ == "__main__":
    verify_dataset_integrity()
