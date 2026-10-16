import sys
import os
import time
import json
import random
from pathlib import Path
import numpy as np
import torch
torch.set_num_threads(1)
import torch.nn as nn
from torch.utils.data import DataLoader

sys.path.append(r"experiments/continuous-asl/phase_2c_27")
from tokenizer import BPETokenizer
from dataset import How2SignAttentionDataset, attention_collate_fn
from model import AttentionSeq2Seq

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def log(msg, log_file=None):
    print(msg, flush=True)
    if log_file:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

def train_attention_model():
    set_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    base_dir = Path(r"d:\Singvox\Singvox")
    exp_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_27"
    exp26_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_26"
    manifest_path = exp26_dir / "dataset_manifest.csv"
    feat_dir = exp26_dir / "features"
    tok_path = exp_dir / "tokenizer.json"
    log_file = exp_dir / "train.log"
    
    # Reset log file
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("--- Phase 2C.27 Training Log ---\n")
        
    log(f"Using device: {device}", log_file)
    log("Loading BPE Tokenizer...", log_file)
    tokenizer = BPETokenizer.load(tok_path)
    vocab_size = len(tokenizer.token2id)
    log(f"Tokenizer loaded with vocab size: {vocab_size}", log_file)
    
    train_dataset = How2SignAttentionDataset(manifest_path, feat_dir, tokenizer, split="train", max_frames=150)
    val_dataset = How2SignAttentionDataset(manifest_path, feat_dir, tokenizer, split="val", max_frames=150)
    
    log(f"Train samples available: {len(train_dataset)}", log_file)
    log(f"Val samples available: {len(val_dataset)}", log_file)
    
    if len(train_dataset) == 0:
        log("ERROR: No training samples available!", log_file)
        return
        
    batch_size = 16
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=lambda b: attention_collate_fn(b, pad_token_id=tokenizer.pad_id)
    )
    
    val_loader = None
    if len(val_dataset) > 0:
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
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
    ).to(device)
    
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log(f"Attention Seq2Seq initialized. Trainable parameters: {total_params:,}", log_file)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss(ignore_index=tokenizer.pad_id)
    
    epochs = 10
    best_val_loss = float("inf")
    patience = 4
    patience_counter = 0
    history = []
    
    best_model_path = exp_dir / "best_attention_model.pt"
    
    log("\nStarting Training Loop...", log_file)
    t0_train = time.time()
    
    for epoch in range(1, epochs + 1):
        t0_epoch = time.time()
        model.train()
        train_loss = 0.0
        train_batches = 0
        
        tf_ratio = max(0.4, 0.7 - 0.03 * (epoch - 1))
        
        for batch_idx, batch in enumerate(train_loader):
            src = batch["src"].to(device)
            src_mask = batch["src_mask"].to(device)
            tgt = batch["tgt"].to(device)
            
            optimizer.zero_grad()
            logits = model(src, src_mask, tgt, teacher_forcing_ratio=tf_ratio)
            
            targets = tgt[:, 1:].contiguous().view(-1)
            logits_flat = logits.contiguous().view(-1, vocab_size)
            
            loss = criterion(logits_flat, targets)
            loss.backward()
            
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()
            
            train_loss += loss.item()
            train_batches += 1
            
        avg_train_loss = train_loss / max(1, train_batches)
        
        # Validation
        avg_val_loss = None
        if val_loader is not None and len(val_dataset) > 0:
            model.eval()
            val_loss = 0.0
            val_batches = 0
            with torch.no_grad():
                for batch in val_loader:
                    src = batch["src"].to(device)
                    src_mask = batch["src_mask"].to(device)
                    tgt = batch["tgt"].to(device)
                    
                    logits = model(src, src_mask, tgt, teacher_forcing_ratio=0.0)
                    targets = tgt[:, 1:].contiguous().view(-1)
                    logits_flat = logits.contiguous().view(-1, vocab_size)
                    loss = criterion(logits_flat, targets)
                    
                    val_loss += loss.item()
                    val_batches += 1
            avg_val_loss = val_loss / max(1, val_batches)
            
        epoch_time = time.time() - t0_epoch
        val_str = f"{avg_val_loss:.4f}" if avg_val_loss is not None else "N/A"
        msg = f"Epoch [{epoch:02d}/{epochs:02d}] ({epoch_time:.1f}s) | Train Loss: {avg_train_loss:.4f} | Val Loss: {val_str}"
        log(msg, log_file)
        
        record = {
            "epoch": epoch,
            "train_loss": round(avg_train_loss, 4),
            "val_loss": round(avg_val_loss, 4) if avg_val_loss is not None else None,
            "tf_ratio": round(tf_ratio, 2),
            "epoch_time_sec": round(epoch_time, 2)
        }
        history.append(record)
        
        # Checkpoint selection
        if avg_val_loss is not None:
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
                torch.save(model.state_dict(), best_model_path)
                log(f"  -> Best model checkpoint saved to {best_model_path.name} (Val Loss: {best_val_loss:.4f})", log_file)
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    log(f"Early stopping triggered at epoch {epoch}.", log_file)
                    break
        else:
            torch.save(model.state_dict(), best_model_path)
            
    total_train_time = time.time() - t0_train
    log(f"\nTraining finished in {total_train_time:.1f}s. Best Val Loss: {best_val_loss:.4f}", log_file)
    
    curves_path = exp_dir / "training_curves.json"
    with open(curves_path, "w", encoding="utf-8") as f:
        json.dump({
            "history": history,
            "best_val_loss": round(best_val_loss, 4) if best_val_loss != float("inf") else None,
            "total_time_seconds": round(total_train_time, 2),
            "trainable_parameters": total_params
        }, f, indent=2)
    log(f"Saved training curves to {curves_path.name}", log_file)

if __name__ == "__main__":
    train_attention_model()
