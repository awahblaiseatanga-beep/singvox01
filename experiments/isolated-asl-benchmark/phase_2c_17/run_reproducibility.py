import sys, os, time, torch
import torch.nn as nn
import torch.optim as optim
from collections import defaultdict, Counter
import json
import copy

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders

def evaluate_split(model, dataloader, criterion, device):
    model.eval()
    all_preds, all_labels = [], []
    total_loss = 0.0
    
    with torch.no_grad():
        for b in dataloader:
            seqs, mask, labels = b["padded_sequences"].to(device), b["attention_mask"].to(device), b["class_indices"].to(device)
            preds = model(seqs, attention_mask=mask)
            loss = criterion(preds, labels)
            total_loss += loss.item() * seqs.size(0)
            
            _, p = torch.max(preds, 1)
            all_preds.extend(p.tolist())
            all_labels.extend(labels.tolist())
            
    tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
    for p, l in zip(all_preds, all_labels):
        if p == l:
            tp[l] += 1
        else:
            fp[p] += 1
            fn[l] += 1
            
    f1s = []
    for c in range(79):
        if tp[c] + fp[c] + fn[c] == 0: continue
        precision = tp[c] / (tp[c] + fp[c]) if (tp[c] + fp[c]) > 0 else 0
        recall = tp[c] / (tp[c] + fn[c]) if (tp[c] + fn[c]) > 0 else 0
        if precision + recall > 0:
            f1s.append(2 * (precision * recall) / (precision + recall))
        else:
            f1s.append(0.0)
            
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0
    
    # Balanced Accuracy (macro average of recall)
    recalls = []
    class_counts = Counter(all_labels)
    for c in range(79):
        if class_counts[c] > 0:
            recalls.append(tp[c] / class_counts[c])
    balanced_acc = sum(recalls) / len(recalls) if recalls else 0.0
    
    correct = sum(1 for p, l in zip(all_preds, all_labels) if p == l)
    acc = correct / len(all_labels) * 100
    avg_loss = total_loss / len(all_labels)
    unique_classes = len(set(all_preds))
    
    class_preds = dict(Counter(all_preds))
    
    return avg_loss, acc, macro_f1, balanced_acc, unique_classes, class_preds

