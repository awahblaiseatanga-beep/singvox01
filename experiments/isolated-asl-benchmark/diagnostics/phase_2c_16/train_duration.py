import sys, os, time, torch
import torch.nn as nn
import torch.optim as optim
from collections import defaultdict, Counter
import json

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders

def evaluate_split(model, dataloader, criterion, device):
    model.eval()
    all_preds, all_labels = [], []
    total_loss = 0.0
    
    with torch.no_grad():
        for b in dataloader:
            seqs = b["padded_sequences"].to(device)
            mask = b["attention_mask"].to(device)
            labels = b["class_indices"].to(device)
            
            preds = model(seqs, attention_mask=mask)
            loss = criterion(preds, labels)
            total_loss += loss.item() * seqs.size(0)
            
            _, p = torch.max(preds, 1)
            all_preds.extend(p.tolist())
            all_labels.extend(labels.tolist())
            
    # Compute metrics exactly like train_isolated.py calc_f1 (Macro-F1 without sklearn)
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    
    for p, l in zip(all_preds, all_labels):
        if p == l:
            tp[l] += 1
        else:
            fp[p] += 1
            fn[l] += 1
            
    f1s = []
    for c in range(79):
        if tp[c] + fp[c] + fn[c] == 0: continue
        precision = tp[c] / (tp[c] + fp[c]) if (tp[c] + fp[c]) > 0 else 0
        recall = tp[c] / (tp[c] + fn[c]) if (tp[c] + fn[c]) > 0 else 0
        if precision + recall > 0:
            f1s.append(2 * (precision * recall) / (precision + recall))
        else:
            f1s.append(0.0)
            
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0
    
    correct = sum(1 for p, l in zip(all_preds, all_labels) if p == l)
    acc = correct / len(all_labels) * 100
    avg_loss = total_loss / len(all_labels)
    unique_classes = len(set(all_preds))
    
    # top 3 predictions
    freq = Counter(all_preds).most_common(3)
    
    return avg_loss, acc, macro_f1, unique_classes, freq

def main():
    print("SPOTER TRAINING DURATION DIAGNOSTIC (PHASE 2C.16)")
    # Set seed for reproducibility
    torch.manual_seed(42)
    device = torch.device("cpu")
    
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    train_loader, val_loader, _ = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    print(f"Train samples: {len(train_loader.dataset)} | Val samples: {len(val_loader.dataset)}")
    
    # Exact original configuration from train_isolated.py
    model = Spoter(num_classes=79, hidden_dim=64, nhead=4, num_encoder_layers=2, num_decoder_layers=2, dim_feedforward=256, dropout=0.1).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-4)
    
    epochs = 50
    record_epochs = {1, 2, 5, 10, 20, 50}
    history = []
    
    start_time = time.time()
    for float_epoch in range(1, epochs + 1):
        model.train()
        grad_norm = 0.0
        
        for batch in train_loader:
            seqs, mask, labels = batch["padded_sequences"].to(device), batch["attention_mask"].to(device), batch["class_indices"].to(device)
            optimizer.zero_grad()
            preds = model(seqs, attention_mask=mask)
            loss = criterion(preds, labels)
            loss.backward()
            
            # Record last batch grad_norm
            gn = 0.0
            for p in model.parameters():
                if p.grad is not None:
                    gn += p.grad.data.norm(2).item() ** 2
            grad_norm = gn ** 0.5
            
            optimizer.step()
            
        if float_epoch in record_epochs:
            tr_loss, tr_acc, tr_f1, tr_uniq, tr_freq = evaluate_split(model, train_loader, criterion, device)
            vl_loss, vl_acc, vl_f1, vl_uniq, vl_freq = evaluate_split(model, val_loader, criterion, device)
            
            record = {
                "epoch": float_epoch,
                "train_loss": tr_loss, "train_acc": tr_acc, "train_f1": tr_f1, "train_uniq": tr_uniq, "train_freq": tr_freq,
                "val_loss": vl_loss, "val_acc": vl_acc, "val_f1": vl_f1, "val_uniq": vl_uniq, "val_freq": vl_freq,
                "grad_norm": grad_norm
            }
            history.append(record)
            print(f"\n--- Epoch {float_epoch} ---")
            print(f"Train -> Loss: {tr_loss:.4f} | Acc: {tr_acc:.2f}% | F1: {tr_f1:.4f} | Uniq: {tr_uniq} | Tops: {tr_freq}")
            print(f"Val   -> Loss: {vl_loss:.4f} | Acc: {vl_acc:.2f}% | F1: {vl_f1:.4f} | Uniq: {vl_uniq} | Tops: {vl_freq}")
            print(f"Gradient Norm: {grad_norm:.6f}")

    total_time = time.time() - start_time
    print(f"\nTraining completed in {total_time:.2f}s")
    
    ckpt_path = r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\diagnostics\phase_2c_16\duration_checkpoint_ep50.pt"
    torch.save(model.state_dict(), ckpt_path)
    print(f"Artifact saved: {ckpt_path}")

    # Output machine-readable JSON
    json_path = r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\diagnostics\phase_2c_16\duration_history.json"
    with open(json_path, 'w') as f:
        json.dump(history, f, indent=2)

if __name__ == "__main__":
    main()
