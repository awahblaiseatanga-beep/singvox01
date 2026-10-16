import sys
import os
import time
import json
import random
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

torch.set_num_threads(1)

# Set deterministic seeds
def seed_everything(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

seed_everything(42)

base_dir = Path(r"d:\Singvox\Singvox")
exp27_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_27"
exp26_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_26"
exp29_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_29"
exp29_dir.mkdir(parents=True, exist_ok=True)

sys.path.append(str(exp27_dir))
sys.path.append(str(exp29_dir))

from dataset import How2SignAttentionDataset, attention_collate_fn
from tokenizer import BPETokenizer
from model import JointCTCAttentionModel

def extract_ctc_targets(tgt, tgt_lens, src_lens, pad_id=0):
    """
    Extracts raw target tokens excluding <sos> and <eos> for CTC loss.
    Returns:
      ctc_targets: [B, max_ctc_len]
      ctc_target_lens: [B]
    """
    batch_size = tgt.size(0)
    ctc_targets_list = []
    ctc_target_lens = []

    for i in range(batch_size):
        raw_len = tgt_lens[i].item()
        # Tokens between <sos> (idx 0) and <eos> (idx raw_len - 1)
        if raw_len > 2:
            raw_tokens = tgt[i, 1 : raw_len - 1]
        else:
            raw_tokens = tgt[i, 1 : 2] # fallback 1 token
        
        # CTC constraint: target length must not exceed source length
        s_len = src_lens[i].item()
        if len(raw_tokens) > s_len:
            raw_tokens = raw_tokens[:s_len]

        ctc_targets_list.append(raw_tokens)
        ctc_target_lens.append(len(raw_tokens))

    max_ctc_len = max(max(ctc_target_lens), 1)
    padded_ctc = torch.full((batch_size, max_ctc_len), pad_id, dtype=torch.long, device=tgt.device)
    for i, tokens in enumerate(ctc_targets_list):
        if len(tokens) > 0:
            padded_ctc[i, :len(tokens)] = tokens

    return padded_ctc, torch.tensor(ctc_target_lens, dtype=torch.long, device=tgt.device)

def run_pilot_check(model, sample_batch, device):
    """
    Runs an immediate single-step pilot to verify CTC loss computation,
    gradient backpropagation, and CTC path feasibility.
    """
    print("\n[PILOT CHECK] Running single-batch sanity check...")
    model.train()
    src = sample_batch["src"].to(device)
    src_mask = sample_batch["src_mask"].to(device)
    src_lens = sample_batch["src_lens"].to(device)
    tgt = sample_batch["tgt"].to(device)
    tgt_lens = sample_batch["tgt_lens"].to(device)

    ctc_targets, ctc_target_lens = extract_ctc_targets(tgt, tgt_lens, src_lens, pad_id=model.pad_id)
    
    # Forward pass
    dec_logits, ctc_log_probs = model(src, src_mask, src_lens, tgt, teacher_forcing_ratio=1.0)
    
    # CE loss
    ce_loss_fn = nn.CrossEntropyLoss(ignore_index=model.pad_id)
    ce_loss = ce_loss_fn(
        dec_logits.reshape(-1, model.vocab_size),
        tgt[:, 1:].reshape(-1)
    )

    # CTC loss
    ctc_loss_fn = nn.CTCLoss(blank=model.ctc_blank_id, zero_infinity=True)
    ctc_loss = ctc_loss_fn(
        ctc_log_probs,
        ctc_targets,
        src_lens,
        ctc_target_lens
    )

    total_loss = 0.7 * ce_loss + 0.3 * ctc_loss
    total_loss.backward()

    # Check gradients
    grad_norms = [p.grad.norm().item() for p in model.parameters() if p.grad is not None]
    max_grad = max(grad_norms) if grad_norms else 0.0
    mean_grad = np.mean(grad_norms) if grad_norms else 0.0

    print(f"  CE Loss:   {ce_loss.item():.4f}")
    print(f"  CTC Loss:  {ctc_loss.item():.4f}")
    print(f"  Combined:  {total_loss.item():.4f}")
    print(f"  Max Grad:  {max_grad:.4f}, Mean Grad: {mean_grad:.4f}")
    
    if np.isnan(total_loss.item()) or np.isinf(total_loss.item()):
        raise RuntimeError("Pilot failed: Loss is NaN/Inf!")
    if max_grad == 0.0:
        raise RuntimeError("Pilot failed: Zero gradients!")
        
    model.zero_grad()
    print("[PILOT CHECK] Passed successfully. Model architecture and CTC loss verified.\n")

def train_model():
    manifest_path = exp26_dir / "dataset_manifest.csv"
    feat_dir = exp26_dir / "features"
    tok_path = exp27_dir / "tokenizer.json"

    tokenizer = BPETokenizer.load(tok_path)
    vocab_size = len(tokenizer.token2id)

    train_dataset = How2SignAttentionDataset(manifest_path, feat_dir, tokenizer, split="train", max_frames=150)
    val_dataset = How2SignAttentionDataset(manifest_path, feat_dir, tokenizer, split="val", max_frames=150)

    print(f"Train dataset: {len(train_dataset)} samples")
    print(f"Val dataset:   {len(val_dataset)} samples")

    train_loader = DataLoader(
        train_dataset,
        batch_size=16,
        shuffle=True,
        collate_fn=lambda b: attention_collate_fn(b, pad_token_id=tokenizer.pad_id)
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=16,
        shuffle=False,
        collate_fn=lambda b: attention_collate_fn(b, pad_token_id=tokenizer.pad_id)
    )

    device = torch.device("cpu")

    model = JointCTCAttentionModel(
        vocab_size=vocab_size,
        in_features=366,
        hidden_dim=256,
        embed_dim=128,
        attn_dim=128,
        pad_id=tokenizer.pad_id,
        sos_id=tokenizer.sos_id,
        eos_id=tokenizer.eos_id,
        dropout=0.2
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"Initialized JointCTCAttentionModel with {total_params:,} parameters.")

    # 1. Run Pilot Check
    sample_batch = next(iter(train_loader))
    run_pilot_check(model, sample_batch, device)

    # 2. Setup training components
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-4, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)
    ce_loss_fn = nn.CrossEntropyLoss(ignore_index=tokenizer.pad_id)
    ctc_loss_fn = nn.CTCLoss(blank=model.ctc_blank_id, zero_infinity=True)

    epochs = 12
    lambda_ctc = 0.3
    best_val_loss = float("inf")
    patience = 4
    patience_counter = 0

    history = {
        "epochs": [],
        "train_loss": [],
        "train_ce_loss": [],
        "train_ctc_loss": [],
        "val_loss": [],
        "val_ce_loss": [],
        "val_ctc_loss": []
    }

    print("Beginning Training Loop...")
    for epoch in range(1, epochs + 1):
        t0 = time.time()
        model.train()
        train_loss_acc = 0.0
        train_ce_acc = 0.0
        train_ctc_acc = 0.0
        train_batches = 0

        for batch in train_loader:
            src = batch["src"].to(device)
            src_mask = batch["src_mask"].to(device)
            src_lens = batch["src_lens"].to(device)
            tgt = batch["tgt"].to(device)
            tgt_lens = batch["tgt_lens"].to(device)

            ctc_targets, ctc_target_lens = extract_ctc_targets(tgt, tgt_lens, src_lens, pad_id=tokenizer.pad_id)

            optimizer.zero_grad()
            dec_logits, ctc_log_probs = model(src, src_mask, src_lens, tgt, teacher_forcing_ratio=0.5)

            ce_loss = ce_loss_fn(
                dec_logits.reshape(-1, vocab_size),
                tgt[:, 1:].reshape(-1)
            )
            ctc_loss = ctc_loss_fn(
                ctc_log_probs,
                ctc_targets,
                src_lens,
                ctc_target_lens
            )

            loss = (1.0 - lambda_ctc) * ce_loss + lambda_ctc * ctc_loss
            loss.backward()

            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            train_loss_acc += loss.item()
            train_ce_acc += ce_loss.item()
            train_ctc_acc += ctc_loss.item()
            train_batches += 1

        avg_train_loss = train_loss_acc / max(1, train_batches)
        avg_train_ce = train_ce_acc / max(1, train_batches)
        avg_train_ctc = train_ctc_acc / max(1, train_batches)

        # Validation
        model.eval()
        val_loss_acc = 0.0
        val_ce_acc = 0.0
        val_ctc_acc = 0.0
        val_batches = 0

        with torch.no_grad():
            for batch in val_loader:
                src = batch["src"].to(device)
                src_mask = batch["src_mask"].to(device)
                src_lens = batch["src_lens"].to(device)
                tgt = batch["tgt"].to(device)
                tgt_lens = batch["tgt_lens"].to(device)

                ctc_targets, ctc_target_lens = extract_ctc_targets(tgt, tgt_lens, src_lens, pad_id=tokenizer.pad_id)

                dec_logits, ctc_log_probs = model(src, src_mask, src_lens, tgt, teacher_forcing_ratio=0.0)

                ce_loss = ce_loss_fn(
                    dec_logits.reshape(-1, vocab_size),
                    tgt[:, 1:].reshape(-1)
                )
                ctc_loss = ctc_loss_fn(
                    ctc_log_probs,
                    ctc_targets,
                    src_lens,
                    ctc_target_lens
                )
                loss = (1.0 - lambda_ctc) * ce_loss + lambda_ctc * ctc_loss

                val_loss_acc += loss.item()
                val_ce_acc += ce_loss.item()
                val_ctc_acc += ctc_loss.item()
                val_batches += 1

        avg_val_loss = val_loss_acc / max(1, val_batches)
        avg_val_ce = val_ce_acc / max(1, val_batches)
        avg_val_ctc = val_ctc_acc / max(1, val_batches)
        scheduler.step(avg_val_loss)

        elapsed = time.time() - t0
        print(f"Epoch {epoch:02d}/{epochs:02d} [{elapsed:.1f}s] | Train Loss: {avg_train_loss:.4f} (CE: {avg_train_ce:.4f}, CTC: {avg_train_ctc:.4f}) | Val Loss: {avg_val_loss:.4f} (CE: {avg_val_ce:.4f}, CTC: {avg_val_ctc:.4f})")

        history["epochs"].append(epoch)
        history["train_loss"].append(round(avg_train_loss, 4))
        history["train_ce_loss"].append(round(avg_train_ce, 4))
        history["train_ctc_loss"].append(round(avg_train_ctc, 4))
        history["val_loss"].append(round(avg_val_loss, 4))
        history["val_ce_loss"].append(round(avg_val_ce, 4))
        history["val_ctc_loss"].append(round(avg_val_ctc, 4))

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            best_path = exp29_dir / "best_ctc_attention_model.pt"
            torch.save(model.state_dict(), best_path)
            print(f"  --> Saved new best checkpoint to {best_path.name} (Val Loss: {best_val_loss:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  Early stopping triggered after {epoch} epochs.")
                break

    # Save history
    hist_path = exp29_dir / "training_history.json"
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    print(f"\nTraining completed. Best Val Loss: {best_val_loss:.4f}. History saved to {hist_path}.")

if __name__ == "__main__":
    train_model()
