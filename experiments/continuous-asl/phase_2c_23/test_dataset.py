import sys
from pathlib import Path
import torch
from torch.utils.data import DataLoader

sys.path.append(str(Path(__file__).resolve().parent))
from config import SANDBOX_CSV_PATH, FEATURES_DIR
from dataset import ContinuousASLDataset, continuous_collate_fn

def test_dataset():
    print("=== Continuous Dataset Validation ===")
    dataset = ContinuousASLDataset(SANDBOX_CSV_PATH, FEATURES_DIR)
    
    print("\n[1] Alignment Statistics:")
    print(f"Verified Extracted Samples: {dataset.stats['verified_count']}")
    print(f"Missing Arrays from Features: {dataset.stats['missing_arrays']}")
    print(f"Empty Sentences encountered: {dataset.stats['empty_sentences']}")
    print(f"Duplicate IDs: {dataset.stats['duplicate_ids']}")
    
    if dataset.stats['verified_count'] == 0:
        print("ERROR: No verifiable arrays loaded. Aborting tests.")
        return
        
    print("\n[2] Single Sample Fetch Test:")
    sample = dataset[0]
    print(f"Sentence Name: {sample['sentence_name']}")
    print(f"Original Sentence: {sample['sentence']}")
    features = sample['features']
    print(f"Feature Shape: {features.shape}, Expected: [T, 366]")
    assert features.ndim == 2 and features.size(1) == 366, "Shape mismatch"
    assert torch.isfinite(features).all(), "NaNs exist"
    
    print("\n[3] Variable-Length Collation & Batching Test:")
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True, collate_fn=continuous_collate_fn)
    
    batch = next(iter(dataloader))
    features_batch = batch['features']
    mask_batch = batch['mask']
    lengths_batch = batch['lengths']
    sentences_batch = batch['sentences']
    
    B, max_t, dim = features_batch.shape
    print(f"Batch Shape: {features_batch.shape}")
    print(f"Lengths: {lengths_batch.tolist()}")
    print(f"Mask Shape: {mask_batch.shape}")
    
    # Validation constraints
    assert dim == 366, "Batch dimension mismatch"
    assert B == min(4, len(dataset)), "Batch dimension B mismatch"
    assert max_t == max(lengths_batch), "Batch max_t should equal max length in batch"
    assert len(sentences_batch) == B, "Targets count mismatch"
    
    # Mask check
    for i, seq_len in enumerate(lengths_batch):
        assert mask_batch[i, :seq_len].all() == True, "Mask inside sequence length should be True"
        if seq_len < max_t:
            assert mask_batch[i, seq_len:].any() == False, "Mask outside sequence length should be False"
            # Ensure padding logic works correctly with 0.0 values natively
            assert torch.sum(features_batch[i, seq_len:]) == 0.0, "Padding region should sum to 0 organically"
            
    print("\n[4] Complete Iteration Loading:")
    count = 0
    for b in dataloader:
        count += len(b['sentence_names'])
    print(f"Total Batched Items Traversed: {count}")
    assert count == len(dataset), "Data loss during collation loop"
    
    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY.")

if __name__ == "__main__":
    test_dataset()
