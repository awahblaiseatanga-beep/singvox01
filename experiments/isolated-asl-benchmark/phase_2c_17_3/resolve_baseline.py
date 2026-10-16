import os, sys, json, csv
from collections import Counter

def main():
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
        asl_to_index = {data["asl_id"]: data["class_index"] for _, data in mapping.items()}
        index_to_asl = {data["class_index"]: data["asl_id"] for _, data in mapping.items()}
        
    labels = []
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['source_split'] == 'val':
                labels.append(asl_to_index[row['asl_id']])
                
    counts = Counter(labels)
    total = sum(counts.values())
    
    majority_class_index = counts.most_common(1)[0][0]
    majority_count = counts.most_common(1)[0][1]
    baseline_acc = majority_count / total
    
    # Let's see if 2.29% vs 2.61% was because 2.61% was the majority for the TRAIN set evaluated on val, or just different splits.
    train_labels = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['source_split'] == 'train':
                train_labels.append(asl_to_index[row['asl_id']])
                
    train_counts = Counter(train_labels)
    train_majority_class_index = train_counts.most_common(1)[0][0]
    train_majority_val_support = counts[train_majority_class_index]
    train_maj_val_acc = train_majority_val_support / total
    
    result = {
        "val_samples_total": total,
        "val_majority": {
            "class_index": majority_class_index,
            "class_asl_id": index_to_asl[majority_class_index],
            "count": majority_count,
            "accuracy": baseline_acc
        },
        "train_majority_applied_to_val": {
            "train_majority_class_index": train_majority_class_index,
            "train_majority_class_asl_id": index_to_asl[train_majority_class_index],
            "val_support_count": train_majority_val_support,
            "accuracy": train_maj_val_acc
        }
    }
    
    with open(r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\phase_2c_17_3\baseline_resolution.json", "w") as f:
        json.dump(result, f, indent=2)
        
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
