import os
import csv
import torch
import numpy as np
from pathlib import Path
from torch.utils.data import Dataset, DataLoader

class ContinuousASLDataset(Dataset):
    def __init__(self, csv_path, features_dir, feature_dim=366):
        self.csv_path = Path(csv_path)
        self.features_dir = Path(features_dir)
        self.feature_dim = feature_dim
        
        self.samples = []
        self._load_and_verify_data()
        
    def _load_and_verify_data(self):
        # We need to map every feature file to its English sentence using SENTENCE_NAME.
        # First gather all available features
        available_features = set()
        if self.features_dir.exists():
            for f in self.features_dir.glob("*.npy"):
                available_features.add(f.stem)
        
        verified_count = 0
        missing_arrays = []
        empty_sentences = 0
        duplicate_ids = set()
        seen_ids = set()
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                sentence_name = row.get("SENTENCE_NAME", "").strip()
                sentence = row.get("SENTENCE", "").strip()
                video_id = row.get("VIDEO_ID", "").strip()
                
                if not sentence_name:
                    continue
                
                if sentence_name in seen_ids:
                    duplicate_ids.add(sentence_name)
                    continue
                
                if sentence_name in available_features:
                    if not sentence:
                        empty_sentences += 1
                        continue
                    
                    seen_ids.add(sentence_name)
                    feature_path = self.features_dir / f"{sentence_name}.npy"
                    
                    self.samples.append({
                        "sentence_name": sentence_name,
                        "video_id": video_id,
                        "sentence": sentence,
                        "feature_path": feature_path
                    })
                    verified_count += 1
                
        # Reporting strictly within Dataset for validation
        self.stats = {
            "verified_count": verified_count,
            "missing_arrays": len(available_features) - verified_count, 
            "empty_sentences": empty_sentences,
            "duplicate_ids": len(duplicate_ids)
        }

    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        sample = self.samples[idx]
        feature_path = str(sample["feature_path"])
        
        # Load feature and verify shape natively
        features = np.load(feature_path).astype(np.float32) # [T, 366]
        
        if len(features.shape) != 2 or features.shape[1] != self.feature_dim:
            raise ValueError(f"Feature {sample['sentence_name']} has invalid shape {features.shape}. Expected [T, {self.feature_dim}].")

        # Check for NaNs/Infs
        if not np.isfinite(features).all():
             raise ValueError(f"Feature {sample['sentence_name']} contains NaN or Infinity.")
        
        return {
            "sentence_name": sample["sentence_name"],
            "video_id": sample["video_id"],
            "sentence": sample["sentence"],
            "features": torch.from_numpy(features), # [T, 366]
            "length": features.shape[0]
        }
        
def continuous_collate_fn(batch):
    """
    Collates a list of dataset samples into padded variable-length batches.
    
    Args:
        batch (list): List of dicts returned by __getitem__
        
    Returns:
        dict: padded features [B, max_T, 366], sequence lengths [B], 
              mask [B, max_T], original sentences [B], sentence_names [B]
    """
    sentence_names = [item["sentence_name"] for item in batch]
    sentences = [item["sentence"] for item in batch]
    video_ids = [item["video_id"] for item in batch]
    lengths = [item["length"] for item in batch]
    features_list = [item["features"] for item in batch]
    
    # Pad sequences to max_T in the batch
    # padded_features will be [B, max_T, 366]
    padded_features = torch.nn.utils.rnn.pad_sequence(features_list, batch_first=True, padding_value=0.0)
    
    batch_size, max_t, _ = padded_features.shape
    
    # Create mask [B, max_T] where True indicates real data, False indicates padded
    mask = torch.zeros((batch_size, max_t), dtype=torch.bool)
    for i, length in enumerate(lengths):
        mask[i, :length] = True
        
    return {
        "features": padded_features,     # [B, max_T, 366]
        "lengths": torch.tensor(lengths, dtype=torch.long), # [B]
        "mask": mask,                    # [B, max_T]
        "sentences": sentences,          # list of string
        "sentence_names": sentence_names,# list of string
        "video_ids": video_ids           # list of string
    }
