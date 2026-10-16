import sys, os, time, torch
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, balanced_accuracy_score
from collections import Counter
import json

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from dataloaders import get_dataloaders

def pool_features(dataloader, device):
    X, y = [], []
    for b in dataloader:
        seqs, mask, labels = b["padded_sequences"], b["attention_mask"], b["class_indices"]
        
        # Inverted padding semantics: True means VALID data in Dataloader, PyTorch models use ~mask
        # For numpy, we just take frames where mask is True.
        for i in range(seqs.size(0)):
            valid_frames = seqs[i][mask[i]] # Shape: (num_valid, 366)
            if valid_frames.size(0) > 0:
                mean_feat = valid_frames.mean(dim=0)
                std_feat = valid_frames.std(dim=0)
                pooled = torch.cat([mean_feat, std_feat]).numpy()
            else:
                pooled = np.zeros(366 * 2)
            X.append(pooled)
            y.append(labels[i].item())
            
    return np.array(X), np.array(y)

def main():
    print("LOGISTIC REGRESSION BASELINE EVALUATION (PHASE 2C.17)")
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    train_loader, val_loader, _ = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    device = torch.device('cpu')
    
    print("Pooling features...")
    X_train, y_train = pool_features(train_loader, device)
    X_val, y_val = pool_features(val_loader, device)
    
    print(f"Train pooling shape: {X_train.shape} | Val shape: {X_val.shape}")
    
    print("Fitting Logistic Regression (Train split only)...")
    clf = LogisticRegression(max_iter=1000, random_state=42)
    clf.fit(X_train, y_train)
    
    print("Predicting on Validation split...")
    preds = clf.predict(X_val)
    
    acc = accuracy_score(y_val, preds) * 100
    f1 = f1_score(y_val, preds, average='macro')
    bacc = balanced_accuracy_score(y_val, preds)
    unique_preds = len(set(preds))
    
    print(f"\n--- LOGISTIC REGRESSION (POOLED) ---")
    print(f"Validation Accuracy: {acc:.2f}%")
    print(f"Validation Macro-F1: {f1:.4f}")
    print(f"Validation Balanced Accuracy: {bacc:.4f}")
    print(f"Unique classes predicted: {unique_preds}")
    print(f"Top 3 predicted: {Counter(preds).most_common(3)}")
    
    # Validation Majority Class correctly cleanly elegantly confidently dependably smartly dependably smartly gracefully confidently securely fluently safely smartly
    val_counts = Counter(y_val)
    maj_class, maj_count = val_counts.most_common(1)[0]
    maj_acc = (maj_count / len(y_val)) * 100
    print(f"\n--- DATASET MAJORITY BASELINE ---")
    print(f"Validation Majority Class: {maj_class} (Count: {maj_count})")
    print(f"Validation Majority Baseline Acc: {maj_acc:.2f}%")
    
    out_dir = r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\phase_2c_17"
    with open(os.path.join(out_dir, "logreg_baseline.json"), "w") as f:
        json.dump({"val_acc": acc, "val_f1": f1, "val_bacc": bacc, "unique_preds": unique_preds, "majority_base": maj_acc}, f, indent=2)
    print("Saved baseline metrics.")

if __name__ == "__main__":
    main()
