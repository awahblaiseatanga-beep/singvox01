import sys
import os
import math
import json
import re
from pathlib import Path
from collections import Counter
import numpy as np
import torch
torch.set_num_threads(1)
from torch.utils.data import DataLoader

sys.path.append(r"experiments/continuous-asl/phase_2c_27")
from tokenizer import BPETokenizer
from dataset import How2SignAttentionDataset, attention_collate_fn
from model import AttentionSeq2Seq

def normalize_text(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s']", " ", text)
    return " ".join(text.split())

def compute_ngrams(tokens, n):
    return Counter([tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)])

def compute_bleu(references, hypotheses, max_n=4):
    """
    Computes corpus-level BLEU-1, BLEU-2, BLEU-4 with Chen & Cherry smoothing method 1.
    references: list of reference strings
    hypotheses: list of hypothesis strings
    """
    precisions = [[] for _ in range(max_n)]
    c_len = 0 # hypothesis length
    r_len = 0 # reference length
    
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
            
            # Smoothing method 1
            if numerator == 0:
                p = 0.1 / denominator
            else:
                p = numerator / denominator
            precisions[n - 1].append(p)
            
    # Brevity penalty
    if c_len == 0:
        return {"bleu1": 0.0, "bleu2": 0.0, "bleu4": 0.0, "bp": 0.0}
        
    bp = 1.0 if c_len > r_len else math.exp(1.0 - r_len / max(1, c_len))
    
    avg_p = [float(np.mean(precisions[i])) for i in range(max_n)]
    
    # BLEU-1
    b1 = bp * avg_p[0] * 100.0
    # BLEU-2
    b2 = bp * math.exp(0.5 * math.log(max(1e-9, avg_p[0])) + 0.5 * math.log(max(1e-9, avg_p[1]))) * 100.0
    # BLEU-4
    log_sum = sum(0.25 * math.log(max(1e-9, avg_p[i])) for i in range(4))
    b4 = bp * math.exp(log_sum) * 100.0
    
    return {
        "bleu1": round(b1, 2),
        "bleu2": round(b2, 2),
        "bleu4": round(b4, 2),
        "bp": round(bp, 4)
    }

def analyze_predictions(references, hypotheses):
    total = len(references)
    exact_matches = 0
    empty_outputs = 0
    repetitive_outputs = 0
    
    for ref, hyp in zip(references, hypotheses):
        norm_ref = normalize_text(ref)
        norm_hyp = normalize_text(hyp)
        
        if norm_ref == norm_hyp and norm_hyp != "":
            exact_matches += 1
            
        if norm_hyp == "":
            empty_outputs += 1
            
        toks = norm_hyp.split()
        if len(toks) >= 4:
            # Check 3 consecutive identical tokens
            for i in range(len(toks) - 2):
                if toks[i] == toks[i+1] == toks[i+2]:
                    repetitive_outputs += 1
                    break
                    
    bleu_stats = compute_bleu(references, hypotheses)
    
    return {
        "total_samples": total,
        "exact_match_count": exact_matches,
        "exact_match_pct": round(exact_matches / max(1, total) * 100.0, 2),
        "empty_output_count": empty_outputs,
        "empty_output_pct": round(empty_outputs / max(1, total) * 100.0, 2),
        "repetitive_output_count": repetitive_outputs,
        "repetitive_output_pct": round(repetitive_outputs / max(1, total) * 100.0, 2),
        "bleu1": bleu_stats["bleu1"],
        "bleu2": bleu_stats["bleu2"],
        "bleu4": bleu_stats["bleu4"],
        "brevity_penalty": bleu_stats["bp"]
    }

