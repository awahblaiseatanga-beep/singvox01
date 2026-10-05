import os, time, torch
from collections import defaultdict
import sys

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")

from spoter import Spoter
from dataloaders import get_dataloaders, set_seed

def apply_group_norm(padded_seqs, lengths):
    out = padded_seqs.clone()
    groups = {"LH": (0, 63), "RH": (63, 126), "POSE": (126, 291), "FACE": (291, 366)}
    
    mask = (out != 0.0)
    for g_name, (start, end) in groups.items():
        block = out[:, :, start:end]
        b_mask = mask[:, :, start:end]
        
        b_sum = (block * b_mask).sum(dim=(1, 2), keepdim=True)
        b_count = b_mask.sum(dim=(1, 2), keepdim=True).clamp(min=1)
        mean = b_sum / b_count
        
        var_sum = (((block - mean) * b_mask) ** 2).sum(dim=(1, 2), keepdim=True)
        std = torch.sqrt(var_sum / b_count)
        
        valid_std = std.clamp(min=1e-6)
        out[:, :, start:end] = torch.where(b_mask, (block - mean) / valid_std, block)
        
    return out

print("Starting speed test...")
manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
train_loader, val_loader, test_loader = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)

t0 = time.time()
b = next(iter(train_loader))
t1 = time.time()
print(f"Data batch load took {t1-t0:.4f}s")

t0 = time.time()
for _ in range(10):
    seqs = apply_group_norm(b["padded_sequences"], b["original_lengths"])
t1 = time.time()
print(f"10 apply_group_norm took {t1-t0:.4f}s")

model = Spoter(num_classes=79, hidden_dim=512, nhead=8, num_encoder_layers=6, num_decoder_layers=6, dim_feedforward=2048, dropout=0.1)

t0 = time.time()
for _ in range(10):
    out = model(seqs, attention_mask=b["attention_mask"])
t1 = time.time()
print(f"10 forwards took {t1-t0:.4f}s")
