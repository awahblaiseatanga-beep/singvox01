import sys
import torch
import torch.nn as nn
import torch.optim as optim
import time
import json
import csv
from collections import Counter

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders

def run_overfit_diagnostic():
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    checkpoint_out = r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\diagnostics\phase_2c_15\overfit_checkpoint.pt"

    # We use a batch size of 8 as the tiny subset
    train_loader, _, _ = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=16)
    device = torch.device("cpu")
    
    # 1. Select deterministic subset
    # Since shuffle=True in get_dataloaders, we just get the first batch, but to be truly frozen,
    # let's fix the seed right before iter
    torch.manual_seed(42)
    b = next(iter(train_loader))
    
    seqs = b["padded_sequences"].to(device)
    mask = b["attention_mask"].to(device)
    labels = b["class_indices"].to(device)

    print("--- Tiny-Subset Selected ---")
    print(f"Shapes -> seqs: {seqs.shape}, mask: {mask.shape}, labels: {labels.shape}")
    print(f"Target Labels: {labels.tolist()}")

    # 4. Canonical Model
    model = Spoter(num_classes=79, hidden_dim=128, nhead=4, num_encoder_layers=2, num_decoder_layers=2).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-3)
    
    epochs = 400
    print("\n--- Training Overfit Loop ---")
    start = time.time()

    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        
        preds = model(seqs, attention_mask=mask)
        loss = criterion(preds, labels)
        loss.backward()
        
        # Monitor gradient norms to ensure flow
        grad_norm = 0.0
        for p in model.parameters():
            if p.grad is not None:
                grad_norm += p.grad.data.norm(2).item() ** 2
        grad_norm = grad_norm ** 0.5
        
        optimizer.step()
        
        if epoch % 50 == 0 or epoch == 1:
            _, predicted = torch.max(preds, 1)
            correct = (predicted == labels).sum().item()
            acc = correct / labels.size(0) * 100
            unique_preds = len(set(predicted.tolist()))
            
            print(f"Epoch {epoch:03d}/{epochs} | Loss: {loss.item():.4f} | Acc: {acc:>6.2f}% | GradNorm: {grad_norm:.6f} | Unique Preds: {unique_preds}")
            if epoch == epochs:
                print(f"Final predictions: {predicted.tolist()}")

    print(f"\nTraining Complete (Time: {time.time()-start:.1f}s)")
    torch.save(model.state_dict(), checkpoint_out)
    print(f"Artifact Saved: {checkpoint_out}")

if __name__ == "__main__":
    run_overfit_diagnostic()
