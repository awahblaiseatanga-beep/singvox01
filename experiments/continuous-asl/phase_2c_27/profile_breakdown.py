import time
import torch
torch.set_num_threads(1)
from model import AttentionSeq2Seq

from dataset import How2SignAttentionDataset, attention_collate_fn
from tokenizer import BPETokenizer
from torch.utils.data import DataLoader
from pathlib import Path

base_dir = Path(r"d:\Singvox\Singvox")
exp_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_27"
exp26_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_26"
manifest_path = exp26_dir / "dataset_manifest.csv"
feat_dir = exp26_dir / "features"
tok_path = exp_dir / "tokenizer.json"

tokenizer = BPETokenizer.load(tok_path)
vocab_size = len(tokenizer.token2id)

train_dataset = How2SignAttentionDataset(manifest_path, feat_dir, tokenizer, split="train", max_frames=150)
loader = DataLoader(
    train_dataset,
    batch_size=16,
    shuffle=False,
    collate_fn=lambda b: attention_collate_fn(b, pad_token_id=tokenizer.pad_id)
)

model = AttentionSeq2Seq(
    vocab_size=vocab_size,
    in_features=366,
    hidden_dim=128,
    embed_dim=64,
    attn_dim=64,
    pad_id=tokenizer.pad_id,
    sos_id=tokenizer.sos_id,
    eos_id=tokenizer.eos_id,
    dropout=0.2
)

for batch in loader:
    src = batch["src"]
    src_mask = batch["src_mask"]
    tgt = batch["tgt"]
    break

# 1. Profile Encoder
t0 = time.time()
enc_outputs, dec_hidden = model.encoder(src)
t_enc = time.time() - t0
print(f"Encoder forward took: {t_enc:.4f}s", flush=True)

# 2. Profile Attention projection
t0 = time.time()
enc_proj = model.decoder.attention.w_enc(enc_outputs)
t_proj = time.time() - t0
print(f"w_enc projection took: {t_proj:.4f}s", flush=True)

# 3. Profile inv_mask
t0 = time.time()
inv_mask = ~src_mask if src_mask is not None else None
t_mask = time.time() - t0
print(f"inv_mask took: {t_mask:.4f}s", flush=True)

# 4. Profile Decoder loop breakdown
tgt_len = tgt.size(1)
input_tok = tgt[:, 0]

times_attn = []
times_gru = []
times_fc = []

for t in range(1, min(tgt_len, 6)):
    t_start = time.time()
    embed = model.decoder.dropout(model.decoder.embedding(input_tok))
    
    t_a = time.time()
    context, attn_weights = model.decoder.attention(dec_hidden, enc_outputs, enc_proj, inv_mask)
    times_attn.append(time.time() - t_a)
    
    t_g = time.time()
    gru_input = torch.cat([embed, context], dim=1)
    dec_hidden = model.decoder.gru_cell(gru_input, dec_hidden)
    times_gru.append(time.time() - t_g)
    
    t_f = time.time()
    out_cat = torch.cat([dec_hidden, embed, context], dim=1)
    logits = model.decoder.fc_out(out_cat)
    times_fc.append(time.time() - t_f)
    
    input_tok = tgt[:, t]
    print(f"Step {t}: attn={times_attn[-1]:.4f}s, gru={times_gru[-1]:.4f}s, fc={times_fc[-1]:.4f}s | step_total={time.time()-t_start:.4f}s", flush=True)

print("Done profile breakdown.", flush=True)
