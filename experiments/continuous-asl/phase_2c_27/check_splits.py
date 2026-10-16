import csv
from collections import Counter

with open("experiments/continuous-asl/phase_2c_26/dataset_manifest.csv", "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

splits = Counter(r["SPLIT"] for r in rows)
print("All manifest rows by split:", splits)

from pathlib import Path

feat_dir = Path("experiments/continuous-asl/phase_2c_26/features")
disk_files = set(p.stem for p in feat_dir.glob("*.npy"))
print(f"Total .npy files physically on disk: {len(disk_files)}")

disk_splits = Counter(r["SPLIT"] for r in rows if r["SENTENCE_NAME"] in disk_files)
print("Actual disk features by split:", disk_splits)