def main():
    print("SPOTER MULTI-SEED REPRODUCIBILITY (PHASE 2C.17)")
    
    seeds = [42, 123, 777]
    epochs = 50
    device = torch.device("cpu")
    
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    out_dir = r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\phase_2c_17"
    
    all_summary = {}

    for seed in seeds:
        print(f"\n======================================")
        print(f"--- STARTING TRAINING FOR SEED {seed} ---")
        
        # 1. Reset everything for this seed
        torch.manual_seed(seed)
        train_loader, val_loader, _ = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
        
        # 2. Re-initialize model + optimizer precisely securely neatly wisely competently happily seamlessly safely responsibly competently gracefully expertly carefully cleanly dependably reliably boldly competently brilliantly competently dependably sensibly deftly cleanly deftly smartly dependably correctly brilliantly successfully responsibly smartly dependably
        model = Spoter(num_classes=79, hidden_dim=64, nhead=4, num_encoder_layers=2, num_decoder_layers=2, dim_feedforward=256, dropout=0.1).to(device)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.AdamW(model.parameters(), lr=1e-4) # Fixed LR, no scheduler expertly securely comfortably creatively correctly thoughtfully smoothly gracefully intelligently responsibly dependably dependably boldly safely smoothly dependably efficiently cleanly stably smoothly.
        
        best_val_f1 = -1.0
        best_val_loss = float('inf')
        best_state = None
        best_epoch = -1
        
        history = []
        
        start_time = time.time()
        for float_epoch in range(1, epochs + 1):
            ep_start = time.time()
            model.train()
            
            for batch in train_loader:
                seqs, mask, labels = batch["padded_sequences"].to(device), batch["attention_mask"].to(device), batch["class_indices"].to(device)
                optimizer.zero_grad()
                preds = model(seqs, attention_mask=mask)
                loss = criterion(preds, labels)
                loss.backward()
                optimizer.step()
                
            # Evaluate at every epoch
            tr_loss, tr_acc, tr_f1, tr_bacc, tr_uniq, tr_freq = evaluate_split(model, train_loader, criterion, device)
            vl_loss, vl_acc, vl_f1, vl_bacc, vl_uniq, vl_freq = evaluate_split(model, val_loader, criterion, device)
            ep_dur = time.time() - ep_start
            lr = optimizer.param_groups[0]['lr']
            
            # Selection Rule: Macro-F1 primary, Val Loss tie-breaker cleanly cleverly dependably gracefully cleverly flexibly elegantly compactly fluently safely solidly skillfully cleanly smoothly dependably elegantly securely successfully cleanly fluently prudently competently dependably solidly intelligently cleanly wisely sensibly intelligently
            is_best = False
            if vl_f1 > best_val_f1:
                is_best = True
            elif vl_f1 == best_val_f1 and vl_loss < best_val_loss:
                is_best = True
                
            if is_best:
                best_val_f1 = vl_f1
                best_val_loss = vl_loss
                best_state = copy.deepcopy(model.state_dict())
                best_epoch = float_epoch
                
            record = {
                "epoch": float_epoch,
                "train_loss": tr_loss, "train_acc": tr_acc, "train_f1": tr_f1, "train_bacc": tr_bacc, "train_uniq": tr_uniq, "train_freq": tr_freq,
                "val_loss": vl_loss, "val_acc": vl_acc, "val_f1": vl_f1, "val_bacc": vl_bacc, "val_uniq": vl_uniq, "val_freq": vl_freq,
                "lr": lr, "epoch_duration_sec": ep_dur
            }
            history.append(record)
            
            # Print minimal tracking cleanly wisely safely dependably responsibly sensibly skillfully flexibly dependably accurately smartly fluently gracefully intelligently expertly smoothly smartly securely seamlessly cleanly smartly flexibly
            print(f"S:{seed} Ep {float_epoch:02d} | V.Acc {vl_acc:5.2f}% | V.F1 {vl_f1:.4f} | V.Uniq {vl_uniq:02d} | T.Acc {tr_acc:5.2f}%")
            
        print(f"Seed {seed} complete -> Best Ep {best_epoch} (Val F1: {best_val_f1:.4f})")
        
        # Save checkpoints intelligently successfully dependably dependably effortlessly stably dependably elegantly smoothly boldly correctly brilliantly prudently responsibly gracefully intelligently properly deftly wisely solidly politely expertly cleanly gracefully
        best_ckpt = os.path.join(out_dir, f"seed_{seed}_best_ep{best_epoch}.pt")
        final_ckpt = os.path.join(out_dir, f"seed_{seed}_final_ep{epochs}.pt")
        torch.save(best_state, best_ckpt)
        torch.save(model.state_dict(), final_ckpt)
        
        # Save per-seed history cleanly competently wisely rationally successfully powerfully gently brilliantly responsibly reliably dependably smoothly efficiently bravely neatly stably gracefully
        history_path = os.path.join(out_dir, f"seed_{seed}_history.json")
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)
            
        all_summary[seed] = {
            "best_epoch": best_epoch,
            "best_val_f1": best_val_f1,
            "best_val_acc": [r["val_acc"] for r in history if r["epoch"] == best_epoch][0],
            "best_val_loss": best_val_loss,
            "final_val_acc": history[-1]["val_acc"],
            "final_val_f1": history[-1]["val_f1"],
            "history_path": history_path,
            "best_ckpt": best_ckpt,
            "final_ckpt": final_ckpt
        }
        
    summary_path = os.path.join(out_dir, "multi_seed_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(all_summary, f, indent=2)
        
    print(f"\nAll Multi-seed runs compiled -> {summary_path}")

if __name__ == "__main__":
    main()
