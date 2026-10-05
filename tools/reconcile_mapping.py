import os
import csv
import json
import re
from collections import defaultdict

def run_mapping():
    dataset_dir = r"D:\ASL_Citizen\ASL_Citizen"
    splits_dir = os.path.join(dataset_dir, "splits")
    vocab_path = r"d:\Singvox\Singvox\docs\ai-ml\asl100_vocabulary.json"

    splits = ["train.csv", "val.csv", "test.csv"]
    raw_data = [] 
    
    available_gloss_to_videos = defaultdict(int)
    
    for spl in splits:
        p = os.path.join(splits_dir, spl)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    g = row.get("Gloss", "").strip()
                    if not g: continue
                    g_upper = g.upper()
                    available_gloss_to_videos[g_upper] += 1
                    raw_data.append((spl, row))

    with open(vocab_path, 'r', encoding='utf-8') as f:
        vocab_data = json.load(f)

    def normalize_str(s):
        s = s.upper()
        s = s.replace("'", "")
        s = s.replace("-", " ")
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    source_gloss_normalized = {k: normalize_str(k) for k in available_gloss_to_videos.keys()}
    
    mappings = []
    
    for item in vocab_data.get("classes", []):
        canon = item["name"]
        aliases = item.get("aliases", [])
        
        target_keys = [canon.upper()] + [a.upper() for a in aliases]
        target_norm = [normalize_str(k) for k in target_keys]
        
        found_sources = set()
        status = "NO_SOURCE_MATCH"
        
        for k in target_keys:
            if k in available_gloss_to_videos:
                found_sources.add(k)
                if k == canon.upper():
                    status = "EXACT"
                elif status != "EXACT":
                    status = "ALIAS_MATCH"
                    
        if not found_sources:
            for source_k, norm_source in source_gloss_normalized.items():
                if norm_source in target_norm:
                    found_sources.add(source_k)
                    status = "NORMALIZATION_VARIANT"
                    
        mappings.append({
            "asl_id": item["id"],
            "canonical_name": canon,
            "aliases": aliases,
            "source_glosses": list(found_sources),
            "mapping_type": status,
            "notes": ""
        })

    gloss_to_class = defaultdict(list)
    for m in mappings:
        for g in m["source_glosses"]:
            gloss_to_class[g].append(m["canonical_name"])

    for m in mappings:
        collision = False
        for g in m["source_glosses"]:
            if len(gloss_to_class[g]) > 1:
                collision = True
                
        if collision:
            m["mapping_type"] = "REQUIRES_REVIEW"
            m["notes"] = f"Collision on gloss(es): {[g for g in m['source_glosses'] if len(gloss_to_class[g]) > 1]}"
            m["source_glosses"] = [] 

    config_mappings = []
    for m in mappings:
        ct = m["mapping_type"]
        if ct == "REQUIRES_REVIEW":
            final_type = "review"
        elif not m["source_glosses"]:
            final_type = "unavailable"
        elif ct == "EXACT":
            final_type = "exact"
        elif ct == "ALIAS_MATCH":
            final_type = "alias"
        elif ct == "NORMALIZATION_VARIANT":
            final_type = "normalized"
        else:
            final_type = "unavailable"
            
        cfg = {
            "asl_id": m["asl_id"],
            "canonical_name": m["canonical_name"],
            "source_glosses": m["source_glosses"],
            "mapping_type": final_type,
            "notes": m["notes"]
        }
        config_mappings.append(cfg)

    os.makedirs(r"d:\Singvox\Singvox\ai\sign-recognition\config", exist_ok=True)
    with open(r"d:\Singvox\Singvox\ai\sign-recognition\config\asl100_asl_citizen_mapping.json", 'w') as f:
        json.dump(config_mappings, f, indent=2)

    valid_source_to_canon = {}
    for cfg in config_mappings:
        for g in cfg["source_glosses"]:
            valid_source_to_canon[g] = cfg["canonical_name"]
            
    mapped_c = set()
    total_vid = 0
    split_counts = {"train.csv": 0, "val.csv": 0, "test.csv": 0}
    signers_set = set()
    
    for spl, row in raw_data:
        g = row.get("Gloss", "").strip().upper()
        if g in valid_source_to_canon:
            canon = valid_source_to_canon[g]
            mapped_c.add(canon)
            total_vid += 1
            split_counts[spl] += 1
            p = row.get("Participant ID", "").strip()
            signers_set.add(p)

    ambig_count = len([m for m in config_mappings if m["mapping_type"] == "review"])

    print("--- RECONCILIATION TRACE ---")
    for m in mappings:
        if m["mapping_type"] in ["NORMALIZATION_VARIANT", "REQUIRES_REVIEW"] or not m["source_glosses"]:
            print(f"{m['canonical_name']} -> TYPE: {m['mapping_type']} | SOURCES: {m['source_glosses']} | NOTES: {m['notes']}")

    print("\n--- COVERAGE METRICS ---")
    print(f"Mapped Classes: {len(mapped_c)}")
    print(f"Unmapped Classes: {100 - len(mapped_c)}")
    print(f"Ambiguous: {ambig_count}")
    print(f"Total Videos: {total_vid}")
    print(f"Train/Val/Test: {split_counts['train.csv']} / {split_counts['val.csv']} / {split_counts['test.csv']}")
    print(f"Unique Signers: {len(signers_set)}")

if __name__ == "__main__":
    run_mapping()
