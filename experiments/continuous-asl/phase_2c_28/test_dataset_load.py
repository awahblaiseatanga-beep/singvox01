import sys
from pathlib import Path

base_dir = Path(r"d:\Singvox\Singvox")
sys.path.append(str(base_dir / "experiments" / "continuous-asl" / "phase_2c_27"))

from dataset import How2SignAttentionDataset
from tokenizer import BPETokenizer

manifest_path = base_dir / "experiments" / "continuous-asl" / "phase_2c_26" / "dataset_manifest.csv"
feat_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_26" / "features"
tok_path = base_dir / "experiments" / "continuous-asl" / "phase_2c_27" / "tokenizer.json"

tokenizer = BPETokenizer.load(tok_path)

print("Calling How2SignAttentionDataset for train...")
ds_train = How2SignAttentionDataset(manifest_path, feat_dir, tokenizer, split="train", max_frames=150)
print(f"Resulting len: {len(ds_train)}")

print("Calling How2SignAttentionDataset for val...")
ds_val = How2SignAttentionDataset(manifest_path, feat_dir, tokenizer, split="val", max_frames=150)
print(f"Resulting len: {len(ds_val)}")

print("Calling How2SignAttentionDataset for test...")
ds_test = How2SignAttentionDataset(manifest_path, feat_dir, tokenizer, split="test", max_frames=150)
print(f"Resulting len: {len(ds_test)}")
