import sys
import os
import torch
import numpy as np
from collections import Counter
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, balanced_accuracy_score, classification_report

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders, SignVoxDataset

def load_dataset_for_lr(manifest_path, features_dir, mapping_path, split="train"):
    ds = SignVoxDataset(manifest_path, features_dir, mapping_path, split=split)
    X, y = [], []
    for i in range(len(ds)):
        item = ds[i]
        feat = item["sequence"]
        label = item["class_index"].item()
        if feat.size(0) == 0:
            continue
        feat_np = feat.numpy()
        mean_feat = np.mean(feat_np, axis=0)
        std_feat = np.std(feat_np, axis=0)
        X.append(np.concatenate([mean_feat, std_feat]))
        y.append(label)
    return np.array(X), np.array(y)

def verify():
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    checkpoint_path = r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\diagnostics\best_val_checkpoint.pt"

    print("--- 1. Verification of LR ---")
    X_train, y_train = load_dataset_for_lr(manifest_path, features_dir, mapping_path, split="train")
    X_val, y_val = load_dataset_for_lr(manifest_path, features_dir, mapping_path, split="val")
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    clf = LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1, class_weight="balanced")
    clf.fit(X_train_scaled, y_train)
    preds_lr = clf.predict(X_val_scaled)
    
    # Val info
    val_classes = set(y_val)
    print(f"Validation sample count: {len(y_val)}")
    print(f"Number of classes represented in validation: {len(val_classes)}")
    
    # Majority
    c_val = Counter(y_val)
    majority_class, majority_count = c_val.most_common(1)[0]
    majority_acc = majority_count / len(y_val)
    print(f"Majority-class baseline accuracy (calculated from actual val labels): {majority_acc:.4f} (Class {majority_class})")

    lr_acc = accuracy_score(y_val, preds_lr)
    lr_f1 = f1_score(y_val, preds_lr, average='macro', zero_division=0)
    lr_bacc = balanced_accuracy_score(y_val, preds_lr)
    print(f"\nLogistic Regression - Accuracy: {lr_acc:.4f}, Macro-F1: {lr_f1:.4f}, Balanced Acc: {lr_bacc:.4f}")
    
    lr_unique = set(preds_lr)
    print(f"Number of unique predicted classes (LR): {len(lr_unique)}")
    print("Prediction frequency (LR):")
    print(Counter(preds_lr).most_common(5), "... (showing top 5)")

    print("\n--- 2. Verification of SPOTER ---")
    _, val_loader, _ = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    device = torch.device("cpu")
    model = Spoter(num_classes=79, hidden_dim=128, nhead=4, num_encoder_layers=2, num_decoder_layers=2).to(device)
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()

    val_labels = []
    predicted_labels = []
    with torch.no_grad():
        for b in val_loader:
            seqs, mask, labels = b["padded_sequences"].to(device), b["attention_mask"].to(device), b["class_indices"].to(device)
            preds = model(seqs, attention_mask=mask)
            _, p = torch.max(preds, 1)
            val_labels.extend(labels.tolist())
            predicted_labels.extend(p.tolist())

    sp_acc = accuracy_score(val_labels, predicted_labels)
    sp_f1 = f1_score(val_labels, predicted_labels, average='macro', zero_division=0)
    sp_bacc = balanced_accuracy_score(val_labels, predicted_labels)
    
    print(f"SPOTER - Accuracy: {sp_acc:.4f}, Macro-F1: {sp_f1:.4f}, Balanced Acc: {sp_bacc:.4f}")
    
    sp_unique = set(predicted_labels)
    print(f"Number of unique predicted classes (SPOTER): {len(sp_unique)}")
    print("Prediction frequency (SPOTER):")
    print(Counter(predicted_labels).most_common(5))
    
    print("\nDid the two models use identical labels?")
    print(val_labels == list(y_val))
    
if __name__ == "__main__":
    verify()
