import json
import csv
from pathlib import Path
from collections import defaultdict

data = json.load(open("experiments/spoter_v3/stage_a_100_class_coverage.json", "r"))
SPLITS_DIR = Path(r"D:\ASL_Citizen\ASL_Citizen\splits")

valid_gloss_to_asl = {}
for d in data:
    for g in d["valid_matched_labels"]:
        valid_gloss_to_asl[g] = (d["asl_id"], d["canonical_name"])

split_counts = defaultdict(lambda: defaultdict(int))
split_signers = defaultdict(lambda: defaultdict(set))
split_total = defaultdict(int)
all_rows = []

for s in ["train", "val", "test"]:
    with open(SPLITS_DIR / f"{s}.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            g = r["Gloss"].strip()
            if g in valid_gloss_to_asl:
                asl_id, cname = valid_gloss_to_asl[g]
                split_counts[s][asl_id] += 1
                split_signers[s][asl_id].add(r["Participant ID"].strip())
                split_total[s] += 1
                all_rows.append({
                    "asl_id": asl_id,
                    "canonical_name": cname,
                    "source_gloss": g,
                    "video_file": r["Video file"].strip(),
                    "participant_id": r["Participant ID"].strip(),
                    "source_split": s,
                    "asl_lex_code": r.get("ASL-LEX Code", "").strip()
                })

print(f"Total matched videos by split:")
print(f"  Train: {split_total['train']}")
print(f"  Val:   {split_total['val']}")
print(f"  Test:  {split_total['test']}")
print(f"  Total: {sum(split_total.values())}")

# Check per-class support in train/val/test
zero_in_train = [d["asl_id"] for d in data if d["num_valid_videos"] > 0 and split_counts["train"][d["asl_id"]] == 0]
zero_in_val = [d["asl_id"] for d in data if d["num_valid_videos"] > 0 and split_counts["val"][d["asl_id"]] == 0]
zero_in_test = [d["asl_id"] for d in data if d["num_valid_videos"] > 0 and split_counts["test"][d["asl_id"]] == 0]

print(f"\nOf 95 accepted classes:")
print(f"  Classes with 0 train samples: {len(zero_in_train)}")
print(f"  Classes with 0 val samples: {len(zero_in_val)}: {zero_in_val}")
print(f"  Classes with 0 test samples: {len(zero_in_test)}: {zero_in_test}")

# Save reproducible manifest
manifest_dir = Path(r"d:\Singvox\Singvox\experiments\spoter_v3\manifests")
manifest_dir.mkdir(parents=True, exist_ok=True)
manifest_csv = manifest_dir / "spoter_v3_matched_manifest.csv"

with open(manifest_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "asl_id", "canonical_name", "source_gloss", "video_file", "participant_id", "source_split", "asl_lex_code"
    ])
    writer.writeheader()
    writer.writerows(all_rows)

print(f"\nSaved {len(all_rows)} rows to {manifest_csv}")
