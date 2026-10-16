"""
SignVox SPOTER V3 Dataset and DataLoader
Supports canonical 100-class vocabulary indexing (0-99).
Strictly signer-independent split filtering.
Dynamic sequence padding and attention mask generation.
"""

import os
import json
import csv
import random
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Optional, Tuple

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def get_feature_channel_indices():
    """
    Returns channel slices for canonical 366-D SignVox landmark vectors:
    - Left hand: 0-62 (21 landmarks * 3 coordinates)
    - Right hand: 63-125 (21 landmarks * 3 coordinates)
    - Pose XYZ: 126-224 (33 landmarks * 3 xyz coordinates out of 5 attributes)
    - Face: 291-365 (25 key landmarks * 3 coordinates)
    """
    lh_idx = list(range(0, 63))
    rh_idx = list(range(63, 126))
    pose_xyz_idx = [126 + i * 5 + j for i in range(33) for j in range(3)]
    face_idx = list(range(291, 366))
    return lh_idx, rh_idx, pose_xyz_idx, face_idx

def compute_groupnorm_scalars(train_loader: DataLoader) -> Dict[str, float]:
    """
    Computes empirical standard deviation scaling factors on the training set
    to normalize spatial landmark coordinates across body groups.
    """
    lh_idx, rh_idx, pose_xyz_idx, face_idx = get_feature_channel_indices()
    lh_vals, rh_vals, pose_vals, face_vals = [], [], [], []
    
    for batch in train_loader:
        seqs = batch["padded_sequences"]
        lengths = batch["original_lengths"]
        
        for b in range(seqs.size(0)):
            l = lengths[b].item()
            valid_seq = seqs[b, :l, :]
            
            # Left Hand
            lh_active = (valid_seq[:, lh_idx].abs().sum(dim=1) > 0)
            if lh_active.sum() > 0:
                lh_vals.append(valid_seq[lh_active][:, lh_idx].flatten())
                
            # Right Hand
            rh_active = (valid_seq[:, rh_idx].abs().sum(dim=1) > 0)
            if rh_active.sum() > 0:
                rh_vals.append(valid_seq[rh_active][:, rh_idx].flatten())
                
            # Pose XYZ
            pose_active = (valid_seq[:, pose_xyz_idx].abs().sum(dim=1) > 0)
            if pose_active.sum() > 0:
                pose_vals.append(valid_seq[pose_active][:, pose_xyz_idx].flatten())
                
            # Face
            face_active = (valid_seq[:, face_idx].abs().sum(dim=1) > 0)
            if face_active.sum() > 0:
                face_vals.append(valid_seq[face_active][:, face_idx].flatten())
                
    scalars = {
        "left_hand": float(torch.cat(lh_vals).std().item()) if lh_vals else 1.0,
        "right_hand": float(torch.cat(rh_vals).std().item()) if rh_vals else 1.0,
        "pose_xyz": float(torch.cat(pose_vals).std().item()) if pose_vals else 1.0,
        "face": float(torch.cat(face_vals).std().item()) if face_vals else 1.0
    }
    return scalars

def apply_groupnorm_scaling(seqs: torch.Tensor, scalars: Dict[str, float]) -> torch.Tensor:
    """
    Normalizes feature channels by the group-specific standard deviations.
    """
    lh_idx, rh_idx, pose_xyz_idx, face_idx = get_feature_channel_indices()
    scaled = seqs.clone().float()
    
    scaled[:, :, lh_idx] = scaled[:, :, lh_idx] / float(scalars.get("left_hand", 1.0))
    scaled[:, :, rh_idx] = scaled[:, :, rh_idx] / float(scalars.get("right_hand", 1.0))
    scaled[:, :, pose_xyz_idx] = scaled[:, :, pose_xyz_idx] / float(scalars.get("pose_xyz", 1.0))
    scaled[:, :, face_idx] = scaled[:, :, face_idx] / float(scalars.get("face", 1.0))
    return scaled

class SpoterV3Dataset(Dataset):
    def __init__(
        self,
        manifest_path: str,
        features_dir: str,
        mapping_path: str,
        split: str = "train"
    ):
        self.split = split
        self.features_dir = features_dir
        
        # Load 100-class canonical mapping
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping_dict = json.load(f)
            
        self.asl_to_index = {
            asl_id: data["class_index"]
            for asl_id, data in mapping_dict.items()
        }
        
        self.samples = []
        with open(manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("source_split", "").strip() == split:
                    asl_id = row.get("asl_id", "").strip()
                    if asl_id not in self.asl_to_index:
                        continue
                    
                    base_name = os.path.splitext(row["video_file"])[0]
                    npy_path = os.path.join(features_dir, f"{base_name}_features.npy")
                    
                    # Store sample if features file is present
                    if os.path.exists(npy_path):
                        self.samples.append({
                            "video_file": row["video_file"],
                            "npy_path": npy_path,
                            "class_index": self.asl_to_index[asl_id],
                            "asl_id": asl_id,
                            "canonical_name": row.get("canonical_name", ""),
                            "participant_id": row.get("participant_id", ""),
                            "source_split": row.get("source_split", "")
                        })
                        
        # Sort for deterministic sequence ordering
        self.samples.sort(key=lambda s: s["video_file"])

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = self.samples[idx]
        seq = np.load(item["npy_path"])
        
        # Sanity check
        if np.isnan(seq).any() or np.isinf(seq).any():
            raise ValueError(f"Corrupted features encountered in {item['video_file']}")
            
        seq_tensor = torch.tensor(seq, dtype=torch.float32)
        return {
            "sequence": seq_tensor,
            "class_index": torch.tensor(item["class_index"], dtype=torch.long),
            "asl_id": item["asl_id"],
            "canonical_name": item["canonical_name"],
            "participant_id": item["participant_id"],
            "source_split": item["source_split"],
            "length": len(seq_tensor)
        }

def spoter_v3_collate_fn(batch: List[Dict]) -> Dict[str, torch.Tensor]:
    sequences = [item["sequence"] for item in batch]
    class_indices = torch.stack([item["class_index"] for item in batch])
    lengths = torch.tensor([item["length"] for item in batch], dtype=torch.long)
    
    asl_ids = [item["asl_id"] for item in batch]
    canonical_names = [item["canonical_name"] for item in batch]
    participant_ids = [item["participant_id"] for item in batch]
    source_splits = [item["source_split"] for item in batch]
    
    # Pad dynamically to max length within batch
    padded_seqs = torch.nn.utils.rnn.pad_sequence(sequences, batch_first=True, padding_value=0.0)
    
    # Attention mask: True for valid frames, False for padding frames
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

def get_spoter_v3_dataloaders(
    manifest_path: str,
    features_dir: str,
    mapping_path: str,
    batch_size: int = 16,
    num_workers: int = 0
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    train_dataset = SpoterV3Dataset(manifest_path, features_dir, mapping_path, split="train")
    val_dataset = SpoterV3Dataset(manifest_path, features_dir, mapping_path, split="val")
    test_dataset = SpoterV3Dataset(manifest_path, features_dir, mapping_path, split="test")
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=spoter_v3_collate_fn,
        num_workers=num_workers
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=spoter_v3_collate_fn,
        num_workers=num_workers
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=spoter_v3_collate_fn,
        num_workers=num_workers
    )
    return train_loader, val_loader, test_loader
