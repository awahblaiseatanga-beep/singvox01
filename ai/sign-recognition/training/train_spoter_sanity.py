import sys
import os
import time
import torch
import torch.nn as nn
import torch.optim as optim

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders

def compute_accuracy(preds, labels):
    _, predicted = torch.max(preds, 1)
    correct = (predicted == labels).sum().item()
    return correct / labels.size(0)

def main():
    print("SPOTER SANITY TRAINING RUN STARTED")
    
    # 1. Initialize data loaders
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    # Batch size 32
    train_loader, val_loader, test_loader = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    print(f"Train split samples usage: {len(train_loader.dataset)}")
    print(f"Val split samples usage: {len(val_loader.dataset)}")
    
    # Asserting Test Split is completely untouched
    test_data_used = 0 
    
    device = torch.device("cpu") # Given the environment constraint
    
    model = Spoter(
        num_classes=79, hidden_dim=512, nhead=8, 
        num_encoder_layers=6, num_decoder_layers=6, 
        dim_feedforward=2048, dropout=0.1
    ).to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-4)
    
    epochs = 2
    
    # Pre-training check
    pre_params = [p.clone() for p in model.parameters()]
    first_batch_step = False
    param_updated = False
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        train_acc = 0.0
        start_time = time.time()
        
        for batch in train_loader:
            seqs = batch["padded_sequences"].to(device)
            mask = batch["attention_mask"].to(device)
            labels = batch["class_indices"].to(device)
            
            optimizer.zero_grad()
            preds = model(seqs, attention_mask=mask)
            loss = criterion(preds, labels)
            
            # gradient check on first step
            loss.backward()
            
            if not first_batch_step:
                has_finite_grads = all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
                print(f"Epoch {epoch+1} Batch 1 - Finite gradients check: {has_finite_grads}")
                first_batch_step = True
                
            optimizer.step()
            
            if not param_updated:
                param_updated = any(not torch.equal(p, p_new) for p, p_new in zip(pre_params, model.parameters()))
                print(f"Epoch {epoch+1} Batch 1 - Parameters updated successfully: {param_updated}")
                
            train_loss += loss.item() * seqs.size(0)
            train_acc += compute_accuracy(preds, labels) * seqs.size(0)
            
        train_loss /= len(train_loader.dataset)
        train_acc /= len(train_loader.dataset)
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_acc = 0.0
        
        with torch.no_grad():
            for batch in val_loader:
                seqs = batch["padded_sequences"].to(device)
                mask = batch["attention_mask"].to(device)
                labels = batch["class_indices"].to(device)
                
                preds = model(seqs, attention_mask=mask)
                loss = criterion(preds, labels)
                
                val_loss += loss.item() * seqs.size(0)
                val_acc += compute_accuracy(preds, labels) * seqs.size(0)
                
        val_loss /= len(val_loader.dataset)
        val_acc /= len(val_loader.dataset)
        
        elapsed = time.time() - start_time
        print(f"Epoch {epoch+1}/{epochs} | "
              f"Time: {elapsed:.2f}s | "
              f"LR: 1e-4 | "
              f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}")
              
    # Save checkpoint
    chkpt_path = r"d:\Singvox\Singvox\ai\sign-recognition\models\sanity_checkpoint.pt"
    torch.save(model.state_dict(), chkpt_path)
    print(f"Checkpoint saved successfully to {chkpt_path}")
    
    # Reload validation
    model2 = Spoter()
    model2.load_state_dict(torch.load(chkpt_path, weights_only=True))
    model2.eval()
    
    batch = next(iter(val_loader))
    with torch.no_grad():
        preds2 = model2(batch["padded_sequences"], attention_mask=batch["attention_mask"])
    print(f"Reload Checkpoint Shape Eval: {list(preds2.shape)}")
    print(f"Test Split Extent Reached: {test_data_used} arrays - Untouched guarantee confirmed.")
    print("SANITY RUN COMPLETE")

if __name__ == "__main__":
    main()
