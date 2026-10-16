import sys
import torch
import torch.nn as nn
from collections import Counter
from sklearn.metrics import accuracy_score, f1_score

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders

def evaluate_split(model, dataloader, criterion, device):
    all_preds, all_labels = [], []
    total_loss = 0.0
    
    with torch.no_grad():
        for b in dataloader:
            seqs = b["padded_sequences"].to(device)
            mask = b["attention_mask"].to(device)
            labels = b["class_indices"].to(device)
            
            preds = model(seqs, attention_mask=mask)
            loss = criterion(preds, labels)
            
            total_loss += loss.item() * seqs.size(0)
            _, p = torch.max(preds, 1)
            
            all_preds.extend(p.tolist())
            all_labels.extend(labels.tolist())
            
    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)
    avg_loss = total_loss / len(dataloader.dataset)
    
    unique_classes = set(all_preds)
    freq = Counter(all_preds)
    
    return acc, f1, avg_loss, unique_classes, freq

def run_compare():
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    checkpoint_path = r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\diagnostics\best_val_checkpoint.pt"

    train_loader, val_loader, _ = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    device = torch.device("cpu")
    
    model = Spoter(num_classes=79, hidden_dim=128, nhead=4, num_encoder_layers=2, num_decoder_layers=2).to(device)
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()
    
    criterion = nn.CrossEntropyLoss()

    print("--- Train Split Evaluation ---")
    tr_acc, tr_f1, tr_loss, tr_uniq, tr_freq = evaluate_split(model, train_loader, criterion, device)
    print(f"Accuracy: {tr_acc:.4f} | Macro-F1: {tr_f1:.4f} | Loss: {tr_loss:.4f}")
    print(f"Unique classes predicted: {len(tr_uniq)}")
    print(f"Top 5 frequencies: {tr_freq.most_common(5)}")
    
    print("\n--- Val Split Evaluation ---")
    vl_acc, vl_f1, vl_loss, vl_uniq, vl_freq = evaluate_split(model, val_loader, criterion, device)
    print(f"Accuracy: {vl_acc:.4f} | Macro-F1: {vl_f1:.4f} | Loss: {vl_loss:.4f}")
    print(f"Unique classes predicted: {len(vl_uniq)}")
    print(f"Top 5 frequencies: {vl_freq.most_common(5)}")

if __name__ == "__main__":
    run_compare()
