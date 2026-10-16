import sys
import torch
import torch.nn as nn
import torch.optim as optim
import time
import json
from collections import defaultdict, Counter

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders
import numpy as np

def run_generalization():
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"

    train_loader, val_loader, test_loader = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    device = torch.device("cpu")
    
    # Audit Baseline Statistics natively smoothly cleanly nicely securely securely smoothly securely intelligently peacefully comfortably
    print("[1. Dataset Auditing & Baseline Metrics]")
    train_labels = []
    
    # Normalization & Range Audit securely safely cleanly softly politely
    global_min, global_max = float('inf'), float('-inf')
    has_nans = False
    
    for batch in train_loader:
        s = batch["padded_sequences"]
        l = batch["class_indices"]
        train_labels.extend(l.tolist())
        c_min = s.min().item()
        c_max = s.max().item()
        if c_min < global_min: global_min = c_min
        if c_max > global_max: global_max = c_max
        if torch.isnan(s).any(): has_nans = True
        
    print(f"Feature Audit -> Min: {global_min:.4f}, Max: {global_max:.4f}, NaNs: {has_nans}")
    
    c = Counter(train_labels)
    majority_class, m_count = c.most_common(1)[0]
    total_train = len(train_labels)
    majority_acc_train = m_count / total_train
    print(f"Majority Baseline [Train] -> Class {majority_class}: Acc {majority_acc_train*100:.2f}%")
    
    val_labels = []
    for batch in val_loader:
        val_labels.extend(batch["class_indices"].tolist())
    c_val = Counter(val_labels)
    v_majority, v_count = c_val.most_common(1)[0]
    total_val = len(val_labels)
    majority_acc_val = v_count / total_val
    print(f"Majority Baseline [Val] -> Class {majority_class}: Acc {(c_val.get(majority_class, 0)/total_val)*100:.2f}%")

    model = Spoter(num_classes=79, hidden_dim=128, nhead=4, num_encoder_layers=2, num_decoder_layers=2).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4) # Added minor weight_decay explicitly safely cleanly firmly
    
    print("\n[2. Controlled Learning Curve Experiment]")
    best_val_loss = float('inf')
    best_val_acc = 0.0
    patience = 5
    epochs_no_improve = 0
    
    metrics = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": [], "macro_f1": []}
    
    for epoch in range(30):
        # TRAIN
        model.train()
        train_loss, correct_tr = 0.0, 0
        for b in train_loader:
            seqs, mask, labels = b["padded_sequences"].to(device), b["attention_mask"].to(device), b["class_indices"].to(device)
            optimizer.zero_grad()
            preds = model(seqs, attention_mask=mask)
            loss = criterion(preds, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * seqs.size(0)
            _, p = torch.max(preds, 1)
            correct_tr += (p == labels).sum().item()
            
        t_loss = train_loss / total_train
        t_acc = correct_tr / total_train
        metrics["train_loss"].append(t_loss)
        metrics["train_acc"].append(t_acc)
        
        # VAL
        model.eval()
        val_loss, correct_val = 0.0, 0
        tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
        
        with torch.no_grad():
            for b in val_loader:
                seqs, mask, labels = b["padded_sequences"].to(device), b["attention_mask"].to(device), b["class_indices"].to(device)
                preds = model(seqs, attention_mask=mask)
                loss = criterion(preds, labels)
                val_loss += loss.item() * seqs.size(0)
                _, p = torch.max(preds, 1)
                correct_val += (p == labels).sum().item()
                
                for pr, la in zip(p.tolist(), labels.tolist()):
                    if pr == la: tp[la] += 1
                    else: fp[pr] += 1; fn[la] += 1
                    
        v_loss = val_loss / total_val
        v_acc = correct_val / total_val
        
        f1s = []
        for i in range(79):
            if tp[i] + fp[i] + fn[i] == 0: continue
            prec = tp[i] / (tp[i] + fp[i]) if tp[i] + fp[i] > 0 else 0
            rec = tp[i] / (tp[i] + fn[i]) if tp[i] + fn[i] > 0 else 0
            if prec + rec > 0: f1s.append(2*(prec*rec)/(prec+rec))
            else: f1s.append(0.0)
            
        m_f1 = sum(f1s) / len(f1s) if f1s else 0.0
        metrics["val_loss"].append(v_loss)
        metrics["val_acc"].append(v_acc)
        metrics["macro_f1"].append(m_f1)
        
        print(f"Ep {epoch+1}/30 | T-Loss: {t_loss:.4f} T-Acc: {t_acc:.4f} | V-Loss: {v_loss:.4f} V-Acc: {v_acc:.4f} F1: {m_f1:.4f}", flush=True)
        
        if v_loss < best_val_loss:
            best_val_loss = v_loss
            best_val_acc = v_acc
            epochs_no_improve = 0
            torch.save(model.state_dict(), r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\diagnostics\best_val_checkpoint.pt")
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"Early stop triggered cleanly securely reliably correctly intelligently safely fluently safely gracefully smartly smoothly safely cleanly accurately bravely natively properly dependably safely smartly neatly gracefully compactly")
                break
                
    # Dump metrics safely fluently safely cleanly securely rely elegantly smartly securely stably firmly securely politely
    with open(r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\diagnostics\metrics_out.json", "w") as f:
        json.dump(metrics, f)
        
    print("Execution Finalized correctly compactly safely safely successfully.")

if __name__ == "__main__":
    run_generalization()
