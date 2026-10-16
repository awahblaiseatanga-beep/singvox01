import os
import csv
import json
import numpy as np
from collections import defaultdict

MANIFEST = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
FEATURES_DIR = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
VOCAB_PATH = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"

PILOT_LABELS = ["HELLO", "YES", "NO"]

def verify_pilot_data():
    print("=== WORKSTREAM 2: PILOT DATA VERIFICATION ===")
    
    # 1. Vocabulary Mapping
    with open(VOCAB_PATH, 'r') as f:
        vocab = json.load(f)
    print("Vocabulary Mapping Check:")
    mapped = {}
    for idx, v in vocab.items():
        if v["canonical_name"] in PILOT_LABELS:
            print(f"- Found {v['canonical_name']} at index {idx} -> Source Glosses: {v.get('source_gloss', v.get('source_glosses', 'N/A'))}")
            mapped[v["canonical_name"]] = int(idx)
    
    if len(mapped) != 3:
        print("ERROR: Pilot labels do not map cleanly to vocabulary.")
        return

    # 2. Extract Manifest
    stats = defaultdict(lambda: {"videos": set(), "signers_train": set(), "signers_val": set(), "signers_test": set()})
    
    valid_samples = 0
    invalid_samples = 0
    missing_samples = 0

    with open(MANIFEST, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            canonical = row.get("canonical_name")
            if canonical in PILOT_LABELS:
                vid = row.get("video_file")
                pid = row.get("participant_id")
                split = row.get("source_split", "train").lower()
                
                # Split isolation checks
                if split == "train": stats[canonical]["signers_train"].add(pid)
                elif split == "val": stats[canonical]["signers_val"].add(pid)
                elif split == "test": stats[canonical]["signers_test"].add(pid)
                
                feature_name = vid.replace(".mp4", "_features.npy")
                fpath = os.path.join(FEATURES_DIR, feature_name)
                
                if not os.path.exists(fpath):
                    missing_samples += 1
                    continue
                
                try:
                    feat = np.load(fpath)
                    if feat.shape[0] == 0 or feat.shape[1] != 366:
                        invalid_samples += 1
                    elif np.isnan(feat).any() or np.isinf(feat).any():
                        invalid_samples += 1
                    else:
                        valid_samples += 1
                        stats[canonical]["videos"].add(vid)
                except Exception as e:
                    invalid_samples += 1

    print("\nFeature Sequence Check:")
    print(f"- Valid sequences: {valid_samples}")
    print(f"- Missing files: {missing_samples}")
    print(f"- Invalid arrays (NaN/Inf or bad shape): {invalid_samples}")
    
    print("\nSigner Independence Check:")
    leakage_failures = 0
    for c in sorted(stats.keys()):
        train_val = stats[c]["signers_train"].union(stats[c]["signers_val"])
        test_signers = stats[c]["signers_test"]
        
        overlap = train_val.intersection(test_signers)
        if len(overlap) > 0:
            print(f"- [FAIL] Leakage in {c}! Test signers in Train/Val: {overlap}")
            leakage_failures += 1
        else:
            print(f"- [PASS] {c}: 0 leakage. Test signers fully independent.")
            
    if leakage_failures > 0 or missing_samples > 0 or invalid_samples > 0:
        print("\nDATA VERIFICATION FAILED. Resolution required.")
    else:
        print("\nDATA VERIFICATION PASSED SUCCESSFULLY.")

if __name__ == "__main__":
    verify_pilot_data()
