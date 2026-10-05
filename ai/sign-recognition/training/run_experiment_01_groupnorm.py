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

def compute_train_scalars(train_loader):
    lh_idx, rh_idx, pose_xyz_idx, face_idx = get_xyz_indices()
    
    lh_vals, rh_vals, pose_vals, face_vals = [], [], [], []
    
    for batch in train_loader:
        seqs = batch["padded_sequences"]
        
        for b in range(seqs.size(0)):
            l = batch["original_lengths"][b].item()
            valid_seq = seqs[b, :l, :]
            
            # Extract elements omitting pure zeros (pad / missing tracking)
            # Left Hand
            lh_active = (valid_seq[:, lh_idx].abs().sum(dim=1) > 0)
            if lh_active.sum() > 0:
                lh_vals.append(valid_seq[lh_active][:, lh_idx].flatten())
                
            # Right Hand
            rh_active = (valid_seq[:, rh_idx].abs().sum(dim=1) > 0)
            if rh_active.sum() > 0:
                rh_vals.append(valid_seq[rh_active][:, rh_idx].flatten())
                
            # Pose XYZ
            pose_active = (valid_seq[:, pose_xyz_idx].abs().sum(dim=1) > 0)
            if pose_active.sum() > 0:
                pose_vals.append(valid_seq[pose_active][:, pose_xyz_idx].flatten())
                
            # Face
            face_active = (valid_seq[:, face_idx].abs().sum(dim=1) > 0)
            if face_active.sum() > 0:
                face_vals.append(valid_seq[face_active][:, face_idx].flatten())
                
    lh_tensor = torch.cat(lh_vals)
    rh_tensor = torch.cat(rh_vals)
    pose_tensor = torch.cat(pose_vals)
    face_tensor = torch.cat(face_vals)
    
    # Compute std explicitly over active elements uniformly across training volume
    scalars = {
        "left_hand": lh_tensor.std().item(),
        "right_hand": rh_tensor.std().item(),
        "pose_xyz": pose_tensor.std().item(),
        "face": face_tensor.std().item()
    }
    return scalars

def apply_scaling(seqs, scalars):
    lh_idx, rh_idx, pose_xyz_idx, face_idx = get_xyz_indices()
    scaled_seqs = seqs.clone()
    
    # Because valid zero bounds represent missing features, division gracefully maintains 0.0 = 0.0 
    # Pose visibility and presence metrics are completely unaffected structurally natively
    scaled_seqs[:, :, lh_idx] = scaled_seqs[:, :, lh_idx] / scalars["left_hand"]
    scaled_seqs[:, :, rh_idx] = scaled_seqs[:, :, rh_idx] / scalars["right_hand"]
    scaled_seqs[:, :, pose_xyz_idx] = scaled_seqs[:, :, pose_xyz_idx] / scalars["pose_xyz"]
    scaled_seqs[:, :, face_idx] = scaled_seqs[:, :, face_idx] / scalars["face"]
    return scaled_seqs

