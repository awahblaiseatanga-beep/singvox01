import os
import json
import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
import random
import csv

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

class SignVoxDataset(Dataset):
    def __init__(self, manifest_path, features_dir, mapping_path, split="train"):
        self.split = split
        self.features_dir = features_dir
        
        with open(mapping_path, 'r', encoding='utf-8') as f:
            mapping_dict = json.load(f)
            
        self.asl_to_index = {
            data["asl_id"]: data["class_index"] 
            for key, data in mapping_dict.items()
        }
        
        self.samples = []
        with open(manifest_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['source_split'] == split:
                    base_name = os.path.splitext(row['video_file'])[0]
                    npy_path = os.path.join(features_dir, f"{base_name}_features.npy")
                    if os.path.exists(npy_path):
                        self.samples.append({
                            "video_file": row['video_file'],
                            "npy_path": npy_path,
                            "class_index": self.asl_to_index[row['asl_id']],
                            "asl_id": row['asl_id'],
                            "canonical_name": row['canonical_name'],
                            "participant_id": row['participant_id'],
                            "source_split": row['source_split']
                        })
                        
        # Ensure deterministic ordering within split
        self.samples.sort(key=lambda x: x['video_file'])
        
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        item = self.samples[idx]
        seq = np.load(item['npy_path'])
        
        # Verify and cast gracefully
        if np.isnan(seq).any() or np.isinf(seq).any():
            raise ValueError(f"Corrupt data in {item['video_file']}")
            
        seq_tensor = torch.tensor(seq, dtype=torch.float32)
        return {
            "sequence": seq_tensor,
            "class_index": torch.tensor(item['class_index'], dtype=torch.long),
            "asl_id": item['asl_id'],
            "canonical_name": item['canonical_name'],
            "participant_id": item['participant_id'],
            "source_split": item['source_split'],
            "length": len(seq_tensor)
        }

def collate_fn(batch):
    sequences = [item['sequence'] for item in batch]
    class_indices = torch.stack([item['class_index'] for item in batch])
    lengths = torch.tensor([item['length'] for item in batch], dtype=torch.long)
    
    asl_ids = [item['asl_id'] for item in batch]
    canonical_names = [item['canonical_name'] for item in batch]
    participant_ids = [item['participant_id'] for item in batch]
    source_splits = [item['source_split'] for item in batch]
    
    # Pad variable-length sequences dynamically to maximum length within batch
    # Padding value is explicitly 0.0
    padded_seqs = torch.nn.utils.rnn.pad_sequence(sequences, batch_first=True, padding_value=0.0)
    
    # Create mask (True for actual spatial data, False for padding vector)
    batch_size = len(batch)
    max_len = padded_seqs.size(1)
    
    mask = torch.zeros((batch_size, max_len), dtype=torch.bool)
    for i, length in enumerate(lengths):
        mask[i, :length] = True
        
    return {
        "padded_sequences": padded_seqs,
        "attention_mask": mask,
        "class_indices": class_indices,
        "original_lengths": lengths,
        "asl_ids": asl_ids,
        "canonical_names": canonical_names,
        "participant_ids": participant_ids,
        "source_splits": source_splits
    }

def get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32, num_workers=0, seed=None):
    if seed is not None:
        set_seed(seed)
    
    train_dataset = SignVoxDataset(manifest_path, features_dir, mapping_path, split="train")
    val_dataset = SignVoxDataset(manifest_path, features_dir, mapping_path, split="val")
    test_dataset = SignVoxDataset(manifest_path, features_dir, mapping_path, split="test")
    
    # We create a torch generator to ensure the dataloader shuffle respects the requested seed if provided explicitly safely.
    g = torch.Generator()
    if seed is not None:
        g.manual_seed(seed)
    else:
        g.manual_seed(torch.initial_seed() % (2**32))
        
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn, num_workers=num_workers, generator=g)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn, num_workers=num_workers)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn, num_workers=num_workers)
    
    return train_loader, val_loader, test_loader

if __name__ == "__main__":
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    
    train_loader, val_loader, test_loader = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=8)
    
    report = {}
    for name, loader in [("train", train_loader), ("validation", val_loader), ("test", test_loader)]:
        batch = next(iter(loader))
        report[name] = {
            "batch_size": batch["padded_sequences"].shape[0],
            "padded_tensor_shape": list(batch["padded_sequences"].shape),
            "mask_shape": list(batch["attention_mask"].shape),
            "original_sequence_lengths": batch["original_lengths"].tolist(),
            "feature_dimension": batch["padded_sequences"].shape[2],
            "labels": batch["class_indices"].tolist(),
            "class_index_bounds": (int(batch["class_indices"].min()), int(batch["class_indices"].max()))
        }
    
    print(json.dumps(report, indent=2))
