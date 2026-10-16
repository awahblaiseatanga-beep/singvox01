import csv
import json
import re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(r"d:\Singvox\Singvox")
ASL_CITIZEN_DIR = Path(r"D:\ASL_Citizen\ASL_Citizen")
SPLITS_DIR = ASL_CITIZEN_DIR / "splits"
VIDEOS_DIR = ASL_CITIZEN_DIR / "videos"
VOCAB_SPEC = REPO_ROOT / "docs" / "ai-ml" / "ASL_100_VOCABULARY_SPEC.md"
OLD_MAPPING_PATH = REPO_ROOT / "ai" / "sign-recognition" / "config" / "asl100_asl_citizen_mapping.json"

def parse_vocab_spec():
    lines = VOCAB_SPEC.read_text(encoding="utf-8").splitlines()
    classes = []
    table_started = False
    for line in lines:
        if line.strip().startswith("| # | Gloss / concept |"):
            table_started = True
            continue
        if table_started:
            if not line.strip().startswith("|"):
                if classes:
                    break
                continue
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 6 and parts[0].isdigit():
                idx = int(parts[0])
                raw_gloss = parts[1].replace("**", "").strip()
                category = parts[2]
                difficulty = parts[3]
                priority = parts[4]
                note = parts[5] if len(parts) > 5 else ""
                asl_id = f"ASL_{idx:03d}"
                classes.append({
                    "id": idx,
                    "asl_id": asl_id,
                    "name": raw_gloss,
                    "category": category,
                    "difficulty": difficulty,
                    "priority": priority,
                    "note": note
                })
    return classes

def normalize_text(text):
    text = text.upper().strip()
    # Normalize punctuation/spaces
    text = re.sub(r"['’]", "", text)
    text = re.sub(r"[-_/]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def load_all_asl_citizen():
    records = []
    all_glosses = defaultdict(list)
    unique_videos = set()
    
    for split_name in ["train", "val", "test"]:
        csv_file = SPLITS_DIR / f"{split_name}.csv"
        if not csv_file.exists():
            print(f"Warning: {csv_file} does not exist!")
            continue
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row["Participant ID"].strip()
                vfile = row["Video file"].strip()
                gloss = row["Gloss"].strip()
                code = row["ASL-LEX Code"].strip() if "ASL-LEX Code" in row else ""
                rec = {
                    "participant_id": pid,
                    "video_file": vfile,
                    "gloss": gloss,
                    "norm_gloss": normalize_text(gloss),
                    "code": code,
                    "split": split_name
                }
                records.append(rec)
                all_glosses[gloss].append(rec)
                unique_videos.add(vfile)
                
    print(f"Total ASL Citizen rows: {len(records)}")
    print(f"Total unique videos referenced: {len(unique_videos)}")
    print(f"Total distinct raw glosses: {len(all_glosses)}")
    return records, all_glosses

def audit():
    classes = parse_vocab_spec()
    print(f"Parsed {len(classes)} classes from vocabulary spec.")
    assert len(classes) == 100, f"Expected 100 classes, got {len(classes)}"

    records, all_glosses = load_all_asl_citizen()

    # Build normalized gloss lookup map: normalized_gloss -> list of raw glosses
    norm_to_raw = defaultdict(set)
    for g in all_glosses.keys():
        norm_to_raw[normalize_text(g)].add(g)

    # Load old mapping for comparison
    with open(OLD_MAPPING_PATH, "r", encoding="utf-8") as f:
        old_mapping = json.load(f)
    old_map_by_id = {item["asl_id"]: item for item in old_mapping}

    results = []

    for c in classes:
        asl_id = c["asl_id"]
        cname = c["name"]
        
        # Analyze potential gloss representations in ASL Citizen
        # 1. Exact match on canonical name
        # 2. Canonical name split on '/' (e.g. TODAY/NOW, PAIN/HURT, FINE/OKAY, ME/PRO1, YOU/PRO2, AFRAID/SCARED, NICE/CLEAN)
        slash_parts = [p.strip() for p in cname.split("/")]
        
        candidates = set()
        for p in slash_parts:
            norm_p = normalize_text(p)
            # direct raw matches
            if p in all_glosses:
                candidates.add(p)
            # normalized matches
            if norm_p in norm_to_raw:
                for rg in norm_to_raw[norm_p]:
                    candidates.add(rg)
            # check numeric variants like "WANT 2", "WANT2", "HOT 2", etc.
            for g in all_glosses.keys():
                norm_g = normalize_text(g)
                # match pattern like "P" followed by digit, e.g. "WANT 2" -> "WANT 2"
                m = re.match(r"^" + re.escape(norm_p) + r"\s*(\d+)$", norm_g)
                if m:
                    candidates.add(g)
        
        # Also check what old mapping had
        old_item = old_map_by_id.get(asl_id, {})
        old_glosses = old_item.get("source_glosses", [])
        for og in old_glosses:
            if og in all_glosses:
                candidates.add(og)

        # Check total videos for these candidates
        candidate_videos = []
        for g in candidates:
            candidate_videos.extend(all_glosses[g])
        
        # Unique signers and video files
        unique_v = set(r["video_file"] for r in candidate_videos)
        unique_signers = set(r["participant_id"] for r in candidate_videos)

        results.append({
            "idx": c["id"],
            "asl_id": asl_id,
            "canonical_name": cname,
            "category": c["category"],
            "difficulty": c["difficulty"],
            "priority": c["priority"],
            "old_mapping_type": old_item.get("mapping_type", "unknown"),
            "old_glosses": old_glosses,
            "candidates_found": sorted(list(candidates)),
            "num_candidate_videos": len(candidate_videos),
            "num_unique_videos": len(unique_v),
            "num_unique_signers": len(unique_signers),
            "sample_records": candidate_videos[:3]
        })

    # Summary analysis
    print("\n--- AUDIT SUMMARY BY CLASS ---")
    zero_candidates = []
    has_candidates = []
    
    for r in results:
        status_str = f"Found {r['num_unique_videos']} vids across {r['num_unique_signers']} signers from glosses {r['candidates_found']}"
        if r['num_unique_videos'] == 0:
            zero_candidates.append(r)
            print(f"[{r['asl_id']}] {r['canonical_name']}: ZERO CANDIDATES (Old: {r['old_mapping_type']})")
        else:
            has_candidates.append(r)
            # print first 10 and every 10th
            if r['idx'] <= 10 or r['idx'] % 10 == 0:
                print(f"[{r['asl_id']}] {r['canonical_name']}: {status_str}")

    print(f"\nTotal classes with >= 1 candidate video: {len(has_candidates)}/100")
    print(f"Total classes with 0 candidate videos: {len(zero_candidates)}/100")
    
    # Save full audit JSON
    out_json = REPO_ROOT / "experiments" / "spoter_v3" / "stage_a_dataset_audit.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Saved audit results to {out_json}")

if __name__ == "__main__":
    audit()
