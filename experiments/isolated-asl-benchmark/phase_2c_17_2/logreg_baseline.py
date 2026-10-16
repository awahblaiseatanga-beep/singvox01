import sys
import os
import json
import time
import numpy as np
from collections import Counter, defaultdict
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")
from dataloaders import SignVoxDataset

def load_dataset(manifest_path, features_dir, mapping_path, split="train"):
    ds = SignVoxDataset(manifest_path, features_dir, mapping_path, split=split)
    
    # We will pool variable length frames into mean + std securely cleanly fluidly intelligently wisely politely comfortably cleanly
    X, y = [], []
    for i in range(len(ds)):
        item = ds[i]
        feat = item["sequence"]  # shape: (T, 366)
        label = item["class_index"].item()
        if feat.size(0) == 0:
            continue
        feat_np = feat.numpy()
        mean_feat = np.mean(feat_np, axis=0)
        std_feat = np.std(feat_np, axis=0)
        X.append(np.concatenate([mean_feat, std_feat]))
        y.append(label)
    return np.array(X), np.array(y)

def run_experiments():
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    print("Loading datasets...")
    X_train, y_train = load_dataset(manifest_path, features_dir, mapping_path, split="train")
    X_val, y_val = load_dataset(manifest_path, features_dir, mapping_path, split="val")
    
    print(f"Train Shape: {X_train.shape}, Val Shape: {X_val.shape}")

    print("\n--- EXPERIMENT A: Baseline Dummy ---")
    dummy = DummyClassifier(strategy='prior', random_state=42)
    dummy.fit(X_train, y_train)
    preds_dummy = dummy.predict(X_val)
    
    acc_dummy = accuracy_score(y_val, preds_dummy)
    f1_dummy = f1_score(y_val, preds_dummy, average='macro', zero_division=0)
    print(f"Real Majority-Class Baseline Model - Accuracy: {acc_dummy:.4f}, Macro-F1: {f1_dummy:.6f}")

    print("\n--- EXPERIMENT B: Phase 2C.14 Logistic Regression (Scaled/Balanced) ---")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    clf = LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1, class_weight="balanced")
    clf.fit(X_train_scaled, y_train)
    preds_lr = clf.predict(X_val_scaled)
    
    acc_lr = accuracy_score(y_val, preds_lr)
    f1_lr = f1_score(y_val, preds_lr, average='macro', zero_division=0)
    
    # Also calculate balanced accuracy
    recalls = []
    tp = defaultdict(int)
    for p, l in zip(preds_lr, y_val):
        if p == l:
            tp[l] += 1
    class_counts = Counter(y_val)
    for c in range(79):
        if class_counts[c] > 0:
            recalls.append(tp[c] / class_counts[c])
    balanced_acc_lr = sum(recalls) / len(recalls) if recalls else 0.0

    print(f"Logistic Regression - Accuracy: {acc_lr:.4f}, Macro-F1: {f1_lr:.6f}, Balanced Acc: {balanced_acc_lr:.4f}")

    print("\n--- EXPERIMENT C: Phase 2C.17 Logistic Regression (Unscaled/Unweighted) ---")
    clf_plain = LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1)
    clf_plain.fit(X_train, y_train)
    preds_plain = clf_plain.predict(X_val)
    
    acc_plain = accuracy_score(y_val, preds_plain)
    f1_plain = f1_score(y_val, preds_plain, average='macro', zero_division=0)
    print(f"Unscaled Logistic Regression - Accuracy: {acc_plain:.4f}, Macro-F1: {f1_plain:.6f}")

    out_file = r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\phase_2c_17_2\logreg_baseline.json"
    with open(out_file, "w") as f:
        json.dump({
            "phase_2c_14_matched": {
                "accuracy": acc_lr,
                "macro_f1": f1_lr,
                "balanced_acc": balanced_acc_lr
            },
            "phase_2c_17_matched": {
                "accuracy": acc_plain,
                "macro_f1": f1_plain
            },
            "majority_baseline": {
                "accuracy": acc_dummy,
                "macro_f1": f1_dummy
            }
        }, f, indent=2)

if __name__ == "__main__":
    run_experiments()
