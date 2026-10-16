import sys
import os
import re
import math
import time
import json
import random
from pathlib import Path
from collections import Counter
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.set_num_threads(1)

base_dir = Path(r"d:\Singvox\Singvox")
exp27_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_27"
exp26_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_26"
exp29_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_29"

sys.path.append(str(exp27_dir))
sys.path.append(str(exp29_dir))

from dataset import How2SignAttentionDataset
from tokenizer import BPETokenizer
from model import JointCTCAttentionModel

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
            
            p = 0.1 / denominator if numerator == 0 else numerator / denominator
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

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            insert = prev[j + 1] + 1
            delete = curr[j] + 1
            sub = prev[j] + (0 if c1 == c2 else 1)
            curr.append(min(insert, delete, sub))
        prev = curr
    return prev[-1]

def compute_token_accuracy(references, hypotheses):
    """
    Computes Levenshtein token similarity and unigram F1 score.
    """
    lev_similarities = []
    precisions = []
    recalls = []

    for ref_str, hyp_str in zip(references, hypotheses):
        ref_tokens = normalize_text(ref_str).split()
        hyp_tokens = normalize_text(hyp_str).split()

        max_len = max(len(ref_tokens), len(hyp_tokens), 1)
        dist = levenshtein_distance(ref_tokens, hyp_tokens)
        sim = max(0.0, 1.0 - (dist / max_len))
        lev_similarities.append(sim)

        ref_cnt = Counter(ref_tokens)
        hyp_cnt = Counter(hyp_tokens)
        overlap = sum(min(count, hyp_cnt[t]) for t, count in ref_cnt.items())
        p = overlap / max(1, len(hyp_tokens))
        r = overlap / max(1, len(ref_tokens))
        precisions.append(p)
        recalls.append(r)

    mean_p = float(np.mean(precisions))
    mean_r = float(np.mean(recalls))
    f1 = 2 * mean_p * mean_r / max(1e-9, mean_p + mean_r)

    return {
        "levenshtein_token_accuracy_pct": round(float(np.mean(lev_similarities)) * 100.0, 2),
        "token_precision_pct": round(mean_p * 100.0, 2),
        "token_recall_pct": round(mean_r * 100.0, 2),
        "token_f1_pct": round(f1 * 100.0, 2)
    }

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
    token_stats = compute_token_accuracy(references, hypotheses)

    return {
        "bleu_1": bleu_stats["bleu1"],
        "bleu_2": bleu_stats["bleu2"],
        "bleu4": bleu_stats["bleu4"],
        "bp": bleu_stats["bp"],
        "exact_match_pct": round(exact_matches / max(1, total) * 100.0, 2),
        "mean_ref_len": round(float(np.mean(ref_lens)), 2),
        "mean_hyp_len": round(float(np.mean(hyp_lens)), 2),
        "repetition_rate_pct": round(sum(repetition_flags) / max(1, total) * 100.0, 2),
        **token_stats,
        "sample_count": total
    }

