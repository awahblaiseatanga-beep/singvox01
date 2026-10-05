import csv
import json
import os

def create_mapping():
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    unique_classes = {}
    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            asl_id = row['asl_id']
            canon = row['canonical_name']
            if asl_id not in unique_classes:
                unique_classes[asl_id] = canon
                
    sorted_ids = sorted(list(unique_classes.keys()))
    
    mapping = {}
    for idx, asl_id in enumerate(sorted_ids):
        mapping[str(idx)] = {
            "class_index": idx,
            "asl_id": asl_id,
            "canonical_name": unique_classes[asl_id]
        }
        
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2)
        
    print(f"Created mapping with {len(mapping)} classes.")

if __name__ == "__main__":
    create_mapping()
