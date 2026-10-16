import time
import torch
import csv
from model import AttentionSeq2Seq
from dataset import How2SignAttentionDataset, attention_collate_fn
from tokenizer import BPETokenizer
from torch.utils.data import DataLoader
from pathlib import Path

print("Profiling 1 training batch...", flush=True)
base_dir = Path(r"d:\Singvox\Singvox")
exp_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_27"
exp26_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_26"
manifest_path = exp26_dir / "dataset_manifest.csv"
feat_dir = exp26_dir / "features"
tok_path = exp_dir / "tokenizer.json"

tokenizer = BPETokenizer.load(tok_path)
vocab_size = len(tokenizer.token2id)

print("Loading dataset...", flush=True)
train_dataset = How2SignAttentionDataset(manifest_path, feat_dir, tokenizer, split="train", max_frames=150)
print(f"Dataset created with {len(train_dataset)} samples.", flush=True)

loader = DataLoader(
    train_dataset,
    batch_size=16,
    shuffle=False,
    collate_fn=lambda b: attention_collate_fn(b, pad_token_id=tokenizer.pad_id)
)

model = AttentionSeq2Seq(
    vocab_size=vocab_size,
    in_features=366,
    hidden_dim=128,
    embed_dim=64,
    attn_dim=64,
    pad_id=tokenizer.pad_id,
    sos_id=tokenizer.sos_id,
    eos_id=tokenizer.eos_id,
    dropout=0.2
)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
criterion = torch.nn.CrossEntropyLoss(ignore_index=tokenizer.pad_id)

print("Fetching first batch from DataLoader...", flush=True)
t0 = time.time()
for batch in loader:
    t_load = time.time() - t0
    src = batch["src"]
    src_mask = batch["src_mask"]
    tgt = batch["tgt"]
    print(f"Batch loaded in {t_load:.3f}s. src: {src.shape}, tgt: {tgt.shape}", flush=True)
    
    t1 = time.time()
    logits = model(src, src_mask, tgt, teacher_forcing_ratio=0.5)
    t_fwd = time.time() - t1
    print(f"Forward pass took {t_fwd:.3f}s", flush=True)
    
    t2 = time.time()
    targets = tgt[:, 1:].contiguous().view(-1)
    logits_flat = logits.contiguous().view(-1, vocab_size)
    loss = criterion(logits_flat, targets)
    loss.backward()
    optimizer.step()
    t_bwd = time.time() - t2
    print(f"Backward pass took {t_bwd:.3f}s. Total step: {t_fwd + t_bwd:.3f}s", flush=True)
    break

