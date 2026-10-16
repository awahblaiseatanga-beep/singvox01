"""
SignVox SPOTER V3 Official Training Pipeline
Vocabulary: 100 Canonical Classes (ASL-100 specification)
Architecture: SpoterV3 (Transformer Encoder-Decoder with Learnable Class Query)
Inputs: 366-D Normalized Feature Sequences
Outputs: 100-D Logits
Isolation: Strictly isolated under experiments/spoter_v3/
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

# Add relative modules
SCRIPT_DIR = Path(__file__).resolve().parent
EXP_DIR = SCRIPT_DIR.parent
ROOT_DIR = EXP_DIR.parent.parent

sys.path.append(str(EXP_DIR / "models"))
sys.path.append(str(SCRIPT_DIR))

from spoter_v3 import SpoterV3
from dataloaders_v3 import (
    set_seed,
    get_spoter_v3_dataloaders,
    compute_groupnorm_scalars,
    apply_groupnorm_scaling
)

def parse_args():
    parser = argparse.ArgumentParser(description="SignVox SPOTER V3 Training Script")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--weight_decay", type=float, default=1e-4, help="Weight decay")
    parser.add_argument("--hidden_dim", type=int, default=512, help="Transformer hidden dimension")
    parser.add_argument("--num_encoder_layers", type=int, default=6, help="Number of encoder layers")
    parser.add_argument("--num_decoder_layers", type=int, default=6, help="Number of decoder layers")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--manifest_path", type=str, default=str(EXP_DIR / "manifests" / "spoter_v3_matched_manifest.csv"))
    parser.add_argument("--features_dir", type=str, default=str(ROOT_DIR / "ai" / "sign-recognition" / "data" / "dataset_extracted"))
    parser.add_argument("--mapping_path", type=str, default=str(EXP_DIR / "config" / "asl100_v3_class_mapping.json"))
    parser.add_argument("--output_dir", type=str, default=str(EXP_DIR / "checkpoints"))
    parser.add_argument("--logs_dir", type=str, default=str(EXP_DIR / "logs"))
    parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint to resume from")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--early_stopping_patience", type=int, default=10, help="Stop if val loss doesn't improve for N epochs (0=disabled)")
    parser.add_argument("--recompute_scalars", action="store_true", help="Force re-computation of normalization scalars even if saved file exists")
    return parser.parse_args()

def compute_per_class_metrics(all_preds: list, all_labels: list, num_classes: int = 100):
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for p, l in zip(all_preds, all_labels):
        cm[l, p] += 1
        
    per_class_acc = np.zeros(num_classes)
    class_support = np.zeros(num_classes)
    for i in range(num_classes):
        support = cm[i, :].sum()
        class_support[i] = support
        if support > 0:
            per_class_acc[i] = cm[i, i] / support
            
    active_mask = class_support > 0
    macro_acc = np.mean(per_class_acc[active_mask]) if active_mask.any() else 0.0
    top1_overall = (np.array(all_preds) == np.array(all_labels)).mean() if len(all_preds) > 0 else 0.0
    return cm, per_class_acc, class_support, macro_acc, top1_overall

def train_epoch(model, loader, optimizer, criterion, scalars, device):
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    
    for batch in loader:
        seqs = batch["padded_sequences"].to(device)
        mask = batch["attention_mask"].to(device)
        targets = batch["class_indices"].to(device)
        
        # Apply landmark coordinate normalization
        scaled_seqs = apply_groupnorm_scaling(seqs, scalars).to(device)
        
        optimizer.zero_grad()
        logits = model(scaled_seqs, attention_mask=mask)
        loss = criterion(logits, targets)
        loss.backward()
        
        # Gradient clipping for transformer stability
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        total_loss += loss.item() * targets.size(0)
        preds = logits.argmax(dim=-1)
        correct += (preds == targets).sum().item()
        total += targets.size(0)
        
    return total_loss / max(total, 1), correct / max(total, 1)

def evaluate(model, loader, criterion, scalars, device, num_classes=100):
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_labels = []
    all_top3_correct = 0
    total = 0
    
    with torch.no_grad():
        for batch in loader:
            seqs = batch["padded_sequences"].to(device)
            mask = batch["attention_mask"].to(device)
            targets = batch["class_indices"].to(device)
            
            scaled_seqs = apply_groupnorm_scaling(seqs, scalars).to(device)
            logits = model(scaled_seqs, attention_mask=mask)
            loss = criterion(logits, targets)
            
            total_loss += loss.item() * targets.size(0)
            preds = logits.argmax(dim=-1)
            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(targets.cpu().tolist())
            
            # Top-3 accuracy
            top3 = torch.topk(logits, k=min(3, num_classes), dim=-1).indices
            targets_exp = targets.unsqueeze(-1).expand_as(top3)
            all_top3_correct += (top3 == targets_exp).any(dim=-1).sum().item()
            total += targets.size(0)
            
    cm, per_class_acc, class_support, macro_acc, top1 = compute_per_class_metrics(
        all_preds, all_labels, num_classes=num_classes
    )
    top3_acc = all_top3_correct / max(total, 1)
    avg_loss = total_loss / max(total, 1)
    
    return avg_loss, top1, top3_acc, macro_acc, cm, per_class_acc, class_support

def main():
    args = parse_args()
    set_seed(args.seed)
    
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.logs_dir, exist_ok=True)
    
    print("=" * 70)
    print("SignVox SPOTER V3 100-Class Official Training Pipeline")
    print(f"Device: {args.device} | Seed: {args.seed} | Epochs: {args.epochs} | Batch Size: {args.batch_size}")
    print(f"Manifest: {args.manifest_path}")
    print(f"Features: {args.features_dir}")
    print(f"Mapping: {args.mapping_path}")
    print("=" * 70)
    
    # 1. Load Data
    train_loader, val_loader, test_loader = get_spoter_v3_dataloaders(
        args.manifest_path,
        args.features_dir,
        args.mapping_path,
        batch_size=args.batch_size
    )
    print(f"Loaded datasets: Train={len(train_loader.dataset)}, Val={len(val_loader.dataset)}, Test={len(test_loader.dataset)}")
    
    # 2. Compute Normalization Scalars
    scalars_path = Path(args.output_dir) / "spoter_v3_groupnorm_scalars.json"
    if scalars_path.exists() and not args.recompute_scalars:
        with open(scalars_path, "r", encoding="utf-8") as sf:
            scalars = json.load(sf)
        print(f"Loaded existing scalars from {scalars_path}: {scalars}")
    else:
        if args.recompute_scalars:
            print("Forcing re-computation of normalization scalars (--recompute_scalars set)...")
        else:
            print("Computing training normalization scalars...")
        scalars = compute_groupnorm_scalars(train_loader)
        with open(scalars_path, "w", encoding="utf-8") as sf:
            json.dump(scalars, sf, indent=2)
        print(f"Computed and saved scalars to {scalars_path}: {scalars}")
        
    # 3. Initialize Model
    model = SpoterV3(
        num_classes=100,
        input_dim=366,
        hidden_dim=args.hidden_dim,
        num_encoder_layers=args.num_encoder_layers,
        num_decoder_layers=args.num_decoder_layers
    ).to(args.device)
    
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)
    
    start_epoch = 0
    best_val_loss = float("inf")
    best_val_acc = 0.0
    early_stop_counter = 0
    
    # 4. Checkpoint Resumption
    if args.resume:
        print(f"Resuming training from checkpoint: {args.resume}")
        checkpoint = torch.load(args.resume, map_location=args.device, weights_only=False)
        model.load_state_dict(checkpoint["model_state_dict"])
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        start_epoch = checkpoint["epoch"] + 1
        best_val_loss = checkpoint.get("best_val_loss", float("inf"))
        best_val_acc = checkpoint.get("best_val_acc", 0.0)
        print(f"Resumed from epoch {start_epoch} (Best Val Acc: {best_val_acc:.4f})")
        
    training_log = []
    
    # 5. Training Loop
    for epoch in range(start_epoch, args.epochs):
        t0 = time.time()
        train_loss, train_acc = train_epoch(
            model, train_loader, optimizer, criterion, scalars, args.device
        )
        val_loss, val_top1, val_top3, val_macro, cm, per_class_acc, support = evaluate(
            model, val_loader, criterion, scalars, args.device, num_classes=100
        )
        scheduler.step()
        epoch_time = time.time() - t0
        
        log_entry = {
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "train_acc": round(train_acc, 4),
            "val_loss": round(val_loss, 4),
            "val_top1": round(val_top1, 4),
            "val_top3": round(val_top3, 4),
            "val_macro": round(val_macro, 4),
            "lr": optimizer.param_groups[0]["lr"],
            "time_sec": round(epoch_time, 2)
        }
        training_log.append(log_entry)
        
        print(f"Epoch {epoch+1:03d}/{args.epochs:03d} [{epoch_time:.1f}s] | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc*100:.2f}% | "
              f"Val Loss: {val_loss:.4f} Top-1: {val_top1*100:.2f}% Top-3: {val_top3*100:.2f}% Macro: {val_macro*100:.2f}%")
              
        # Save latest checkpoint
        latest_cp = {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "scalars": scalars,
            "val_loss": val_loss,
            "val_acc": val_top1,
            "best_val_loss": best_val_loss,
            "best_val_acc": best_val_acc,
            "config": vars(args)
        }
        torch.save(latest_cp, os.path.join(args.output_dir, "spoter_v3_latest_checkpoint.pt"))
        
        # Save best validation loss checkpoint
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            latest_cp["best_val_loss"] = best_val_loss
            torch.save(latest_cp, os.path.join(args.output_dir, "spoter_v3_best_val_loss_checkpoint.pt"))
            print(f"  --> Saved new best val loss checkpoint ({val_loss:.4f})")
            
        # Save best validation accuracy checkpoint
        if val_top1 > best_val_acc:
            best_val_acc = val_top1
            latest_cp["best_val_acc"] = best_val_acc
            torch.save(latest_cp, os.path.join(args.output_dir, "spoter_v3_best_val_acc_checkpoint.pt"))
            print(f"  --> Saved new best val acc checkpoint ({val_top1*100:.2f}%)")

        # Early stopping on validation loss
        if args.early_stopping_patience > 0:
            if val_loss < best_val_loss:
                early_stop_counter = 0
            else:
                early_stop_counter += 1
                print(f"  [Early Stop] No improvement for {early_stop_counter}/{args.early_stopping_patience} epochs.")
                if early_stop_counter >= args.early_stopping_patience:
                    print(f"  [Early Stop] Patience exhausted at epoch {epoch+1}. Stopping training.")
                    with open(os.path.join(args.logs_dir, "training_history.json"), "w", encoding="utf-8") as lf:
                        json.dump(training_log, lf, indent=2)
                    break

        # Write periodic log
        with open(os.path.join(args.logs_dir, "training_history.json"), "w", encoding="utf-8") as lf:
            json.dump(training_log, lf, indent=2)
            
    print("\n--- Training Completed Successfully ---")
    print(f"Best Validation Accuracy: {best_val_acc*100:.2f}%")
    print(f"Best Validation Loss: {best_val_loss:.4f}")

if __name__ == "__main__":
    main()
