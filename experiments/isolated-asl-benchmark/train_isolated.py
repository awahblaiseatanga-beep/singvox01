import sys, os, time, torch
import torch.nn as nn
import torch.optim as optim
from collections import defaultdict
import datetime

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders

def calc_f1(preds, labels, num_classes=79):
    _, predicted = torch.max(preds, 1)
    
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    
    for p, l in zip(predicted.tolist(), labels.tolist()):
        if p == l:
            tp[l] += 1
        else:
            fp[p] += 1
            fn[l] += 1
            
    f1s = []
    for c in range(num_classes):
        if tp[c] + fp[c] + fn[c] == 0: continue
        precision = tp[c] / (tp[c] + fp[c]) if (tp[c] + fp[c]) > 0 else 0
        recall = tp[c] / (tp[c] + fn[c]) if (tp[c] + fn[c]) > 0 else 0
        if precision + recall > 0:
            f1s.append(2 * (precision * recall) / (precision + recall))
        else:
            f1s.append(0.0)
            
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0
    correct = (predicted == labels).sum().item()
    return correct, macro_f1

def main():
    print("SPOTER ISOLATED ASL BENCHMARK STARTED")
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    train_loader, val_loader, test_loader = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    device = torch.device("cpu") 
    
    model = Spoter(num_classes=79, hidden_dim=64, nhead=4, num_encoder_layers=2, num_decoder_layers=2, dim_feedforward=256, dropout=0.1).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-4)
    epochs = 2
    
    print("\n--- Training Loop Phase (2 Epochs) ---", flush=True)
    start = time.time()
    for epoch in range(epochs):
        model.train()
        train_loss, train_correct = 0.0, 0
        for batch in train_loader:
            seqs, mask, labels = batch["padded_sequences"].to(device), batch["attention_mask"].to(device), batch["class_indices"].to(device)
            optimizer.zero_grad()
            preds = model(seqs, attention_mask=mask)
            loss = criterion(preds, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * seqs.size(0)
            c, _ = calc_f1(preds, labels)
            train_correct += c
            
        print(f"Epoch {epoch+1} Train Loss: {train_loss/len(train_loader.dataset):.4f}", flush=True)
        
    print(f"\nTraining Complete (Time: {time.time()-start:.1f}s)", flush=True)
    
    chkpt_path = r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\isolated_benchmark.pt"
    torch.save(model.state_dict(), chkpt_path)
    print(f"Artifact Saved: {chkpt_path}", flush=True)
    
    # Eval Val set
    print("\n--- Validation Run ---", flush=True)
    model.eval()
    val_correct = 0
    all_preds, all_labels = [], []
    with torch.no_grad():
        for batch in val_loader:
            seqs, mask, labels = batch["padded_sequences"], batch["attention_mask"], batch["class_indices"]
            preds = model(seqs, attention_mask=mask)
            all_preds.append(preds)
            all_labels.append(labels)
            
    val_preds = torch.cat(all_preds, 0)
    val_true = torch.cat(all_labels, 0)
    c, f1 = calc_f1(val_preds, val_true)
    print(f"Validation Target Acc: {c/len(val_loader.dataset)*100:.2f}%")
    print(f"Validation Macro-F1: {f1:.4f}")

if __name__ == "__main__":
    main()
