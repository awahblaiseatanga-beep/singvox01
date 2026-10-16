import sys
import os
import re
import math
import json
import random
from pathlib import Path
from collections import Counter
import numpy as np
import torch
import torch.nn as nn

torch.set_num_threads(1)

base_dir = Path(r"d:\Singvox\Singvox")
exp27_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_27"
exp26_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_26"
exp29_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_29"
exp29_dir.mkdir(parents=True, exist_ok=True)

sys.path.append(str(exp27_dir))
from model import LandmarkEncoder, AttentionDecoder, AttentionSeq2Seq
from dataset import How2SignAttentionDataset
from tokenizer import BPETokenizer

class FrozenPhase27Model(AttentionSeq2Seq):
    def __init__(self, vocab_size, in_features=366, hidden_dim=256, embed_dim=128, attn_dim=128, pad_id=0, sos_id=1, eos_id=2, dropout=0.2):
        super().__init__(vocab_size, in_features, hidden_dim, embed_dim, attn_dim, pad_id, sos_id, eos_id, dropout)
        self.encoder = LandmarkEncoder(in_features=in_features, hidden_dim=hidden_dim, num_layers=2, dropout=dropout)
        self.decoder = AttentionDecoder(vocab_size=vocab_size, embed_dim=embed_dim, enc_dim=hidden_dim, dec_dim=hidden_dim, attn_dim=attn_dim, pad_id=pad_id, dropout=dropout)

def normalize_text(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s']", " ", text)
    return " ".join(text.split())

def compute_ngrams(tokens, n):
    return Counter([tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)])

def compute_bleu(references, hypotheses, max_n=4):
    precisions = [[] for _ in range(max_n)]
    c_len = 0
    r_len = 0
    
    for ref_str, hyp_str in zip(references, hypotheses):
        ref_tokens = normalize_text(ref_str).split()
        hyp_tokens = normalize_text(hyp_str).split()
        
        c_len += len(hyp_tokens)
        r_len += len(ref_tokens)
        
        for n in range(1, max_n + 1):
            hyp_ngrams = compute_ngrams(hyp_tokens, n)
            ref_ngrams = compute_ngrams(ref_tokens, n)
            
            numerator = sum(min(count, ref_ngrams[ng]) for ng, count in hyp_ngrams.items())
            denominator = max(1, len(hyp_tokens) - n + 1)
            
            if numerator == 0:
                p = 0.1 / denominator
            else:
                p = numerator / denominator
            precisions[n - 1].append(p)
            
    if c_len == 0:
        return {"bleu1": 0.0, "bleu2": 0.0, "bleu4": 0.0, "bp": 0.0}
        
    bp = 1.0 if c_len > r_len else math.exp(1.0 - r_len / max(1, c_len))
    avg_p = [float(np.mean(precisions[i])) for i in range(max_n)]
    
    b1 = bp * avg_p[0] * 100.0
    b2 = bp * math.exp(0.5 * math.log(max(1e-9, avg_p[0])) + 0.5 * math.log(max(1e-9, avg_p[1]))) * 100.0
    log_sum = sum(0.25 * math.log(max(1e-9, avg_p[i])) for i in range(4))
    b4 = bp * math.exp(log_sum) * 100.0
    
    return {
        "bleu1": round(b1, 2),
        "bleu2": round(b2, 2),
        "bleu4": round(b4, 2),
        "bp": round(bp, 4)
    }

def has_repetition(tokens):
    if len(tokens) < 4:
        return False
    for i in range(len(tokens) - 2):
        if tokens[i] == tokens[i+1] == tokens[i+2]:
            return True
    for i in range(len(tokens) - 3):
        if tokens[i:i+2] == tokens[i+2:i+4]:
            return True
    return False

def analyze_generation(references, hypotheses):
    total = len(references)
    exact_matches = 0
    ref_lens = []
    hyp_lens = []
    repetition_flags = []

    for ref_str, hyp_str in zip(references, hypotheses):
        ref_tokens = normalize_text(ref_str).split()
        hyp_tokens = normalize_text(hyp_str).split()
        ref_lens.append(len(ref_tokens))
        hyp_lens.append(len(hyp_tokens))

        if normalize_text(ref_str) == normalize_text(hyp_str):
            exact_matches += 1

        repetition_flags.append(has_repetition(hyp_tokens))

    bleu_stats = compute_bleu(references, hypotheses)
    return {
        "bleu_1": bleu_stats["bleu1"],
        "bleu_2": bleu_stats["bleu2"],
        "bleu_4": bleu_stats["bleu4"],
        "bp": bleu_stats["bp"],
        "exact_match_pct": round(exact_matches / max(1, total) * 100.0, 2),
        "mean_ref_len": round(float(np.mean(ref_lens)), 2),
        "mean_hyp_len": round(float(np.mean(hyp_lens)), 2),
        "repetition_rate_pct": round(sum(repetition_flags) / max(1, total) * 100.0, 2),
        "sample_count": total
    }

