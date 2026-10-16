import csv
from collections import defaultdict

MANIFEST = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
SELECTED_30 = [
    "HELLO", "GOOD", "BAD", "PLEASE", "SORRY", "HELP", "STOP", "WAIT", "YES", "NO",
    "ME", "YOU", "LOVE", "HAPPY", "SAD", "ANGRY",
    "NAME", "LEARN", "TEACHER", "SCHOOL", "WORK", "HOME",
    "WATER", "HUNGRY", "SLEEP", "SICK",
    "GO", "COME", "FINISH", "MORE"
]

class_data = defaultdict(lambda: {"videos": set(), "participants": set(), "train": 0, "val": 0, "test": 0})

try:
    with open(MANIFEST, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            c_name = row.get("canonical_name")
            if c_name in SELECTED_30:
                vid = row.get("video_file")
                pid = row.get("participant_id")
                split = row.get("source_split", "train").lower()

                class_data[c_name]["videos"].add(vid)
                class_data[c_name]["participants"].add(pid)
                class_data[c_name][split] += 1
except Exception as e:
    print(f"Error reading manifest: {e}")

print("=== DATASET UNIQUENESS AUDIT ===")
for c in SELECTED_30:
    d = class_data[c]
    v_count = len(d["videos"])
    p_count = len(d["participants"])
    print(f"[{c}] Videos: {v_count} | Unique Signers: {p_count} | Train: {d['train']} | Val: {d['val']} | Test: {d['test']}")

