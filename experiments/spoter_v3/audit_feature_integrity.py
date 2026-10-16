import os
import json
import numpy as np
from pathlib import Path
from collections import defaultdict

FEATURES_DIR = Path(r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted")
OUT_JSON = Path(r"d:\Singvox\Singvox\experiments\spoter_v3\stage_b_feature_integrity.json")

def audit_features():
    npy_files = list(FEATURES_DIR.glob("*_features.npy"))
    print(f"Found {len(npy_files)} feature files in {FEATURES_DIR}")
    
    total_files = len(npy_files)
    total_frames = 0
    nan_files = 0
    inf_files = 0
    dim_mismatches = 0
    lengths = []
    
    classes_found = set()
    split_counts = defaultdict(int)
    
    for idx, f in enumerate(npy_files):
        arr = np.load(f)
        total_frames += arr.shape[0]
        lengths.append(arr.shape[0])
        
        if arr.shape[1] != 366:
            dim_mismatches += 1
            
        if np.isnan(arr).any():
            nan_files += 1
            
        if np.isinf(arr).any():
            inf_files += 1
            
        # Check corresponding meta file
        meta_file = f.with_name(f.name.replace("_features.npy", "_meta.json"))
        if meta_file.exists():
            try:
                with open(meta_file, "r") as mf:
                    meta = json.load(mf)
                    classes_found.add(meta.get("canonical_name", ""))
                    split_counts[meta.get("source_split", "unknown")] += 1
            except Exception:
                pass
                
        if (idx + 1) % 500 == 0 or idx + 1 == total_files:
            print(f"Processed {idx + 1}/{total_files} files...")
            
    summary = {
        "total_feature_files": total_files,
        "expected_feature_dimension": 366,
        "dimension_mismatches": dim_mismatches,
        "nan_files_count": nan_files,
        "inf_files_count": inf_files,
        "total_frames": total_frames,
        "sequence_lengths": {
            "min": int(np.min(lengths)),
            "max": int(np.max(lengths)),
            "mean": float(np.mean(lengths)),
            "median": float(np.median(lengths))
        },
        "classes_represented": len(classes_found),
        "split_distribution": dict(split_counts),
        "integrity_status": "PASSED" if (dim_mismatches == 0 and nan_files == 0 and inf_files == 0) else "FAILED"
    }
    
    with open(OUT_JSON, "w", encoding="utf-8") as out_f:
        json.dump(summary, out_f, indent=2)
        
    print("\n--- FEATURE INTEGRITY AUDIT RESULTS ---")
    print(f"Status: {summary['integrity_status']}")
    print(f"Total Files Audited: {total_files}")
    print(f"Total Frames: {total_frames}")
    print(f"Feature Dimension: 366 (Mismatches: {dim_mismatches})")
    print(f"NaN Files: {nan_files}, Inf Files: {inf_files}")
    print(f"Sequence Lengths: min={summary['sequence_lengths']['min']}, max={summary['sequence_lengths']['max']}, mean={summary['sequence_lengths']['mean']:.1f}, median={summary['sequence_lengths']['median']:.1f}")
    print(f"Splits: {dict(split_counts)}")
    print(f"Saved results to {OUT_JSON}")

if __name__ == "__main__":
    audit_features()
