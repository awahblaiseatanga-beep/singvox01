import json

with open("experiments/spoter_v3/stage_a_100_class_coverage.json", "r") as f:
    data = json.load(f)

print(f"Total entries: {len(data)}")
by_id = {d["asl_id"]: d for d in data}

check_ids = [
    "ASL_001", "ASL_005", "ASL_012", "ASL_015", "ASL_026", 
    "ASL_032", "ASL_040", "ASL_045", "ASL_060", "ASL_066", 
    "ASL_074", "ASL_077", "ASL_078", "ASL_082", "ASL_085", "ASL_087"
]

for cid in check_ids:
    item = by_id[cid]
    print(f"[{item['asl_id']}] {item['canonical_name']:<18} | Valid: {item['num_valid_videos']:<3} | Signers: {item['num_distinct_signers']:<2} | Status: {item['mapping_status']:<16} | Labels: {item['valid_matched_labels']}")

total_valid_videos = sum(d["num_valid_videos"] for d in data)
print(f"\nTotal valid videos across all accepted classes: {total_valid_videos}")
zero_classes = [d for d in data if d["num_valid_videos"] == 0]
print(f"Classes with 0 valid videos ({len(zero_classes)}): {[d['asl_id'] + ':' + d['canonical_name'] for d in zero_classes]}")
