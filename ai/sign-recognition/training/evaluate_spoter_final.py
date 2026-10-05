import os
import time
import json
import torch
import sys
import numpy as np
import torch.nn as nn

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders

def compute_accuracy(preds, labels):
    _, predicted = torch.max(preds, 1)
    correct = (predicted == labels).sum().item()
    return correct, labels.size(0)

def compute_per_class_metrics(all_preds, all_labels, num_classes=79):
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
            
    macro_acc = np.mean(per_class_acc[class_support > 0])
    return cm, per_class_acc, class_support, macro_acc

def evaluate_final():
    start_time = time.time()
    ckpt_path = r"d:\Singvox\Singvox\ai\sign-recognition\models\spoter_baseline_best_val_acc_checkpoint.pt"
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    # Strictly isolate just the test_loader
    train_loader, val_loader, test_loader = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    del train_loader
    del val_loader
    
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping_dict = json.load(f)
    
    canonical_mapping = {v['class_index']: v['canonical_name'] for k, v in mapping_dict.items()}
    
    device = torch.device("cpu")
    model = Spoter(num_classes=79, hidden_dim=512, nhead=8, num_encoder_layers=6, num_decoder_layers=6, dim_feedforward=2048, dropout=0.1)
    
    state_dict = torch.load(ckpt_path, map_location=device, weights_only=True)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    
    criterion = nn.CrossEntropyLoss()
    
    test_loss = 0.0
    total_correct = 0
    total_samples = 0
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for batch in test_loader:
            seqs = batch["padded_sequences"].to(device)
            mask = batch["attention_mask"].to(device)
            labels = batch["class_indices"].to(device)
            
            preds = model(seqs, attention_mask=mask)
            loss = criterion(preds, labels)
            
            test_loss += loss.item() * seqs.size(0)
            corr, t = compute_accuracy(preds, labels)
            total_correct += corr
            total_samples += t
            
            _, predicted = torch.max(preds, 1)
            all_preds.extend(predicted.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())
            
    test_loss /= total_samples
    top1_acc = total_correct / total_samples
    
    cm, per_class_acc, class_support, macro_acc = compute_per_class_metrics(all_preds, all_labels, num_classes=79)
    
    elapsed = time.time() - start_time
    
    # Generate report
    report_content = f"""# SPOTER FINAL TEST EVALUATION REPORT

## Evaluation Details
- **Evaluation Checkpoint**: `{ckpt_path}` (Epoch 75 Best Validation Accuracy)
- **Dataset / Test Split Used**: 
  - Manifest: `{manifest_path}`
  - Features: `{features_dir}`
  - Mapping: `{mapping_path}`
- **Number of Test Sequences**: {total_samples} (Expected: 1,011)
- **Number of Classes**: 79
- **Evaluation Runtime**: {elapsed:.2f} seconds

## Model Configuration (Frozen Baseline)
- Input: 366-D array (padded masking support)
- d_model: 512, Attention heads: 8
- Encoder layers: 6, Decoder layers: 6
- FFN: 2048, Dropout: 0.1
- Learned positional encoding, Single Class Query

## Limitations and Caveats
**IMPORTANT: Do not call this metric "real-world accuracy."**
The following metrics represent final held-out test performance under exactly the same conditions as the validation split. 
These results reflect performance strictly subject to limitations caused by the dataset's vocabulary coverage, signer distribution biases, and per-class support variance. Preprocessing parameters and class mappings remain artificially constrained to the 79-class subset baseline. 

## Overall Performance Metrics
- **Top-1 Test Accuracy**: {top1_acc:.4f} ({total_correct} / {total_samples})
- **Macro-average Test Accuracy**: {macro_acc:.4f}
- **Test Loss (CrossEntropy)**: {test_loss:.4f}
- **Correct Predictions**: {total_correct}
- **Incorrect Predictions**: {total_samples - total_correct}

## Per-Class Results
"""
    for i in range(79):
        acc = per_class_acc[i]
        sup = int(class_support[i])
        name = canonical_mapping.get(i, f"Class {i}")
        report_content += f"- **Class {i} ({name})**: {acc:.4f} (Support: {sup})\n"
        
    report_content += "\n## Confusion Matrix\n*(Rows: True Class, Columns: Predicted Class)*\n```text\n"
    for row in range(79):
        report_content += " ".join(f"{int(x):3d}" for x in cm[row]) + "\n"
    report_content += "```\n\n## Isolation Guarantee\n"
    report_content += "This assessment explicitly confirms that the test set was utilized exclusively for final performance evaluation without any retraining, hyperparameter adaptation, checkpoint selection, threshold calibration, or post-hoc optimizations applied against test outputs.\n"
    
    report_path = r"d:\Singvox\Singvox\docs\ai-ml\SPOTER_FINAL_TEST_EVALUATION_REPORT.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print("SPOTER FINAL TEST EVALUATION — COMPLETE")
    print(f"Test Top-1 Accuracy: {top1_acc:.4f}")
    print(f"Macro Accuracy: {macro_acc:.4f}")
    print(f"Test Loss: {test_loss:.4f}")
    print(f"Correct / Total: {total_correct} / {total_samples}")
    print(f"Number of classes: 79")

if __name__ == "__main__":
    evaluate_final()
