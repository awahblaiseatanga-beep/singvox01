from pathlib import Path

feat_dir = Path(r"d:\Singvox\Singvox\experiments\continuous-asl\phase_2c_26\features")
files = list(feat_dir.glob("*.npy"))
print(f"Total extracted feature files: {len(files)}")
