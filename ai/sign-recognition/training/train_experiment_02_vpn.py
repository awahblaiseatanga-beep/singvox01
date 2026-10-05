import sys
import os
import time
import json
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders

def get_xyz_indices():
    lh_idx = list(range(0, 63))
    rh_idx = list(range(63, 126))
    pose_xyz_idx = [126 + i*5 + j for i in range(33) for j in range(3)]
    face_idx = list(range(291, 366))
    return lh_idx, rh_idx, pose_xyz_idx, face_idx

def apply_vpn_scaling(seqs):
    # FIXED V2 PRE-COMPUTED SCALARS
    scalars = {
        "left_hand": 0.3887,
        "right_hand": 0.3666,
        "pose_xyz": 1.8127,
        "face": 0.3139
    }
    
    lh_idx, rh_idx, pose_xyz_idx, face_idx = get_xyz_indices()
    scaled_seqs = seqs.clone().float()
    
    # 1. Nullify Pose Visibility/Presence [225:291]
    scaled_seqs[:, :, 225:291] = 0.0
    
    # 2. V2 Standard Spatial Normalized Operations Unchanged
    scaled_seqs[:, :, lh_idx] = scaled_seqs[:, :, lh_idx] / scalars["left_hand"]
    scaled_seqs[:, :, rh_idx] = scaled_seqs[:, :, rh_idx] / scalars["right_hand"]
    scaled_seqs[:, :, pose_xyz_idx] = scaled_seqs[:, :, pose_xyz_idx] / scalars["pose_xyz"]
    scaled_seqs[:, :, face_idx] = scaled_seqs[:, :, face_idx] / scalars["face"]
    
    return scaled_seqs

def compute_accuracy(preds, labels):
    _, predicted = torch.max(preds, 1)
    correct = (predicted == labels).sum().item()
    return correct / labels.size(0)

def compute_per_class_metrics(all_preds, all_labels, num_classes=79):
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for p, l in zip(all_preds, all_labels):
        cm[l, p] += 1
    per_class_acc = np.zeros(num_classes)
    class_support = np.zeros(num_classes)
    for i in range(num_classes):
        support = cm[i, :].sum()
        class_support[i] = support
        if support > 0: per_class_acc[i] = cm[i, i] / support
    macro_acc = np.mean(per_class_acc[class_support > 0])
    return cm, per_class_acc, class_support, macro_acc

def main():
    print("SPOTER EXPERIMENT 02 (V2-VPN) TRAINING — STARTED")
    
    # EXACT REPRODUCIBILITY SEED
    torch.manual_seed(42)
    np.random.seed(42)
    
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    train_loader, val_loader, test_loader = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    
    # 100% Assurance that Test is untouched natively
    del test_loader
    print("Test loader explicitly destroyed avoiding test bleed automatically.")
    
    device = torch.device("cpu")
    model = Spoter(num_classes=79, hidden_dim=512, nhead=8, num_encoder_layers=6, num_decoder_layers=6, dim_feedforward=2048, dropout=0.1).to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-4)
    max_epochs = 100
    
    best_val_loss = float('inf')
    best_val_loss_epoch = -1
    best_val_acc = -1.0
    best_val_acc_epoch = -1
    
    checkpoint_dir = r"d:\Singvox\Singvox\ai\sign-recognition\checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    latest_ckpt = os.path.join(checkpoint_dir, "spoter_exp02_vpn_latest.pt")
    best_loss_ckpt = os.path.join(checkpoint_dir, "spoter_exp02_vpn_best_val_loss.pt")
    best_acc_ckpt = os.path.join(checkpoint_dir, "spoter_exp02_vpn_best_val_acc.pt")
    
    history = []
    total_start_time = time.time()
    
    final_cm, final_per_class_acc, final_class_support, final_macro_acc = None, None, None, None
    final_preds, final_labels = None, None
    
    for epoch in range(1, max_epochs + 1):
        model.train()
        train_loss, train_acc = 0.0, 0.0
        epoch_start = time.time()
        
        for batch in train_loader:
            seqs = apply_vpn_scaling(batch["padded_sequences"]).to(device)
            mask = batch["attention_mask"].to(device)
            labels = batch["class_indices"].to(device)
            
            optimizer.zero_grad()
            preds = model(seqs, attention_mask=mask)
            loss = criterion(preds, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * seqs.size(0)
            train_acc += compute_accuracy(preds, labels) * seqs.size(0)
            
        train_loss /= len(train_loader.dataset)
        train_acc /= len(train_loader.dataset)
        
        model.eval()
        val_loss, val_acc = 0.0, 0.0
        all_preds, all_labels = [], []
        
        with torch.no_grad():
            for batch in val_loader:
                seqs = apply_vpn_scaling(batch["padded_sequences"]).to(device)
                mask = batch["attention_mask"].to(device)
                labels = batch["class_indices"].to(device)
                
                preds = model(seqs, attention_mask=mask)
                loss = criterion(preds, labels)
                
                val_loss += loss.item() * seqs.size(0)
                val_acc += compute_accuracy(preds, labels) * seqs.size(0)
                
                _, predicted = torch.max(preds, 1)
                all_preds.extend(predicted.cpu().tolist())
                all_labels.extend(labels.cpu().tolist())
                
        val_loss /= len(val_loader.dataset)
        val_acc /= len(val_loader.dataset)
        
        cm, per_class_acc, class_support, macro_acc = compute_per_class_metrics(all_preds, all_labels, num_classes=79)
        elapsed = time.time() - epoch_start
        print(f"Epoch {epoch}/{max_epochs} | Time: {elapsed:.2f}s | Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f} | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}")
        
        torch.save(model.state_dict(), latest_ckpt)
        
        saved_best_loss = False
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_val_loss_epoch = epoch
            torch.save(model.state_dict(), best_loss_ckpt)
            saved_best_loss = True
            
        saved_best_acc = False
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_val_acc_epoch = epoch
            torch.save(model.state_dict(), best_acc_ckpt)
            saved_best_acc = True
            
            final_cm = cm.tolist()
            final_per_class_acc = per_class_acc.tolist()
            final_class_support = class_support.tolist()
            final_macro_acc = macro_acc
            final_preds = all_preds
            final_labels = all_labels
            
        history.append({"epoch": epoch, "time": elapsed, "train_loss": train_loss, "train_acc": train_acc, "val_loss": val_loss, "val_acc": val_acc, "saved_best_loss": saved_best_loss, "saved_best_acc": saved_best_acc})
        
    total_time = time.time() - total_start_time
    
    with open(r"d:\Singvox\Singvox\docs\ai-ml\EXPERIMENT_02_VPN_RAW_RESULTS.json", 'w') as f:
        json.dump({
            "history": history,
            "best_val_acc": best_val_acc,
            "best_acc_epoch": best_val_acc_epoch,
            "best_val_loss": best_val_loss,
            "best_loss_epoch": best_val_loss_epoch,
            "final_macro_acc": final_macro_acc,
            "confusion_matrix": final_cm,
            "per_class_accuracy": final_per_class_acc,
            "class_support": final_class_support,
            "total_time": total_time,
            "all_preds": final_preds,
            "all_labels": final_labels
        }, f, indent=2)
        
    print("SPOTER EXPERIMENT 02 (V2-VPN) TRAINING — COMPLETE")

if __name__ == "__main__":
    main()
