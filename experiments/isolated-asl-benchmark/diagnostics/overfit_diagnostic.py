import sys
import torch
import torch.nn as nn
import torch.optim as optim

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders
import time

def run_diagnostic():
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"

    # Batch Size 4, so we evaluate overfit natively effectively properly
    train_loader, _, _ = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=4)
    device = torch.device("cpu")
    
    # Tiny Configuration
    model = Spoter(num_classes=79, hidden_dim=64, nhead=4, num_encoder_layers=2, num_decoder_layers=2).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-3)
    
    # Grab exactly ONE batch (4 sequences)
    b = next(iter(train_loader))
    seqs = b["padded_sequences"].to(device)
    mask = b["attention_mask"].to(device)
    labels = b["class_indices"].to(device)
    
    print(f"[Small Subset Constraints Diagnostics]")
    print(f"Target Subset Labels: {labels.tolist()}")
    print("Beginning 100 Epochs strict Overfit Check natively safely...")
    
    start = time.time()
    for epoch in range(100):
        model.train()
        optimizer.zero_grad()
        
        preds = model(seqs, attention_mask=mask)
        loss = criterion(preds, labels)
        loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 25 == 0:
            _, predicted = torch.max(preds, 1)
            correct = (predicted == labels).sum().item()
            print(f"Epoch {epoch+1}/100 | Loss: {loss.item():.4f} | Output Predictions: {predicted.tolist()} | Acc: {correct/4*100}%")
            
    print(f"Complete Diagnostics safely ({time.time()-start:.1f}s)")

if __name__ == "__main__":
    run_diagnostic()
