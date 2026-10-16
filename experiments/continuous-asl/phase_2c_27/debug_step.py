import sys
import traceback

try:
    print("Step 1: Imports...")
    import torch
    import torch.nn as nn
    from pathlib import Path
    sys.path.append(r"experiments/continuous-asl/phase_2c_27")
    from tokenizer import BPETokenizer
    from dataset import How2SignAttentionDataset, attention_collate_fn
    from model import AttentionSeq2Seq
    
    print("Step 2: Load Tokenizer...")
    base_dir = Path(r"d:\Singvox\Singvox")
    exp_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_27"
    exp26_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_26"
    tok = BPETokenizer.load(exp_dir / "tokenizer.json")
    
    print("Step 3: Load Dataset...")
    ds = How2SignAttentionDataset(exp26_dir / "dataset_manifest.csv", exp26_dir / "features", tok, split="train", max_frames=350)
    print(f"Dataset len: {len(ds)}")
    
    loader = torch.utils.data.DataLoader(ds, batch_size=4, shuffle=False, collate_fn=lambda b: attention_collate_fn(b, pad_token_id=0))
    batch = next(iter(loader))
    print(f"Batch loaded. src: {batch['src'].shape}, tgt: {batch['tgt'].shape}")
    
    print("Step 4: Model init...")
    model = AttentionSeq2Seq(len(tok.token2id), in_features=366, hidden_dim=256, embed_dim=128, attn_dim=128)
    
    print("Step 5: Forward pass...")
    logits = model(batch["src"], batch["src_mask"], batch["tgt"], teacher_forcing_ratio=0.5)
    print(f"Forward success! Logits: {logits.shape}")
    
    print("Step 6: Loss calculation...")
    criterion = nn.CrossEntropyLoss(ignore_index=0)
    loss = criterion(logits.view(-1, len(tok.token2id)), batch["tgt"][:, 1:].contiguous().view(-1))
    print(f"Loss: {loss.item():.4f}")
    
    print("Step 7: Backward pass...")
    loss.backward()
    print("Backward pass success!")
    
except Exception as e:
    print("EXCEPTION OCCURRED:")
    traceback.print_exc()
