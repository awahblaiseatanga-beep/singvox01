import sys
import csv
from pathlib import Path
import numpy as np
import json

base_dir = Path(r"d:\Singvox\Singvox")
exp27_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_27"
exp26_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_26"
exp28_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_28"

sys.path.append(str(exp27_dir))
from tokenizer import BPETokenizer

manifest_path = exp26_dir / "dataset_manifest.csv"
tok_path = exp27_dir / "tokenizer.json"
tokenizer = BPETokenizer.load(tok_path)

rows = []
with open(manifest_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

print(f"Total manifest rows: {len(rows)}")

ratios = []
t_lengths = []
l_lengths = []
violations_s1 = 0
violations_s2 = 0
violations_s4 = 0

for row in rows:
    npy_path = exp26_dir / "features" / f"{row['SENTENCE_NAME']}.npy"
    if not npy_path.exists():
        continue
    try:
        feat = np.load(npy_path)
    except Exception:
        continue
    T = min(150, feat.shape[0])
    tokens = tokenizer.encode(str(row["SENTENCE"]), add_special_tokens=False)
    L = len(tokens)
    if L == 0:
        continue
    t_lengths.append(T)
    l_lengths.append(L)
    ratios.append(T / L)
    if T < L:
        violations_s1 += 1
    if (T // 2) < L:
        violations_s2 += 1
    if (T // 4) < L:
        violations_s4 += 1

N = len(t_lengths)
print(f"Valid checked samples: {N}")
print(f"Frames T: min={min(t_lengths)}, median={np.median(t_lengths)}, mean={np.mean(t_lengths):.1f}, max={max(t_lengths)}")
print(f"Tokens L: min={min(l_lengths)}, median={np.median(l_lengths)}, mean={np.mean(l_lengths):.1f}, max={max(l_lengths)}")
print(f"Ratio T/L: min={min(ratios):.2f}, median={np.median(ratios):.2f}, mean={np.mean(ratios):.2f}")
print(f"CTC Violations (T < L, stride 1): {violations_s1} ({violations_s1/N*100:.2f}%)")
print(f"CTC Violations (T//2 < L, stride 2): {violations_s2} ({violations_s2/N*100:.2f}%)")
print(f"CTC Violations (T//4 < L, stride 4): {violations_s4} ({violations_s4/N*100:.2f}%)")

results = {
    "total_samples": N,
    "frames_T": {
        "min": int(min(t_lengths)),
        "median": float(np.median(t_lengths)),
        "mean": round(float(np.mean(t_lengths)), 2),
        "max": int(max(t_lengths))
    },
    "tokens_L": {
        "min": int(min(l_lengths)),
        "median": float(np.median(l_lengths)),
        "mean": round(float(np.mean(l_lengths)), 2),
        "max": int(max(l_lengths))
    },
    "ratio_T_over_L": {
        "min": round(float(min(ratios)), 2),
        "median": round(float(np.median(ratios)), 2),
        "mean": round(float(np.mean(ratios)), 2)
    },
    "ctc_feasibility": {
        "stride_1_violations_pct": round(violations_s1 / N * 100.0, 2),
        "stride_2_violations_pct": round(violations_s2 / N * 100.0, 2),
        "stride_4_violations_pct": round(violations_s4 / N * 100.0, 2)
    }
}

with open(exp28_dir / "hypothesis_feasibility.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved hypothesis_feasibility.json successfully.")