def run_baseline_evaluation():
    manifest_path = exp26_dir / "dataset_manifest.csv"
    feat_dir = exp26_dir / "features"
    tok_path = exp27_dir / "tokenizer.json"
    model_path = exp27_dir / "best_attention_model.pt"

    tokenizer = BPETokenizer.load(tok_path)
    vocab_size = len(tokenizer.token2id)

    model = FrozenPhase27Model(
        vocab_size=vocab_size,
        in_features=366,
        hidden_dim=256,
        embed_dim=128,
        attn_dim=128,
        pad_id=tokenizer.pad_id,
        sos_id=tokenizer.sos_id,
        eos_id=tokenizer.eos_id,
        dropout=0.2
    )
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    val_dataset = How2SignAttentionDataset(manifest_path, feat_dir, tokenizer, split="val", max_frames=150)
    N = len(val_dataset)
    print(f"Loaded validation set: {N} samples.")

    refs = []
    features_list = []
    masks_list = []

    for i in range(N):
        sample = val_dataset[i]
        feat = sample["features"].unsqueeze(0)
        mask = torch.ones((1, feat.size(1)), dtype=torch.bool)
        refs.append(sample["sentence"])
        features_list.append(feat)
        masks_list.append(mask)

    def generate_all(feats, masks):
        hyps = []
        with torch.no_grad():
            for f, m in zip(feats, masks):
                tokens = model.generate(f, m, max_len=50)
                if isinstance(tokens, torch.Tensor):
                    int_tokens = tokens.squeeze().tolist()
                    if isinstance(int_tokens, int):
                        int_tokens = [int_tokens]
                elif isinstance(tokens, list):
                    int_tokens = [t.item() if isinstance(t, torch.Tensor) else int(t) for t in tokens]
                else:
                    int_tokens = list(tokens)
                hyps.append(tokenizer.decode(int_tokens, skip_special_tokens=True))
        return hyps

    print("Evaluating Condition 1: Normal Validation Videos...")
    normal_hyps = generate_all(features_list, masks_list)
    normal_metrics = analyze_generation(refs, normal_hyps)

    print("Evaluating Condition 2: Zeroed Landmark Features...")
    zero_feats = [torch.zeros_like(f) for f in features_list]
    zero_hyps = generate_all(zero_feats, masks_list)
    zero_metrics = analyze_generation(refs, zero_hyps)

    print("Evaluating Condition 3: Shuffled-Frame Features...")
    shuff_feats = []
    for f in features_list:
        T = f.size(1)
        perm = torch.randperm(T)
        shuff_feats.append(f[:, perm, :])
    shuff_hyps = generate_all(shuff_feats, masks_list)
    shuff_metrics = analyze_generation(refs, shuff_hyps)

    shuff_ident = sum(1 for h1, h2 in zip(normal_hyps, shuff_hyps) if normalize_text(h1) == normalize_text(h2)) / N * 100.0

    print("Evaluating Condition 4: Mismatched-Video References (Seed 42)...")
    rng = random.Random(42)
    shift = rng.randint(1, N - 1)
    mismatched_refs = [refs[(i + shift) % N] for i in range(N)]
    mismatched_metrics = analyze_generation(mismatched_refs, normal_hyps)

    baseline_data = {
        "checkpoint": str(model_path),
        "total_parameters": sum(p.numel() for p in model.parameters()),
        "validation_samples": N,
        "conditions": {
            "normal": normal_metrics,
            "zeroed": zero_metrics,
            "shuffled": shuff_metrics,
            "mismatched": mismatched_metrics
        },
        "temporal_dependence": {
            "shuffled_identical_output_pct": round(shuff_ident, 2)
        },
        "sample_comparisons": [
            {
                "idx": i,
                "ref": refs[i],
                "hyp_normal": normal_hyps[i],
                "hyp_shuffled": shuff_hyps[i],
                "hyp_zeroed": zero_hyps[i]
            }
            for i in range(5)
        ]
    }

    out_file = exp29_dir / "baseline_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(baseline_data, f, indent=2)
    print(f"Saved baseline results to {out_file}")
    print("\n================= PHASE 2C.27 BASELINE VERIFIED =================")
    print(f"Normal Input:     BLEU-1={normal_metrics['bleu_1']}%, BLEU-4={normal_metrics['bleu_4']}%, Repetition={normal_metrics['repetition_rate_pct']}%, Mean Hyp Len={normal_metrics['mean_hyp_len']}")
    print(f"Zeroed Input:     BLEU-1={zero_metrics['bleu_1']}%, BLEU-4={zero_metrics['bleu_4']}%, Repetition={zero_metrics['repetition_rate_pct']}%, Mean Hyp Len={zero_metrics['mean_hyp_len']}")
    print(f"Shuffled Input:   BLEU-1={shuff_metrics['bleu_1']}%, Shuffled Output Identity={shuff_ident:.2f}%")
    print(f"Mismatched Pair:  BLEU-1={mismatched_metrics['bleu_1']}%, BLEU-4={mismatched_metrics['bleu_4']}%")
    print("==================================================================")

if __name__ == "__main__":
    run_baseline_evaluation()