def audit_attention(model, features_list, masks_list):
    """
    Audits attention entropy and temporal progression on the validation set.
    """
    model.eval()
    entropies = []
    coverages = []
    com_progressions = []

    with torch.no_grad():
        for f, m in zip(features_list[:50], masks_list[:50]): # sample 50 clips for detailed attention tracking
            T = f.size(1)
            enc_out = model.encoder(f, m, None)
            inv_mask = ~m
            precomputed_enc = model.decoder.attention.w_enc(enc_out)

            mask_expanded = m.unsqueeze(-1).float()
            sum_enc = (enc_out * mask_expanded).sum(dim=1)
            mean_enc = sum_enc / mask_expanded.sum(dim=1).clamp(min=1.0)
            dec_state = torch.tanh(model.enc_to_dec(mean_enc))

            token_in = torch.tensor([model.sos_id], dtype=torch.long, device=f.device)
            clip_entropies = []
            coms = []

            for _ in range(15):
                _, dec_state, attn = model.decoder.forward_step(
                    token_in, dec_state, enc_out, precomputed_enc, inv_mask
                )
                weights = attn[0].cpu().numpy() # [T]
                # Normalized entropy
                h = -np.sum(weights * np.log(np.maximum(weights, 1e-12)))
                h_norm = h / max(1e-12, np.log(T))
                clip_entropies.append(h_norm)

                # Coverage (weights > 1 / (2*T))
                cov = np.sum(weights > (0.5 / T)) / T
                coverages.append(cov)

                # Center of mass
                t_idx = np.arange(T)
                com = np.sum(t_idx * weights)
                coms.append(com)

                token_in = torch.tensor([model.pad_id], dtype=torch.long, device=f.device)

            entropies.append(float(np.mean(clip_entropies)))
            if len(coms) > 1:
                progression = coms[-1] - coms[0]
                com_progressions.append(progression)

    return {
        "mean_normalized_entropy": round(float(np.mean(entropies)), 4),
        "mean_coverage_pct": round(float(np.mean(coverages)) * 100.0, 2),
        "mean_center_of_mass_drift": round(float(np.mean(com_progressions)), 2)
    }

