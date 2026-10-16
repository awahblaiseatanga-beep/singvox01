import os
import sys
import json
import csv
import torch
import numpy as np
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PHASE_24_DIR = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_24"
PHASE_23_DIR = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_23"
PHASE_22_DIR = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_22"
FEATURES_DIR = PHASE_22_DIR / "features"

sys.path.append(str(PHASE_24_DIR))
sys.path.append(str(PHASE_23_DIR))

from tokenizer import SimpleWordTokenizer
from model import Seq2Seq

def analyze_splits_and_vocab():
    print("=" * 60)
    print("1. SPLIT AND VOCABULARY AUDIT")
    print("=" * 60)
    
    tokenizer = SimpleWordTokenizer()
    tokenizer.load()
    train_vocab = set(tokenizer.word2id.keys())
    print(f"Train Vocab Size: {len(train_vocab)} (including 4 special tokens)")
    
    splits = {}
    for split_name in ["train", "val", "test"]:
        csv_file = PHASE_24_DIR / f"{split_name}.csv"
        rows = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for r in reader:
                rows.append(r)
        splits[split_name] = rows
        
    for split_name, rows in splits.items():
        vids = Counter(r["VIDEO_ID"] for r in rows)
        word_counts = []
        frame_counts = []
        all_words = []
        oov_words = []
        
        for r in rows:
            s = r["SENTENCE"]
            words = tokenizer._normalize(s)
            word_counts.append(len(words))
            all_words.extend(words)
            for w in words:
                if w not in tokenizer.word2id:
                    oov_words.append(w)
                    
            feat_file = FEATURES_DIR / f"{r['SENTENCE_NAME']}.npy"
            if feat_file.exists():
                arr = np.load(feat_file)
                frame_counts.append(arr.shape[0])
            else:
                frame_counts.append(0)
                
        oov_rate = len(oov_words) / max(1, len(all_words))
        unique_oov = set(oov_words)
        print(f"\n--- Split: {split_name.upper()} ---")
        print(f"Total Sentences: {len(rows)}")
        print(f"Unique Video IDs ({len(vids)}): {dict(vids)}")
        print(f"Sentence Length (words): min={min(word_counts)}, max={max(word_counts)}, mean={np.mean(word_counts):.1f}, median={np.median(word_counts):.1f}")
        print(f"Feature Sequence Length (frames): min={min(frame_counts)}, max={max(frame_counts)}, mean={np.mean(frame_counts):.1f}, median={np.median(frame_counts):.1f}")
        print(f"Total Words: {len(all_words)}, Unique Words: {len(set(all_words))}")
        print(f"OOV Word Tokens: {len(oov_words)} / {len(all_words)} ({oov_rate * 100:.1f}%)")
        print(f"Unique OOV Words: {len(unique_oov)}")
        if unique_oov:
            sample_oov = list(unique_oov)[:10]
            print(f"Sample OOV Words: {sample_oov}")

def analyze_model_and_probes():
    print("\n" + "=" * 60)
    print("2. MODEL IMPLEMENTATION AND ZERO-INPUT PROBING")
    print("=" * 60)
    
    tokenizer = SimpleWordTokenizer()
    tokenizer.load()
    
    device = torch.device("cpu")
    model = Seq2Seq(
        input_dim=366,
        enc_hidden=128,
        dec_hidden=256,
        vocab_size=tokenizer.vocab_size,
        embed_dim=128
    ).to(device)
    
    ckpt_path = PHASE_24_DIR / "seq2seq_checkpoint.pt"
    if ckpt_path.exists():
        model.load_state_dict(torch.load(ckpt_path, map_location=device))
        print("Loaded trained checkpoint successfully.")
    else:
        print("Checkpoint not found!")
        return
        
    model.eval()
    
    # Probe 1: Zero input features
    print("\n--- Probe 1: Zero input features [1, 100, 366] ---")
    zero_feat = torch.zeros((1, 100, 366), dtype=torch.float32)
    zero_len = torch.tensor([100], dtype=torch.long)
    zero_tokens = model.decode_greedy(zero_feat, zero_len, max_len=30, sos_id=tokenizer.sos_id, eos_id=tokenizer.eos_id)
    zero_pred = tokenizer.decode(zero_tokens[0].tolist())
    print(f"Prediction from all zeros: '{zero_pred}'")
    print(f"Raw Token IDs: {zero_tokens[0].tolist()[:15]}")
    
    # Probe 2: Random noise input features
    print("\n--- Probe 2: Random noise features [1, 100, 366] ---")
    torch.manual_seed(42)
    noise_feat = torch.randn((1, 100, 366), dtype=torch.float32)
    noise_len = torch.tensor([100], dtype=torch.long)
    noise_tokens = model.decode_greedy(noise_feat, noise_len, max_len=30, sos_id=tokenizer.sos_id, eos_id=tokenizer.eos_id)
    noise_pred = tokenizer.decode(noise_tokens[0].tolist())
    print(f"Prediction from random noise: '{noise_pred}'")
    
    # Probe 3: Check across several training samples vs val samples
    print("\n--- Probe 3: Train vs Val Predictions Distribution ---")
    eval_json = PHASE_24_DIR / "evaluation_results.json"
    if eval_json.exists():
        with open(eval_json, 'r') as f:
            eval_data = json.load(f)
            
        for split in ["train", "val", "test"]:
            preds = [ex["pred"] for ex in eval_data[split]["examples"]]
            print(f"\n{split.upper()} Predictions Sample:")
            for i, p in enumerate(preds):
                print(f"  [{i+1}] '{p}'")

def audit_code_mechanics():
    print("\n" + "=" * 60)
    print("3. CODE MECHANICS & ARCHITECTURE AUDIT")
    print("=" * 60)
    
    # Let's inspect model.py and train.py code properties
    from model import Seq2Seq
    m = Seq2Seq(input_dim=366, enc_hidden=128, dec_hidden=256, vocab_size=366, embed_dim=128)
    total_params = sum(p.numel() for p in m.parameters())
    print(f"Model Total Parameters: {total_params:,}")
    print(f"Encoder Parameters: {sum(p.numel() for p in m.encoder.parameters()):,}")
    print(f"Bridge Parameters: {sum(p.numel() for p in m.bridge.parameters()):,}")
    print(f"Decoder GRU Parameters: {sum(p.numel() for p in m.decoder.parameters()):,}")
    print(f"Decoder FC_Out Parameters: {sum(p.numel() for p in m.fc_out.parameters()):,}")
    
    print("\nArchitecture observations:")
    print(" - Input sequence compression: Entire [T, 366] sequence is collapsed into a single [1, B, 256] hidden state via bidirectional GRU last hidden state.")
    print(" - Attention mechanism: NONE. Information bottleneck is severe (T ranges up to 200+ frames).")
    print(" - Autoregressive decoder: At inference, Greedy decoding without EOS early termination in decode_greedy loop (it iterates fixed max_len=30, decode() trims after EOS).")
    print(" - Teacher forcing: ratio 0.5 in train, but tiny dataset (61 sentences) causes strong LM memorization of the dominant sentence pattern.")

if __name__ == "__main__":
    analyze_splits_and_vocab()
    analyze_model_and_probes()
    audit_code_mechanics()
