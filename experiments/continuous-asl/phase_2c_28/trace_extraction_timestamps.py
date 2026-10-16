import os
import csv
from pathlib import Path
from datetime import datetime

base_dir = Path(r"d:\Singvox\Singvox")
feat_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_26" / "features"
manifest_path = base_dir / "experiments" / "continuous-asl" / "phase_2c_26" / "dataset_manifest.csv"

with open(manifest_path, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

row_map = {r["SENTENCE_NAME"]: r for r in rows}

files_with_mtime = []
for p in feat_dir.glob("*.npy"):
    mtime = p.stat().st_mtime
    files_with_mtime.append((mtime, p.stem))

files_with_mtime.sort(key=lambda x: x[0])

print(f"Total files: {len(files_with_mtime)}")
t_first = datetime.fromtimestamp(files_with_mtime[0][0])
t_last = datetime.fromtimestamp(files_with_mtime[-1][0])
print(f"First file written: {t_first}")
print(f"Last file written: {t_last}")
print(f"Span: {t_last - t_first}")

# Check train/val/test counts as files were created chronologically
running_train = 0
running_val = 0
running_test = 0

milestones = []
for idx, (mtime, stem) in enumerate(files_with_mtime, 1):
    r = row_map.get(stem)
    if r:
        if r["SPLIT"] == "train":
            running_train += 1
        elif r["SPLIT"] == "val":
            running_val += 1
        elif r["SPLIT"] == "test":
            running_test += 1
    
    # Check if total files reached specific numbers
    if idx in [500, 964, 1000, 1048, 1200, 1399, 1500, 1739]:
        dt = datetime.fromtimestamp(mtime)
        milestones.append((idx, dt, running_train, running_val, running_test))
    
    # Check if train files reached specific numbers
    if running_train in [964, 1004, 1048, 1215] and (not milestones or milestones[-1][2] != running_train):
        dt = datetime.fromtimestamp(mtime)
        milestones.append((idx, dt, running_train, running_val, running_test))

print("\n--- CHRONOLOGICAL EXTRACTION MILESTONES ---")
for total, dt, tr, va, te in milestones:
    print(f"Total files={total:4d} at {dt.strftime('%H:%M:%S')} | Train={tr:4d}, Val={va:3d}, Test={te:3d}")
