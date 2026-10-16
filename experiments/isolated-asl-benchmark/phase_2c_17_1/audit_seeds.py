import os, sys, torch
import hashlib
import json

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")
from spoter import Spoter
from dataloaders import get_dataloaders

def hash_tensor(tensor):
    return hashlib.md5(tensor.cpu().numpy().tobytes()).hexdigest()

def hash_state_dict(state_dict):
    hashes = {}
    for k, v in state_dict.items():
        hashes[k] = hash_tensor(v)
    return hashes

def check_model_init(seed):
    torch.manual_seed(seed)
    model = Spoter(num_classes=79, hidden_dim=64, nhead=4, num_encoder_layers=2, num_decoder_layers=2, dim_feedforward=256, dropout=0.1)
    return hash_state_dict(model.state_dict())

def check_dataloader_batch(seed):
    torch.manual_seed(seed)
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    train_loader, _, _ = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    
    # Get first batch
    for batch in train_loader:
        labels = batch["class_indices"]
        return hash_tensor(labels)

def main():
    seeds = [42, 123, 777]
    out_dir = r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\phase_2c_17"
    
    results = {"ckpts": {}, "init_hashes": {}, "batch_hashes": {}}
    
    # 1. HASH CHECKPOINTS FROM 2C.17
    print("Checking Epoch 49 Best Checkpoints...")
    for seed in seeds:
        ckpt_path = os.path.join(out_dir, f"seed_{seed}_best_ep49.pt")
        state_dict = torch.load(ckpt_path, map_location='cpu', weights_only=True)
        # Just hash the linear projection layer and class query as a proxy
        results["ckpts"][seed] = {
            "class_query": hash_tensor(state_dict["class_query"]),
            "input_proj.weight": hash_tensor(state_dict["input_proj.weight"])
        }
        
    print("Checkpoint Hashes:", json.dumps(results["ckpts"], indent=2))
    
    # 2. CHECK MODEL INITS
    print("\nChecking Model Initialization Hashes via Spoter class...")
    for seed in seeds:
        init_hashes = check_model_init(seed)
        results["init_hashes"][seed] = {
            "class_query": init_hashes["class_query"],
            "input_proj.weight": init_hashes["input_proj.weight"]
        }
    print("Init Hashes:", json.dumps(results["init_hashes"], indent=2))
        
    # 3. CHECK DATALOADER SHUFFLE
    print("\nChecking Dataloader first batch hashes...")
    for seed in seeds:
        batch_hash = check_dataloader_batch(seed)
        results["batch_hashes"][seed] = batch_hash
    print("Batch Hashes:", json.dumps(results["batch_hashes"], indent=2))
    
    with open(r"d:\Singvox\Singvox\experiments\isolated-asl-benchmark\phase_2c_17_1\audit_seed_hashes.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
