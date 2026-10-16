import csv
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import Dataset

class How2SignAttentionDataset(Dataset):
    def __init__(self, manifest_path, features_dir, tokenizer, split="train", max_frames=600):
        self.features_dir = Path(features_dir)
        self.tokenizer = tokenizer
        self.split = split
        self.max_frames = max_frames
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            all_rows = list(reader)
            
        self.samples = []
        for r in all_rows:
            if r["SPLIT"] != split:
                continue
            name = r["SENTENCE_NAME"]
            feat_path = self.features_dir / f"{name}.npy"
            if feat_path.exists():
                self.samples.append({
                    "name": name,
                    "feat_path": feat_path,
                    "sentence": r["SENTENCE"],
                    "video_id": r["VIDEO_ID"]
                })
                
        print(f"Loaded {len(self.samples)} active samples for split '{split}'.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]
        arr = np.load(item["feat_path"]).astype(np.float32)
        
        # Clip long sequences if exceeding max_frames
        if arr.shape[0] > self.max_frames:
            arr = arr[:self.max_frames]
            
        token_ids = self.tokenizer.encode(item["sentence"], add_special_tokens=True)
        
        return {
            "name": item["name"],
            "features": torch.from_numpy(arr), # [T, 366]
            "tokens": torch.tensor(token_ids, dtype=torch.long),
            "sentence": item["sentence"],
            "video_id": item["video_id"]
        }

def attention_collate_fn(batch, pad_token_id=0):
    batch_size = len(batch)
    
    # Sort by source sequence length descending for efficient RNN packing if needed
    batch = sorted(batch, key=lambda x: x["features"].shape[0], reverse=True)
    
    src_lens = [x["features"].shape[0] for x in batch]
    tgt_lens = [len(x["tokens"]) for x in batch]
    
    max_src_len = max(src_lens)
    max_tgt_len = max(tgt_lens)
    
    # Allocate padded tensors
    padded_src = torch.zeros(batch_size, max_src_len, 366, dtype=torch.float32)
    src_mask = torch.zeros(batch_size, max_src_len, dtype=torch.bool) # True = valid, False = pad
    
    padded_tgt = torch.full((batch_size, max_tgt_len), pad_token_id, dtype=torch.long)
    
    names = []
    sentences = []
    video_ids = []
    
    for i, item in enumerate(batch):
        t = item["features"].shape[0]
        padded_src[i, :t, :] = item["features"]
        src_mask[i, :t] = True
        
        l = len(item["tokens"])
        padded_tgt[i, :l] = item["tokens"]
        
        names.append(item["name"])
        sentences.append(item["sentence"])
        video_ids.append(item["video_id"])
        
    return {
        "src": padded_src,                # [B, T_src, 366]
        "src_lens": torch.tensor(src_lens, dtype=torch.long),
        "src_mask": src_mask,             # [B, T_src] (True = real, False = pad)
        "tgt": padded_tgt,                # [B, T_tgt]
        "tgt_lens": torch.tensor(tgt_lens, dtype=torch.long),
        "names": names,
        "sentences": sentences,
        "video_ids": video_ids
    }