def run_evaluation():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Running evaluation on device: {device}")
    
    base_dir = Path(r"d:\Singvox\Singvox")
    exp_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_27"
    exp26_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_26"
    manifest_path = exp26_dir / "dataset_manifest.csv"
    feat_dir = exp26_dir / "features"
    tok_path = exp_dir / "tokenizer.json"
    model_path = exp_dir / "best_attention_model.pt"
    
    tokenizer = BPETokenizer.load(tok_path)
    vocab_size = len(tokenizer.token2id)
    
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
    ).to(device)
    
    if not model_path.exists():
        print(f"ERROR: Model checkpoint {model_path} not found!")
        return
        
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    print(f"Loaded trained attention model from {model_path}")
    
    # Helper to evaluate with probe
    def eval_split_with_probe(split_name, probe="original"):
        ds = How2SignAttentionDataset(manifest_path, feat_dir, tokenizer, split=split_name, max_frames=150)
        if len(ds) == 0:
            return None, [], []
            
        loader = DataLoader(
            ds,
            batch_size=16,
            shuffle=False,
            collate_fn=lambda b: attention_collate_fn(b, pad_token_id=tokenizer.pad_id)
        )
        
        all_refs = []
        all_hyps = []
        
        with torch.no_grad():
            for batch in loader:
                src = batch["src"].to(device)
                src_mask = batch["src_mask"].to(device)
                b_size = src.size(0)
                
                # Apply probe
                if probe == "zeroed":
                    src = torch.zeros_like(src)
                elif probe == "shuffled":
                    for b in range(b_size):
                        valid_t = int(batch["src_lens"][b])
                        if valid_t > 1:
                            perm = torch.randperm(valid_t)
                            src[b, :valid_t] = src[b, perm]
                elif probe == "mismatched":
                    if b_size > 1:
                        # Roll features by 1 so sample i gets features of sample i+1
                        src = torch.roll(src, shifts=1, dims=0)
                        src_mask = torch.roll(src_mask, shifts=1, dims=0)
                        
                gen_tokens = model.generate(src, src_mask, max_len=60)
                
                for i in range(b_size):
                    tok_ids = gen_tokens[i].tolist()
                    decoded_text = tokenizer.decode(tok_ids, skip_special_tokens=True)
                    all_refs.append(batch["sentences"][i])
                    all_hyps.append(decoded_text)
                    
        stats = analyze_predictions(all_refs, all_hyps)
        return stats, all_refs, all_hyps

    results = {}
    
    # 1. Standard Validation and Test evaluation
    print("\nEvaluating Standard Validation Split...")
    val_stats, val_refs, val_hyps = eval_split_with_probe("val", "original")
    results["val_standard"] = val_stats
    print(f"  Val BLEU-1: {val_stats['bleu1'] if val_stats else 'N/A'}% | BLEU-4: {val_stats['bleu4'] if val_stats else 'N/A'}% | Exact Match: {val_stats['exact_match_pct'] if val_stats else 'N/A'}%")
    
    print("\nEvaluating Standard Test Split...")
    test_stats, test_refs, test_hyps = eval_split_with_probe("test", "original")
    results["test_standard"] = test_stats
    print(f"  Test BLEU-1: {test_stats['bleu1'] if test_stats else 'N/A'}% | BLEU-4: {test_stats['bleu4'] if test_stats else 'N/A'}% | Exact Match: {test_stats['exact_match_pct'] if test_stats else 'N/A'}%")
    
    # 2. Visual Grounding Probes on Validation Set
    probes = ["zeroed", "shuffled", "mismatched"]
    probe_results = {}
    
    print("\nRunning Controlled Visual Grounding Probes...")
    for p in probes:
        p_stats, _, p_hyps = eval_split_with_probe("val", probe=p)
        probe_results[p] = p_stats
        print(f"  Probe [{p}]: BLEU-1={p_stats['bleu1'] if p_stats else 'N/A'}% | BLEU-4={p_stats['bleu4'] if p_stats else 'N/A'}% | Exact Match={p_stats['exact_match_pct'] if p_stats else 'N/A'}%")
        
    results["probes"] = probe_results
    
    # Sample predictions
    sample_preds = []
    if val_refs and val_hyps:
        for idx in range(min(8, len(val_refs))):
            sample_preds.append({
                "sample_idx": idx,
                "reference": val_refs[idx],
                "hypothesis": val_hyps[idx]
            })
    results["sample_predictions"] = sample_preds
    
    out_eval = exp_dir / "evaluation_results.json"
    with open(out_eval, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved evaluation results and probes to {out_eval}")

if __name__ == "__main__":
    run_evaluation()
