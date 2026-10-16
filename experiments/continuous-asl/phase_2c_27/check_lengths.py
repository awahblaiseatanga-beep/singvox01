import csv
import numpy as np

with open("experiments/continuous-asl/phase_2c_26/dataset_manifest.csv", "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

from pathlib import Path

feat_dir = Path("experiments/continuous-asl/phase_2c_26/features")
lengths = []
for p in feat_dir.glob("*.npy"):
    try:
        arr = np.load(p, mmap_mode="r")
        lengths.append(arr.shape[0])
    except Exception:
        pass

lengths = np.array(lengths)
print(f"Total active feature samples: {len(lengths)}")
print(f"Min: {np.min(lengths)}, Max: {np.max(lengths)}")
print(f"Mean: {np.mean(lengths):.1f}, Median: {np.median(lengths):.1f}")
print(f"Percentiles: 50%: {np.percentile(lengths, 50):.1f}, 75%: {np.percentile(lengths, 75):.1f}, 90%: {np.percentile(lengths, 90):.1f}, 95%: {np.percentile(lengths, 95):.1f}")


