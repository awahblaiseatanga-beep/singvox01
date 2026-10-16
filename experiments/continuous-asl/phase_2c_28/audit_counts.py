import os
import csv
from pathlib import Path
from collections import Counter

base_dir = Path(r"d:\Singvox\Singvox")
manifest_p26 = base_dir / "experiments" / "continuous-asl" / "phase_2c_26" / "dataset_manifest.csv"
feat_dir_p26 = base_dir / "experiments" / "continuous-asl" / "phase_2c_26" / "features"
feat_dir_data = base_dir / "data" / "continuous_how2sign_val" / "features"
feat_dir_sandbox = base_dir / "data" / "sandbox_continuous" / "how2sign_sample" / "features"

print("--- AUDITING DIRECTORIES AND MANIFEST ---")
print(f"Manifest path exists: {manifest_p26.exists()}")
print(f"P26 features dir exists: {feat_dir_p26.exists()}")
print(f"Data features dir exists: {feat_dir_data.exists()}")
print(f"Sandbox features dir exists: {feat_dir_sandbox.exists()}")

# 1. Count physical files in each feature directory
p26_files = set(f.stem for f in feat_dir_p26.glob("*.npy")) if feat_dir_p26.exists() else set()
data_files = set(f.stem for f in feat_dir_data.glob("*.npy")) if feat_dir_data.exists() else set()
sandbox_files = set(f.stem for f in feat_dir_sandbox.glob("*.npy")) if feat_dir_sandbox.exists() else set()

print(f"Count in p26 features: {len(p26_files)}")
print(f"Count in data features: {len(data_files)}")
print(f"Count in sandbox features: {len(sandbox_files)}")
print(f"Overlap p26 and data: {len(p26_files.intersection(data_files))}")

# 2. Inspect manifest rows
manifest_rows = []
with open(manifest_p26, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        manifest_rows.append(r)

print(f"\nTotal manifest rows: {len(manifest_rows)}")

split_counts = Counter(r["SPLIT"] for r in manifest_rows)
print(f"Manifest split counts: {dict(split_counts)}")

unique_sentences = set(r["SENTENCE_NAME"] for r in manifest_rows)
print(f"Unique SENTENCE_NAME in manifest: {len(unique_sentences)}")

unique_video_ids = set(r["VIDEO_ID"] for r in manifest_rows)
print(f"Unique VIDEO_ID in manifest: {len(unique_video_ids)}")

video_ids_by_split = {}
for split in ["train", "val", "test"]:
    video_ids_by_split[split] = set(r["VIDEO_ID"] for r in manifest_rows if r["SPLIT"] == split)
    print(f"Unique VIDEO_ID in split '{split}': {len(video_ids_by_split[split])}")

# Check video ID leakage
print("Train-Val VIDEO_ID overlap:", len(video_ids_by_split["train"].intersection(video_ids_by_split["val"])))
print("Train-Test VIDEO_ID overlap:", len(video_ids_by_split["train"].intersection(video_ids_by_split["test"])))
print("Val-Test VIDEO_ID overlap:", len(video_ids_by_split["val"].intersection(video_ids_by_split["test"])))

# 3. Match manifest against feature files in p26 features
p26_present_by_split = Counter()
p26_missing_by_split = Counter()

for r in manifest_rows:
    s = r["SPLIT"]
    name = r["SENTENCE_NAME"]
    if name in p26_files:
        p26_present_by_split[s] += 1
    else:
        p26_missing_by_split[s] += 1

print("\n--- P26 FEATURES MATCHING MANIFEST ---")
print(f"Present by split: {dict(p26_present_by_split)}")
print(f"Missing by split: {dict(p26_missing_by_split)}")
print(f"Total present across all splits: {sum(p26_present_by_split.values())}")

# 4. Check why some logs showed 964 vs 1004 vs 1048
# Let's inspect extraction scripts or check lengths
lengths_p26 = {}
import numpy as np
for r in manifest_rows:
    name = r["SENTENCE_NAME"]
    feat_p = feat_dir_p26 / f"{name}.npy"
    if feat_p.exists():
        try:
            arr = np.load(feat_p, mmap_mode="r")
            lengths_p26[name] = arr.shape[0]
        except Exception as e:
            lengths_p26[name] = -1

print(f"\nTotal readable arrays: {len([k for k, v in lengths_p26.items() if v > 0])}")

# Check length filtering
for cutoff in [150, 300, 500, 600, 1000]:
    cnt_train = sum(1 for r in manifest_rows if r["SPLIT"] == "train" and r["SENTENCE_NAME"] in lengths_p26 and lengths_p26[r["SENTENCE_NAME"]] <= cutoff)
    print(f"Train samples with len <= {cutoff}: {cnt_train}")
