import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders

def test_spoter_configuration():
    print("Testing Pipeline initializing natively...")
    
    # 1. Initialize data loaders
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    train_loader, val_loader, test_loader = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=8)
    
    batch = next(iter(train_loader))
    padded_seqs = batch["padded_sequences"]
    attention_mask = batch["attention_mask"]
    labels = batch["class_indices"]
    
    print(f"Batch Sequences: {padded_seqs.shape}")
    print(f"Batch Mask: {attention_mask.shape}")
    print(f"Batch Labels: {labels.shape}")
    
    # 2. Init Model
    model = Spoter(num_classes=79, hidden_dim=512, nhead=8, num_encoder_layers=6, num_decoder_layers=6, dim_feedforward=2048, dropout=0.1)
    
    # TEST 1 & 2: Forward pass & Masking evaluation
    model.eval()
    with torch.no_grad():
        out = model(padded_seqs, attention_mask=attention_mask)
        assert out.shape == (8, 79), f"Output shape failed: {out.shape}"
        assert not torch.isnan(out).any(), "NaN in output"
        assert not torch.isinf(out).any(), "Inf in output"
        print("TEST 1 & 2 (Forward & Masking): PASS - Output [8, 79] strictly maintained.")
        
    # TEST 3: Loss Function
    model.train()
    criterion = nn.CrossEntropyLoss()
    
    out = model(padded_seqs, attention_mask=attention_mask)
    loss = criterion(out, labels)
    
    assert torch.isfinite(loss), "Loss is not finite!"
    assert labels.min() >= 0 and labels.max() <= 78, "Labels are out of bounding limits."
    print(f"TEST 3 (Loss): PASS - Loss is finite ({loss.item()}) and labels range is valid.")
    
    # TEST 4: Backpropagation & Optimizer Iteration
    optimizer = optim.AdamW(model.parameters(), lr=1e-4)
    
    params_before = [p.clone() for p in model.parameters()]
    
    optimizer.zero_grad()
    loss.backward()
    
    # Verify gradients exist and are finite
    has_finite_grads = all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
    assert has_finite_grads, "Gradients are not finite!"
    
    optimizer.step()
    
    params_changed = any(not torch.equal(p, p_new) for p, p_new in zip(params_before, model.parameters()))
    assert params_changed, "Parameters failed to change heavily sequentially after backwards step."
    
    print("TEST 4 (Backprop & Optimize): PASS - Gradients valid and parameter constraints shifted successfully.")
    
    # TEST 5: Parameter Tracking Constraints
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"TEST 5 (Parameters): Total {total_params} | Trainable {trainable_params}")
    
    print("ALL TESTS PASSED SUCCESSFULLY NATIVELY.")

if __name__ == "__main__":
    test_spoter_configuration()