def compute_group_stats(loader, scalars=None):
    lh_idx, rh_idx, pose_xyz_idx, face_idx = get_xyz_indices()
    groups = {"Left Hand": lh_idx, "Right Hand": rh_idx, "Pose XYZ": pose_xyz_idx, "Face XYZ": face_idx}
    both_hands_idx = lh_idx + rh_idx
    stats_out = {g: {"l2s": [], "vars": [], "zeros": []} for g in list(groups.keys()) + ["Both Hands"]}
    
    for batch in loader:
        seqs = batch["padded_sequences"]
        if scalars is not None:
             seqs = apply_scaling(seqs, scalars)
             
        for b in range(seqs.size(0)):
            l = batch["original_lengths"][b].item()
            valid_seq = seqs[b, :l, :]
            
            for g_name, g_idx in groups.items():
                block = valid_seq[:, g_idx]
                stats_out[g_name]["l2s"].append(torch.linalg.norm(block).item())
                stats_out[g_name]["vars"].append(torch.var(block).item() if block.numel() > 1 else 0.0)
                stats_out[g_name]["zeros"].append((block == 0.0).sum().item() / block.numel())
            
            block_both = valid_seq[:, both_hands_idx]
            stats_out["Both Hands"]["l2s"].append(torch.linalg.norm(block_both).item())
            stats_out["Both Hands"]["vars"].append(torch.var(block_both).item() if block_both.numel() > 1 else 0.0)
            stats_out["Both Hands"]["zeros"].append((block_both == 0.0).sum().item() / block_both.numel())

    final_stats = {}
    for g_name in stats_out:
        final_stats[g_name] = {
            "mean_l2": np.mean(stats_out[g_name]["l2s"]),
            "median_l2": np.median(stats_out[g_name]["l2s"]),
            "variance": np.mean(stats_out[g_name]["vars"]),
            "zero_prop": np.mean(stats_out[g_name]["zeros"])
        }
    return final_stats

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
    print("SPOTER GROUP-NORMALIZED EXPERIMENT 01 RUN STARTED")
    
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    train_loader, val_loader, test_loader = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    
    # Strictly ensure that test split is completely untouched
    del test_loader
    print("Test loader successfully deleted to guarantee ZERO access during training run.")
    
    # 1. Compute Scalars dynamically and save
    print("Computing baseline magnitudes...")
    scalars = compute_train_scalars(train_loader)
    print("Computed Global Scalar Multipliers:")
    print(json.dumps(scalars, indent=2))
    
    scalar_path = r"d:\Singvox\Singvox\ai\sign-recognition\models\spoter_groupnorm_scalars.json"
    with open(scalar_path, 'w') as f: json.dump(scalars, f, indent=2)
    
    # 2. Extract explicit BEFORE vs AFTER metrics safely onto training split subsets natively
    print("\nExtracting BEFORE Representation Magnitude Geometry...")
    stats_before = compute_group_stats(train_loader, scalars=None)
    print("Extracting AFTER Representation Magnitude Geometry...")
    stats_after = compute_group_stats(train_loader, scalars=scalars)
    
    metrics_path = r"d:\Singvox\Singvox\docs\ai-ml\SPOTER_GROUPNORM_MAGNITUDE_METRICS.json"
    with open(metrics_path, 'w') as f:
        json.dump({"BEFORE": stats_before, "AFTER": stats_after}, f, indent=2)
    print(f"Magnitudes safely validated and extracted to {metrics_path}\n")
    
    # 3. Model construction securely analogous to established baseline
    with open(mapping_path, 'r', encoding='utf-8') as f: mapping_dict = json.load(f)
    canonical_mapping = {v['class_index']: v['canonical_name'] for k, v in mapping_dict.items()}
    
    device = torch.device("cpu")
    model = Spoter(num_classes=79, hidden_dim=512, nhead=8, num_encoder_layers=6, num_decoder_layers=6, dim_feedforward=2048, dropout=0.1).to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-4) # Fixed Optimizer and LR
    max_epochs = 100 # Maximum explicitly set to 100 epochs
    
    best_val_loss = float('inf')
    best_val_loss_epoch = -1
    best_val_acc = -1.0
    best_val_acc_epoch = -1
    
    checkpoint_dir = r"d:\Singvox\Singvox\ai\sign-recognition\models"
    best_loss_ckpt = os.path.join(checkpoint_dir, "spoter_groupnorm_best_val_loss_checkpoint.pt")
    best_acc_ckpt = os.path.join(checkpoint_dir, "spoter_groupnorm_best_val_acc_checkpoint.pt")
    
    history = []
    total_start_time = time.time()
    
    final_cm, final_per_class_acc, final_class_support, final_macro_acc = None, None, None, None
    
    # Train Loop dynamically leveraging explicit representations mapped equivalently
    for epoch in range(1, max_epochs + 1):
        model.train()
        train_loss, train_acc = 0.0, 0.0
        epoch_start = time.time()
        
        for batch in train_loader:
            seqs = apply_scaling(batch["padded_sequences"], scalars).to(device)
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
        
        # Validation Phase
        model.eval()
        val_loss, val_acc = 0.0, 0.0
        all_preds, all_labels = [], []
        
        with torch.no_grad():
            for batch in val_loader:
                seqs = apply_scaling(batch["padded_sequences"], scalars).to(device)
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
            
            final_cm = cm
            final_per_class_acc = per_class_acc
            final_class_support = class_support
            final_macro_acc = macro_acc
            
        history.append({"epoch": epoch, "time": elapsed, "train_loss": train_loss, "train_acc": train_acc, "val_loss": val_loss, "val_acc": val_acc, "saved_best_loss": saved_best_loss, "saved_best_acc": saved_best_acc})
        
    total_time = time.time() - total_start_time
    
    # Save the experimental results in an exact layout explicitly
    with open(r"d:\Singvox\Singvox\docs\ai-ml\EXPERIMENT_01_RAW_RESULTS.json", 'w') as f:
        json.dump({
            "history": history,
            "best_val_acc": best_val_acc,
            "best_acc_epoch": best_val_acc_epoch,
            "best_val_loss": best_val_loss,
            "best_loss_epoch": best_val_loss_epoch,
            "final_macro_acc": final_macro_acc,
            "total_time": total_time
        }, f, indent=2)
        
    print("SPOTER GROUP-NORMALIZED TRAINING — COMPLETE")

if __name__ == "__main__":
    main()
