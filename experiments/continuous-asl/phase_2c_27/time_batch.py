import sys
import time
from pathlib import Path
import torch
import torch.nn as nn

sys.path.append(r"experiments/continuous-asl/phase_2c_27")
from tokenizer import BPETokenizer
from dataset import How2SignAttentionDataset, attention_collate_fn
from model import AttentionSeq2Seq

base_dir = Path(r"d:\Singvox\Singvox")
exp_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_27"
exp26_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_26"
manifest_path = exp26_dir / "dataset_manifest.csv"
feat_dir = exp26_dir / "features"
tok_path = exp_dir / "tokenizer.json"

tokenizer = BPETokenizer.load(tok_path)
ds = How2SignAttentionDataset(manifest_path, feat_dir, tokenizer, split="train", max_frames=350)
loader = torch.utils.data.DataLoader(ds, batch_size=16, shuffle=False, collate_fn=lambda b: attention_collate_fn(b, pad_token_id=0))

batch = next(iter(loader))
src = batch["src"]
src_mask = batch["src_mask"]
tgt = batch["tgt"]

print("Batch shapes:", src.shape, tgt.shape)

model = AttentionSeq2Seq(len(tokenizer.token2id), in_features=366, hidden_dim=256, embed_dim=128, attn_dim=128)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
criterion = nn.CrossEntropyLoss(ignore_index=0)

t0 = time.time()
logits = model(src, src_mask, tgt, teacher_forcing_ratio=0.5)
t_fwd = time.time() - t0
print(f"Forward pass time: {t_fwd:.3f}s, Logits shape: {logits.shape}")

t0 = time.time()
targets = tgt[:, 1:].contiguous().view(-1)
logits_flat = logits.contiguous().view(-1, len(tokenizer.token2id))
loss = criterion(logits_flat, targets)
loss.backward()
optimizer.step()
t_bwd = time.time() - t0
print(f"Backward pass time: {t_bwd:.3f}s, Loss: {loss.item():.4f}")
print(f"Total single batch time: {t_fwd + t_bwd:.3f}s")
