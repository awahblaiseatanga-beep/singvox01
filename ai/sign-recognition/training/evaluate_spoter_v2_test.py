import sys
import os
import json
import torch
import torch.nn as nn
from collections import defaultdict

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders
from train_spoter_v2 import apply_scaling, compute_accuracy, compute_per_class_metrics

def main():
    print("SPOTER V2 FINAL TEST EVALUATION")
    
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    # We load standard dataloaders and discard train/val. Use only the final test_loader.
    train_loader, val_loader, test_loader = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    del train_loader
    del val_loader
    
    scalar_path = r"d:\Singvox\Singvox\ai\sign-recognition\models\spoter_v2_groupnorm_scalars.json"
    with open(scalar_path, 'r') as f:
        scalars = json.load(f)
        
    device = torch.device("cpu")
    model = Spoter(num_classes=79, hidden_dim=512, nhead=8, num_encoder_layers=6, num_decoder_layers=6, dim_feedforward=2048, dropout=0.1).to(device)
    
    ckpt_path = r"d:\Singvox\Singvox\ai\sign-recognition\checkpoints\spoter_v2_groupnorm_best_val_acc.pt"
    print(f"Loading checkpoint: {ckpt_path}")
    model.load_state_dict(torch.load(ckpt_path, map_location=device, weights_only=True))
    model.eval()
    
    criterion = nn.CrossEntropyLoss()
    
    test_loss = 0.0
    test_acc = 0.0
    all_preds = []
    all_labels = []
    total_samples = 0
    correct = 0
    incorrect = 0
    
    with torch.no_grad():
        for batch in test_loader:
            seqs = apply_scaling(batch["padded_sequences"], scalars).to(device)
            mask = batch["attention_mask"].to(device)
            labels = batch["class_indices"].to(device)
            
            preds = model(seqs, attention_mask=mask)
            loss = criterion(preds, labels)
            
            bs = seqs.size(0)
            test_loss += loss.item() * bs
            
            _, predicted = torch.max(preds, 1)
            corr = (predicted == labels).sum().item()
            correct += corr
            incorrect += (bs - corr)
            
            all_preds.extend(predicted.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())
            total_samples += bs
            
    test_loss /= total_samples
    test_acc = correct / total_samples
    
    cm, per_class_acc, class_support, macro_acc = compute_per_class_metrics(all_preds, all_labels, num_classes=79)
    
    # generate top confusion pairs
    confusions = []
    for i in range(79):
        for j in range(79):
            if i != j and cm[i][j] > 0:
                confusions.append({
                    "true_class": i,
                    "pred_class": j,
                    "count": int(cm[i][j])
                })
    
    confusions.sort(key=lambda x: x["count"], reverse=True)
    top_confusion_pairs = confusions[:20]
    
    results = {
        "test_top1_accuracy": float(test_acc),
        "correct_predictions": int(correct),
        "incorrect_predictions": int(incorrect),
        "test_loss": float(test_loss),
        "macro_accuracy": float(macro_acc),
        "total_samples": int(total_samples),
        "per_class_accuracy": [float(x) for x in per_class_acc],
        "class_support": [int(x) for x in class_support],
        "top_confusion_pairs": top_confusion_pairs,
        "confusion_matrix": cm.tolist()
    }
    
    with open(r"d:\Singvox\Singvox\docs\ai-ml\SPOTER_V2_FINAL_TEST_RESULTS.json", 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Test Evaluation Complete.")
    print(f"Samples: {total_samples}")
    print(f"Correct: {correct} | Incorrect: {incorrect}")
    print(f"Test Loss: {test_loss:.4f}")
    print(f"Test Acc:  {test_acc*100:.2f}%")
    print(f"Macro Acc: {macro_acc*100:.2f}%")

if __name__ == "__main__":
    main()
