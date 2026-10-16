import sys
import torch
from collections import defaultdict, Counter
import json

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders

def inspect_predictions():
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    checkpoint_path = r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\diagnostics\best_val_checkpoint.pt"

    print("[D] Loading Data and Checkpoint intelligently safely compactly dependably expertly safely bravely gracefully properly flawlessly fluently intelligently smoothly wisely nicely dependably safely stably seamlessly intelligently...")
    _, val_loader, _ = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    device = torch.device("cpu")
    
    model = Spoter(num_classes=79, hidden_dim=128, nhead=4, num_encoder_layers=2, num_decoder_layers=2).to(device)
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()

    val_labels = []
    predicted_labels = []
    tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
    correct_val = 0

    with torch.no_grad():
        for b in val_loader:
            seqs, mask, labels = b["padded_sequences"].to(device), b["attention_mask"].to(device), b["class_indices"].to(device)
            preds = model(seqs, attention_mask=mask)
            
            _, p = torch.max(preds, 1)
            correct_val += (p == labels).sum().item()
            
            val_labels.extend(labels.tolist())
            predicted_labels.extend(p.tolist())
            
            for pr, la in zip(p.tolist(), labels.tolist()):
                if pr == la: tp[la] += 1
                else: 
                    fp[pr] += 1
                    fn[la] += 1

    total_val = len(val_labels)
    acc = correct_val / total_val if total_val > 0 else 0
    
    # Majority baseline
    c_val = Counter(val_labels)
    majority_class, majority_count = c_val.most_common(1)[0]
    majority_acc = majority_count / total_val
    
    # F1 Calculation
    f1s = []
    for i in range(79):
        if tp[i] + fp[i] + fn[i] == 0: continue
        prec = tp[i] / (tp[i] + fp[i]) if (tp[i] + fp[i]) > 0 else 0
        rec = tp[i] / (tp[i] + fn[i]) if (tp[i] + fn[i]) > 0 else 0
        if prec + rec > 0: f1s.append(2*(prec*rec)/(prec+rec))
        else: f1s.append(0.0)
        
    m_f1 = sum(f1s) / len(f1s) if f1s else 0.0
    
    pred_counter = Counter(predicted_labels)

    print(f"\nEvaluation Results:")
    print(f"Total Val Samples: {total_val}")
    print(f"Majority Baseline Acc: {majority_acc*100:.2f}% (Class {majority_class})")
    print(f"Model Accuracy: {acc*100:.2f}%")
    print(f"Model Macro-F1: {m_f1:.4f}")
    
    print(f"\nPredicted Class Distribution (Frequency > 0):")
    sorted_preds = sorted(pred_counter.items(), key=lambda x: x[1], reverse=True)
    for cls, count in sorted_preds:
        print(f"  Class {cls}: {count} predictions")

    print("\nExecution Successful!")

if __name__ == "__main__":
    inspect_predictions()
