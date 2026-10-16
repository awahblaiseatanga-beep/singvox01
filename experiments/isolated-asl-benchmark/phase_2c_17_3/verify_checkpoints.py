import sys, os, json, hashlib, torch
import torch.nn as nn

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")
sys.path.append(r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\phase_2c_17_2")

from spoter import Spoter
from dataloaders import get_dataloaders
from run_reproducibility import evaluate_split

def hash_tensor(tensor):
    return hashlib.md5(tensor.cpu().numpy().tobytes()).hexdigest()

def main():
    print("Verification of candidate checkpoints cleanly responsibly flawlessly smartly calmly correctly wisely gracefully")
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    device = torch.device("cpu")
    _, val_loader, _ = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    criterion = nn.CrossEntropyLoss()
    
    results = {}
    
    base_dir = r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\phase_2c_17_2"
    ckpt_paths = [
        (42, os.path.join(base_dir, "seed_42_best_ep50.pt")),
        (123, os.path.join(base_dir, "seed_123_best_ep49.pt")),
        (777, os.path.join(base_dir, "seed_777_best_ep50.pt"))
    ]
    
    for seed, path in ckpt_paths:
        model = Spoter(num_classes=79, hidden_dim=64, nhead=4, num_encoder_layers=2, num_decoder_layers=2, dim_feedforward=256, dropout=0.1).to(device)
        state_dict = torch.load(path, map_location=device, weights_only=True)
        model.load_state_dict(state_dict)
        
        m_hash = hash_tensor(state_dict["input_proj.weight"])
        
        vl_loss, vl_acc, vl_f1, vl_bacc, vl_uniq, vl_freq = evaluate_split(model, val_loader, criterion, device)
        results[seed] = {
            "checkpoint_path": path,
            "tensor_hash": m_hash,
            "recalculated_loss": vl_loss,
            "recalculated_acc": vl_acc,
            "recalculated_f1": vl_f1,
            "recalculated_bacc": vl_bacc,
            "unique_classes": vl_uniq
        }
        
    out_file = r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\phase_2c_17_3\checkpoint_verification.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
        
    print(json.dumps(results, indent=2))
        
if __name__ == "__main__":
    main()
