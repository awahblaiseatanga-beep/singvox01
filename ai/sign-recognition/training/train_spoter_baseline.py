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
        if support > 0:
            per_class_acc[i] = cm[i, i] / support
            
    macro_acc = np.mean(per_class_acc[class_support > 0])
    return cm, per_class_acc, class_support, macro_acc

def main():
    print("SPOTER BASELINE TRAINING RUN STARTED")
    
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    train_loader, val_loader, test_loader = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    
    print(f"Train split sequences: {len(train_loader.dataset)}")
    print(f"Val split sequences: {len(val_loader.dataset)}")
    print(f"Test split sequences: {len(test_loader.dataset)}")
    
    # Strictly ensure that test split is completely untouched
    del test_loader
    print("Test loader successfully deleted to guarantee ZERO access during training run.")
    
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping_dict = json.load(f)
    
    canonical_mapping = {v['class_index']: v['canonical_name'] for k, v in mapping_dict.items()}
    
    device = torch.device("cpu")
    
    model = Spoter(
        num_classes=79, 
        hidden_dim=512, 
        nhead=8, 
        num_encoder_layers=6, 
        num_decoder_layers=6, 
        dim_feedforward=2048, 
        dropout=0.1
    ).to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-4) # Fixed Optimizer and LR
    
    max_epochs = 100 # Maximum explicitly set to 100 epochs
    
    best_val_loss = float('inf')
    best_val_loss_epoch = -1
    best_val_acc = -1.0
    best_val_acc_epoch = -1
    
    checkpoint_dir = r"d:\Singvox\Singvox\ai\sign-recognition\models"
    latest_ckpt = os.path.join(checkpoint_dir, "spoter_baseline_latest_checkpoint.pt")
    best_loss_ckpt = os.path.join(checkpoint_dir, "spoter_baseline_best_val_loss_checkpoint.pt")
    best_acc_ckpt = os.path.join(checkpoint_dir, "spoter_baseline_best_val_acc_checkpoint.pt")
    
    history = []
    
    total_start_time = time.time()
    
    final_cm = None
    final_per_class_acc = None
    final_class_support = None
    final_macro_acc = None
    
    # Train Loop
    for epoch in range(1, max_epochs + 1):
        model.train()
        train_loss = 0.0
        train_acc = 0.0
        epoch_start = time.time()
        
        for batch in train_loader:
            seqs = batch["padded_sequences"].to(device)
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
        val_loss = 0.0
        val_acc = 0.0
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for batch in val_loader:
                seqs = batch["padded_sequences"].to(device)
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
        
        # Save checkpoints
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
            
            # Record the best metrics layout for the final report based on best_val_acc
            final_cm = cm
            final_per_class_acc = per_class_acc
            final_class_support = class_support
            final_macro_acc = macro_acc
            
        history.append({
            "epoch": epoch,
            "time": elapsed,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "val_loss": val_loss,
            "val_acc": val_acc,
            "saved_best_loss": saved_best_loss,
            "saved_best_acc": saved_best_acc
        })
        
    total_time = time.time() - total_start_time
    
    # Generate the Markdown Report exactly as specified
    report_content = f"""# SPOTER BASELINE TRAINING REPORT

## Final Configuration
- **Model**: SPOTER Encoder-Decoder
- **Input dimension**: 366
- **d_model**: 512
- **Attention heads**: 8
- **Encoder layers**: 6
- **Decoder layers**: 6
- **Feed-forward dimension**: 2048
- **Dropout**: 0.1
- **Output classes**: 79
- **Positional Encoding**: Learned
- **Query Mechanism**: Single Class Query
- **Optimizer**: AdamW
- **Learning rate**: 1e-4
- **Batch size**: 32
- **Loss Function**: CrossEntropyLoss
- **Random seed**: 42
- **Maximum epochs**: 100
- **Test set access**: 0 samples (Strictly isolated)

## Overfitting Observations
Training advanced strictly to the 100 epoch boundary to observe validation drift.
- **Best validation loss recorded:** {best_val_loss:.4f} at Epoch {best_val_loss_epoch}
- **Best validation accuracy recorded:** {best_val_acc:.4f} at Epoch {best_val_acc_epoch}
If the best validation loss occurred significantly earlier than the final epoch whilst training loss continued dropping, overfitting likely occurred past epoch {best_val_loss_epoch}.

## Runtime & Checkpoints
- **Total Training Runtime**: {total_time/60:.2f} minutes
- **Latest Checkpoint**: `{latest_ckpt}`
- **Best Validation Loss Checkpoint**: `{best_loss_ckpt}`
- **Best Validation Accuracy Checkpoint**: `{best_acc_ckpt}`

## Macro & Per-Class Validation Results
*(Measured at Best Validation Accuracy Epoch {best_val_acc_epoch})*
- **Macro Validation Accuracy**: {final_macro_acc:.4f}

### Per-Class Validation Accuracy
"""
    for i in range(79):
        acc = final_per_class_acc[i]
        sup = int(final_class_support[i])
        name = canonical_mapping.get(i, f"Class {i}")
        report_content += f"- **Class {i} ({name})**: {acc:.4f} (Support: {sup})\n"
        
    report_content += "\n## Validation Confusion Matrix\n*(Rows: True Class, Columns: Predicted Class)*\n```text\n"
    for row in range(79):
        report_content += " ".join(f"{int(x):3d}" for x in final_cm[row]) + "\n"
    report_content += "```\n\n## Epoch-by-Epoch History\n"
    
    report_content += "| Epoch | Time (s) | Train Loss | Train Acc | Val Loss | Val Acc | Best Loss Step | Best Acc Step |\n"
    report_content += "|-------|----------|------------|-----------|----------|---------|----------------|---------------|\n"
    for h in history:
         report_content += f"| {h['epoch']} | {h['time']:.2f} | {h['train_loss']:.4f} | {h['train_acc']:.4f} | {h['val_loss']:.4f} | {h['val_acc']:.4f} | {h['saved_best_loss']} | {h['saved_best_acc']} |\n"
         
    report_path = r"d:\Singvox\Singvox\docs\ai-ml\SPOTER_BASELINE_TRAINING_REPORT.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"Report successfully saved to {report_path}")
    print("SPOTER BASELINE TRAINING — COMPLETE")
    
if __name__ == "__main__":
    main()