def run_evaluation():
    manifest_path = exp26_dir / "dataset_manifest.csv"
    feat_dir = exp26_dir / "features"
    tok_path = exp27_dir / "tokenizer.json"
    model_path = exp29_dir / "best_ctc_attention_model.pt"

    tokenizer = BPETokenizer.load(tok_path)
    vocab_size = len(tokenizer.token2id)

    model = JointCTCAttentionModel(
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

    def generate_all(feats, masks, rep_penalty=1.2):
        hyps = []
        latencies = []
        with torch.no_grad():
            for f, m in zip(feats, masks):
                t0 = time.perf_counter()
                tokens = model.generate(f, m, max_len=50, repetition_penalty=rep_penalty)
                latencies.append((time.perf_counter() - t0) * 1000.0)
                hyps.append(tokenizer.decode(tokens, skip_special_tokens=True))
        return hyps, latencies

    def generate_ctc_all(feats, masks):
        hyps = []
        with torch.no_grad():
            for f, m in zip(feats, masks):
                tokens_list = model.generate_ctc(f, m)
                tokens = tokens_list[0]
                hyps.append(tokenizer.decode(tokens, skip_special_tokens=True))
        return hyps

    print("\n[EVALUATION] Generating Condition 1: Normal Videos...")
    normal_hyps, latencies = generate_all(features_list, masks_list, rep_penalty=1.2)
    normal_metrics = analyze_generation(refs, normal_hyps)

    print("[EVALUATION] Generating CTC Greedy Condition...")
    ctc_hyps = generate_ctc_all(features_list, masks_list)
    ctc_metrics = analyze_generation(refs, ctc_hyps)

    print("[EVALUATION] Generating Condition 2: Zeroed Landmark Features...")
    zero_feats = [torch.zeros_like(f) for f in features_list]
    zero_hyps, _ = generate_all(zero_feats, masks_list, rep_penalty=1.2)
    zero_metrics = analyze_generation(refs, zero_hyps)

    print("[EVALUATION] Generating Condition 3: Shuffled-Frame Features...")
    shuff_feats = []
    for f in features_list:
        T = f.size(1)
        perm = torch.randperm(T)
        shuff_feats.append(f[:, perm, :])
    shuff_hyps, _ = generate_all(shuff_feats, masks_list, rep_penalty=1.2)
    shuff_metrics = analyze_generation(refs, shuff_hyps)

    shuff_ident = sum(1 for h1, h2 in zip(normal_hyps, shuff_hyps) if normalize_text(h1) == normalize_text(h2)) / N * 100.0
    zero_ident = sum(1 for h1, h2 in zip(normal_hyps, zero_hyps) if normalize_text(h1) == normalize_text(h2)) / N * 100.0

    print("[EVALUATION] Generating Condition 4: Mismatched References (Seed 42)...")
    rng = random.Random(42)
    shift = rng.randint(1, N - 1)
    mismatched_refs = [refs[(i + shift) % N] for i in range(N)]
    mismatched_metrics = analyze_generation(mismatched_refs, normal_hyps)

    # Win / tie / loss comparison between matched and mismatched
    smooth_p = []
    matched_wins = 0
    ties = 0
    mismatched_wins = 0
    for r_match, r_mismatch, hyp in zip(refs, mismatched_refs, normal_hyps):
        hyp_toks = normalize_text(hyp).split()
        match_toks = normalize_text(r_match).split()
        mismatch_toks = normalize_text(r_mismatch).split()

        b_match = compute_bleu([r_match], [hyp])["bleu1"]
        b_mismatch = compute_bleu([r_mismatch], [hyp])["bleu1"]

        if b_match > b_mismatch:
            matched_wins += 1
        elif b_match < b_mismatch:
            mismatched_wins += 1
        else:
            ties += 1

    print("[EVALUATION] Auditing Attention Distribution...")
    attn_audit = audit_attention(model, features_list, masks_list)

    eval_results = {
        "checkpoint": str(model_path),
        "total_parameters": sum(p.numel() for p in model.parameters()),
        "validation_samples": N,
        "latency_ms": {
            "mean": round(float(np.mean(latencies)), 2),
            "median": round(float(np.median(latencies)), 2),
            "p95": round(float(np.percentile(latencies, 95)), 2)
        },
        "conditions": {
            "normal_attention": normal_metrics,
            "ctc_greedy": ctc_metrics,
            "zeroed": zero_metrics,
            "shuffled": shuff_metrics,
            "mismatched": mismatched_metrics
        },
        "input_dependence": {
            "shuffled_identical_output_pct": round(shuff_ident, 2),
            "zeroed_identical_output_pct": round(zero_ident, 2),
            "matched_win_pct": round(matched_wins / N * 100.0, 2),
            "tie_pct": round(ties / N * 100.0, 2),
            "mismatched_win_pct": round(mismatched_wins / N * 100.0, 2)
        },
        "attention_audit": attn_audit,
        "sample_hypotheses": [
            {
                "idx": i,
                "ref": refs[i],
                "hyp_attention": normal_hyps[i],
                "hyp_ctc": ctc_hyps[i],
                "hyp_shuffled": shuff_hyps[i],
                "hyp_zeroed": zero_hyps[i]
            }
            for i in range(5)
        ]
    }

    out_file = exp29_dir / "evaluation_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(eval_results, f, indent=2)
    print(f"\nSaved evaluation results to {out_file}")

    print("\n================== PHASE 2C.29 RESULTS SUMMARY ==================")
    print(f"Normal Attention:  BLEU-1={normal_metrics['bleu_1']}%, BLEU-4={normal_metrics['bleu4']}%, Token Lev Acc={normal_metrics['levenshtein_token_accuracy_pct']}%, Repetition={normal_metrics['repetition_rate_pct']}%")
    print(f"CTC Greedy:        BLEU-1={ctc_metrics['bleu_1']}%, BLEU-4={ctc_metrics['bleu4']}%, Token Lev Acc={ctc_metrics['levenshtein_token_accuracy_pct']}%, Repetition={ctc_metrics['repetition_rate_pct']}%")
    print(f"Zeroed Input:      BLEU-1={zero_metrics['bleu_1']}%, Shuffled Input: BLEU-1={shuff_metrics['bleu_1']}%")
    print(f"Shuffled Identity: {shuff_ident:.2f}% (Baseline was 90.31%)")
    print(f"Pairwise Wins:     Matched Win={matched_wins/N*100:.1f}%, Tie={ties/N*100:.1f}%, Mismatched Win={mismatched_wins/N*100:.1f}%")
    print(f"Attention Audit:   Mean Normalized Entropy={attn_audit['mean_normalized_entropy']}, Coverage={attn_audit['mean_coverage_pct']}%")
    print(f"Latency:           Mean={eval_results['latency_ms']['mean']} ms, Median={eval_results['latency_ms']['median']} ms")
    print("=================================================================")

if __name__ == "__main__":
    run_evaluation()
