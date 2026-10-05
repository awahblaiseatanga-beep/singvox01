import os
import csv
import json
from collections import defaultdict, Counter

def run_audit():
    dataset_dir = r"D:\ASL_Citizen\ASL_Citizen"
    splits_dir = os.path.join(dataset_dir, "splits")
    videos_dir = os.path.join(dataset_dir, "videos")
    vocab_path = r"d:\Singvox\Singvox\docs\ai-ml\asl100_vocabulary.json"

    historical_files = [
        "signvox_asl100_manifest.csv",
        "signvox_asl100_manifest.json",
        "vocabulary_mapping.csv",
        "coverage_report.md",
        "processing_report.md",
        "process_asl_citizen.py"
    ]
    
    found_historical = []
    for root, _, fnames in os.walk(r"d:\Singvox\Singvox"):
        if ".git" in root: continue
        for fname in fnames:
            if fname in historical_files:
                found_historical.append(os.path.join(root, fname))

    splits = ["train.csv", "val.csv", "test.csv"]
    available_splits = []
    schemas = {}
    raw_data = [] 
    
    for spl in splits:
        p = os.path.join(splits_dir, spl)
        if os.path.exists(p):
            available_splits.append(spl)
            with open(p, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                schemas[spl] = reader.fieldnames
                for row in reader:
                    raw_data.append((spl, row))

    existing_videos = set()
    if os.path.exists(videos_dir):
        existing_videos = set(os.listdir(videos_dir))
        
    with open(vocab_path, 'r', encoding='utf-8') as f:
        vocab_data = json.load(f)
        
    mapping_rules = defaultdict(list)
    canon_classes = set()
    for item in vocab_data.get("classes", []):
        canon = item["name"]
        canon_classes.add(canon)
        mapping_rules[canon.upper()].append(canon)
        for alias in item.get("aliases", []):
            mapping_rules[alias.upper()].append(canon)
            
    alias_collisions = {k: v for k, v in mapping_rules.items() if len(set(v)) > 1}
    safe_mapping = {k: v[0] for k, v in mapping_rules.items() if len(set(v)) == 1}
    
    class_counts = {c: {"train": 0, "val": 0, "test": 0, "total": 0} for c in canon_classes}
    signer_splits = defaultdict(set)
    video_paths = set()
    duplicates = []
    missing_videos = []
    signer_to_split = {}
    leakage = []
    
    malformed_rows = 0
    total_candidate_videos = 0
    
    for spl, row in raw_data:
        vid = row.get("Video file", "").strip()
        participant = row.get("Participant ID", "").strip()
        gloss = row.get("Gloss", "").strip()
        
        if not vid or not participant or not gloss:
            malformed_rows += 1
            continue
            
        if vid in video_paths:
            duplicates.append(vid)
        video_paths.add(vid)
        
        if vid not in existing_videos:
            missing_videos.append(vid)
            
        split_key = spl.replace(".csv", "")
        
        if participant in signer_to_split and signer_to_split[participant] != split_key:
            leakage.append((participant, signer_to_split[participant], split_key))
        signer_to_split[participant] = split_key
        signer_splits[split_key].add(participant)
            
        g_upper = gloss.upper()
        if g_upper in safe_mapping:
            canon = safe_mapping[g_upper]
            if canon in class_counts:
                class_counts[canon][split_key] += 1
                class_counts[canon]["total"] += 1
                total_candidate_videos += 1

    train_signers = signer_splits["train"]
    val_signers = signer_splits["val"]
    test_signers = signer_splits["test"]
    
    disjoint_check = "PASS"
    if train_signers.intersection(val_signers) or train_signers.intersection(test_signers) or val_signers.intersection(test_signers):
        disjoint_check = "FAIL"
        
    zero_video_classes = [c for c, v in class_counts.items() if v["total"] == 0]
    low_video_classes = [c for c, v in class_counts.items() if 0 < v["total"] < 10]
    
    stats = {
        "dataset_exists": os.path.exists(dataset_dir),
        "available_splits": available_splits,
        "csv_schemas": schemas,
        "historical_artifacts_found": found_historical,
        "alias_collisions": alias_collisions,
        "total_candidate_videos": total_candidate_videos,
        "classes_zero_videos": zero_video_classes,
        "classes_low_videos": low_video_classes,
        "signer_leakage_cases": len(leakage),
        "missing_videos_count": len(missing_videos),
        "duplicate_videos_count": len(duplicates),
        "malformed_rows": malformed_rows,
        "signers_train": len(train_signers),
        "signers_val": len(val_signers),
        "signers_test": len(test_signers),
        "signer_disjoint_status": disjoint_check,
        "mapped_classes_count": len([1 for v in class_counts.values() if v["total"] > 0]),
        "total_canonical_classes": len(canon_classes)
    }
    
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    run_audit()
