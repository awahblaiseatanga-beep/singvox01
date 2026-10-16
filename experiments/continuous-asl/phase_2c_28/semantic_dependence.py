import sys
import os
import json
import random
import math
from pathlib import Path
from collections import Counter
import numpy as np
import torch
import torch.nn as nn

torch.set_num_threads(1)

base_dir = Path(r"d:\Singvox\Singvox")
exp27_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_27"
exp26_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_26"
exp28_dir = base_dir / "experiments" / "continuous-asl" / "phase_2c_28"
exp28_dir.mkdir(parents=True, exist_ok=True)

sys.path.append(str(exp27_dir))
from model import LandmarkEncoder, AttentionDecoder, AttentionSeq2Seq
from dataset import How2SignAttentionDataset
from tokenizer import BPETokenizer

# Define exact class matching the 2.08M parameter checkpoint
class FrozenPhase27Model(AttentionSeq2Seq):
    def __init__(self, vocab_size, in_features=366, hidden_dim=256, embed_dim=128, attn_dim=128, pad_id=0, sos_id=1, eos_id=2, dropout=0.2):
        super().__init__(vocab_size, in_features, hidden_dim, embed_dim, attn_dim, pad_id, sos_id, eos_id, dropout)
        self.encoder = LandmarkEncoder(in_features=in_features, hidden_dim=hidden_dim, num_layers=2, dropout=dropout)
        self.decoder = AttentionDecoder(vocab_size=vocab_size, embed_dim=embed_dim, enc_dim=hidden_dim, dec_dim=hidden_dim, attn_dim=attn_dim, pad_id=pad_id, dropout=dropout)

# Set deterministic seeds
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

def compute_corpus_bleu(references, hypotheses):
    def get_ngrams(tokens, n):
        return Counter([tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)])

    p_ns = []
    for n in range(1, 5):
        match_count = 0
        hyp_count = 0
        for ref_str, hyp_str in zip(references, hypotheses):
            ref_tokens = ref_str.strip().lower().split()
            hyp_tokens = hyp_str.strip().lower().split()
            ref_ngrams = get_ngrams(ref_tokens, n)
            hyp_ngrams = get_ngrams(hyp_tokens, n)
            
            for ng, cnt in hyp_ngrams.items():
                match_count += min(cnt, ref_ngrams.get(ng, 0))
            hyp_count += max(0, len(hyp_tokens) - n + 1)
        
        p_n = match_count / max(1, hyp_count) if hyp_count > 0 else 0.0
        p_ns.append(p_n)
        
    total_ref_len = sum(len(r.strip().lower().split()) for r in references)
    total_hyp_len = sum(len(h.strip().lower().split()) for h in hypotheses)
    
    if total_hyp_len == 0:
        bp = 0.0
    elif total_hyp_len < total_ref_len:
        bp = math.exp(1.0 - total_ref_len / total_hyp_len)
    else:
        bp = 1.0

    def geom_mean(p_list):
        if any(p <= 1e-9 for p in p_list):
            return 0.0
        return math.exp(sum(math.log(p) for p in p_list) / len(p_list))

    bleu1 = bp * p_ns[0] * 100.0
    bleu2 = bp * geom_mean(p_ns[:2]) * 100.0
    bleu4 = bp * geom_mean(p_ns) * 100.0

    return {
        "bleu1": round(bleu1, 2),
        "bleu2": round(bleu2, 2),
        "bleu4": round(bleu4, 2),
        "bp": round(bp, 4),
        "total_hyp_len": total_hyp_len,
        "total_ref_len": total_ref_len,
        "avg_hyp_len": round(total_hyp_len / max(1, len(hypotheses)), 2)
    }

def sentence_bleu1(ref_str, hyp_str):
    ref_toks = ref_str.strip().lower().split()
    hyp_toks = hyp_str.strip().lower().split()
    if not hyp_toks or not ref_toks:
        return 0.0
    ref_counts = Counter(ref_toks)
    hyp_counts = Counter(hyp_toks)
    matches = sum(min(c, ref_counts.get(t, 0)) for t, c in hyp_counts.items())
    prec = matches / len(hyp_toks)
    bp = math.exp(1.0 - len(ref_toks) / len(hyp_toks)) if len(hyp_toks) < len(ref_toks) else 1.0
    return bp * prec * 100.0

def word_edit_distance(ref_str, hyp_str):
    r = ref_str.strip().lower().split()
    h = hyp_str.strip().lower().split()
    dp = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        dp[i][0] = i
    for j in range(len(h) + 1):
        dp[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            cost = 0 if r[i-1] == h[j-1] else 1
            dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + cost)
    return dp[len(r)][len(h)]

def generate_derangement(n, seed):
    rng = random.Random(seed)
    indices = list(range(n))
    while True:
        perm = indices[:]
        rng.shuffle(perm)
        if all(perm[i] != i for i in range(n)):
            return perm

def run_semantic_diagnostics():
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
    print("Loaded FrozenPhase27Model (2.08M params) cleanly!")

    val_dataset = How2SignAttentionDataset(manifest_path, feat_dir, tokenizer, split="val", max_frames=150)
    N = len(val_dataset)
    print(f"Validation dataset size: {N} samples.")

    # Cache all validation features and metadata
    raw_samples = []
    for i in range(N):
        raw_samples.append(val_dataset[i])

    print("Cached all validation samples.")

    def decode_feature_list(features_list):
        hypotheses = []
        for i, feat in enumerate(features_list):
            src = feat.unsqueeze(0) # [1, T, 366]
            src_mask = torch.ones((1, feat.size(0)), dtype=torch.bool)
            with torch.no_grad():
                pred_ids = model.generate(src, src_mask=src_mask, max_len=60)
            tok_ids = pred_ids[0].tolist() if isinstance(pred_ids, torch.Tensor) else pred_ids
            hyp_str = tokenizer.decode(tok_ids, skip_special_tokens=True)
            hypotheses.append(hyp_str)
        return hypotheses

    true_references = [s["sentence"] for s in raw_samples]
    sample_names = [s["name"] for s in raw_samples]
    video_ids = [s["video_id"] for s in raw_samples]
    orig_features = [s["features"] for s in raw_samples]

    results = {}

    # Condition 1: Original
    print("\nEvaluating Condition 1: Original Features...")
    hyp_orig = decode_feature_list(orig_features)
    bleu_orig = compute_corpus_bleu(true_references, hyp_orig)
    rep_orig = sum(1 for h in hyp_orig if any(h.split()[i] == h.split()[i+1] == h.split()[i+2] for i in range(len(h.split())-2)))
    results["c1_original"] = {
        "bleu": bleu_orig,
        "repetition_pct": round(rep_orig / N * 100.0, 2),
        "hypotheses": hyp_orig
    }
    print(f"  Condition 1: BLEU-1={bleu_orig['bleu1']}%, BLEU-4={bleu_orig['bleu4']}%, Rep={results['c1_original']['repetition_pct']}%")

    # Condition 2: Zeroed
    print("Evaluating Condition 2: Zeroed Features...")
    zero_features = [torch.zeros_like(f) for f in orig_features]
    hyp_zero = decode_feature_list(zero_features)
    bleu_zero = compute_corpus_bleu(true_references, hyp_zero)
    rep_zero = sum(1 for h in hyp_zero if any(h.split()[i] == h.split()[i+1] == h.split()[i+2] for i in range(len(h.split())-2)))
    results["c2_zeroed"] = {
        "bleu": bleu_zero,
        "repetition_pct": round(rep_zero / N * 100.0, 2),
        "hypotheses": hyp_zero
    }
    print(f"  Condition 2: BLEU-1={bleu_zero['bleu1']}%, BLEU-4={bleu_zero['bleu4']}%, Rep={results['c2_zeroed']['repetition_pct']}%")

    # Condition 3: Temporally Shuffled Frames
    print("Evaluating Condition 3: Temporally Shuffled Frames...")
    rng_shuf = np.random.RandomState(42)
    shuf_features = []
    for f in orig_features:
        T = f.size(0)
        perm = rng_shuf.permutation(T)
        shuf_features.append(f[perm])
    hyp_shuf = decode_feature_list(shuf_features)
    bleu_shuf = compute_corpus_bleu(true_references, hyp_shuf)
    rep_shuf = sum(1 for h in hyp_shuf if any(h.split()[i] == h.split()[i+1] == h.split()[i+2] for i in range(len(h.split())-2)))
    identical_to_orig_shuf = sum(1 for i in range(N) if hyp_orig[i].strip() == hyp_shuf[i].strip())
    results["c3_shuffled"] = {
        "bleu": bleu_shuf,
        "repetition_pct": round(rep_shuf / N * 100.0, 2),
        "identical_to_orig_pct": round(identical_to_orig_shuf / N * 100.0, 2),
        "hypotheses": hyp_shuf
    }
    print(f"  Condition 3: BLEU-1={bleu_shuf['bleu1']}%, BLEU-4={bleu_shuf['bleu4']}%, IdenticalToOrig={results['c3_shuffled']['identical_to_orig_pct']}%")

    # Condition 4: Rolled by 1 (Mismatched reference)
    print("Evaluating Condition 4: Rolled by 1 Features...")
    roll_1_features = [orig_features[(i + 1) % N] for i in range(N)]
    hyp_roll1 = decode_feature_list(roll_1_features)
    bleu_roll1 = compute_corpus_bleu(true_references, hyp_roll1)
    rep_roll1 = sum(1 for h in hyp_roll1 if any(h.split()[i] == h.split()[i+1] == h.split()[i+2] for i in range(len(h.split())-2)))
    identical_to_orig_roll1 = sum(1 for i in range(N) if hyp_orig[i].strip() == hyp_roll1[i].strip())
    results["c4_rolled_1"] = {
        "bleu": bleu_roll1,
        "repetition_pct": round(rep_roll1 / N * 100.0, 2),
        "identical_to_orig_pct": round(identical_to_orig_roll1 / N * 100.0, 2),
        "hypotheses": hyp_roll1
    }
    print(f"  Condition 4: BLEU-1={bleu_roll1['bleu1']}%, BLEU-4={bleu_roll1['bleu4']}%, IdenticalToOrig={results['c4_rolled_1']['identical_to_orig_pct']}%")

    # Condition 5: 5 Seeded Derangements
    print("Evaluating Condition 5: 5 Seeded Derangements...")
    seeds = [101, 202, 303, 404, 505]
    derange_results = []
    for seed in seeds:
        perm = generate_derangement(N, seed)
        accidental_text_matches = sum(1 for i, p_idx in enumerate(perm) if true_references[i].strip().lower() == true_references[p_idx].strip().lower())
        mismatched_features = [orig_features[p_idx] for p_idx in perm]
        hyp_perm = decode_feature_list(mismatched_features)
        bleu_perm = compute_corpus_bleu(true_references, hyp_perm)
        rep_perm = sum(1 for h in hyp_perm if any(h.split()[i] == h.split()[i+1] == h.split()[i+2] for i in range(len(h.split())-2)))
        
        wins = 0 # orig > perm
        ties = 0 # orig == perm
        losses = 0 # orig < perm
        bleu1_diffs = []
        edit_dist_orig = []
        edit_dist_perm = []
        
        for i in range(N):
            b_orig = sentence_bleu1(true_references[i], hyp_orig[i])
            b_perm = sentence_bleu1(true_references[i], hyp_perm[i])
            diff = b_orig - b_perm
            bleu1_diffs.append(diff)
            if diff > 1e-4:
                wins += 1
            elif diff < -1e-4:
                losses += 1
            else:
                ties += 1
            edit_dist_orig.append(word_edit_distance(true_references[i], hyp_orig[i]))
            edit_dist_perm.append(word_edit_distance(true_references[i], hyp_perm[i]))

        mean_diff = float(np.mean(bleu1_diffs))
        std_diff = float(np.std(bleu1_diffs))
        ci95 = 1.96 * std_diff / math.sqrt(N)
        
        identical_hyps = sum(1 for i in range(N) if hyp_orig[i].strip() == hyp_perm[i].strip())
        
        entry = {
            "seed": seed,
            "accidental_text_matches": accidental_text_matches,
            "bleu": bleu_perm,
            "repetition_pct": round(rep_perm / N * 100.0, 2),
            "wins": wins,
            "ties": ties,
            "losses": losses,
            "win_rate_pct": round(wins / N * 100.0, 2),
            "tie_rate_pct": round(ties / N * 100.0, 2),
            "loss_rate_pct": round(losses / N * 100.0, 2),
            "mean_bleu1_diff": round(mean_diff, 4),
            "std_bleu1_diff": round(std_diff, 4),
            "ci95_bleu1_diff": round(ci95, 4),
            "mean_edit_dist_orig": round(float(np.mean(edit_dist_orig)), 2),
            "mean_edit_dist_perm": round(float(np.mean(edit_dist_perm)), 2),
            "identical_hypotheses_pct": round(identical_hyps / N * 100.0, 2)
        }
        derange_results.append(entry)
        print(f"  Seed {seed}: Wins={wins}, Ties={ties}, Losses={losses} | Mean Diff={entry['mean_bleu1_diff']} | Identical={entry['identical_hypotheses_pct']}%")

    results["c5_seeded_derangements"] = derange_results

    # Condition 6: Static First Frame Repeated (Zero Motion)
    print("Evaluating Condition 6: Static First Frame Repeated...")
    static_features = []
    for f in orig_features:
        T = f.size(0)
        first_frame = f[0:1, :].repeat(T, 1)
        static_features.append(first_frame)
    hyp_static = decode_feature_list(static_features)
    bleu_static = compute_corpus_bleu(true_references, hyp_static)
    rep_static = sum(1 for h in hyp_static if any(h.split()[i] == h.split()[i+1] == h.split()[i+2] for i in range(len(h.split())-2)))
    identical_to_orig_static = sum(1 for i in range(N) if hyp_orig[i].strip() == hyp_static[i].strip())
    results["c6_static_frame"] = {
        "bleu": bleu_static,
        "repetition_pct": round(rep_static / N * 100.0, 2),
        "identical_to_orig_pct": round(identical_to_orig_static / N * 100.0, 2),
        "hypotheses": hyp_static
    }
    print(f"  Condition 6: BLEU-1={bleu_static['bleu1']}%, BLEU-4={bleu_static['bleu4']}%, IdenticalToOrig={results['c6_static_frame']['identical_to_orig_pct']}%")

    # Condition 7: Length-matched swap across different VIDEO_IDs
    print("Evaluating Condition 7: Length-Matched Swap...")
    length_swap_indices = []
    used_j = set()
    lengths = [f.size(0) for f in orig_features]
    for i in range(N):
        best_j = None
        best_diff = 999999
        for j in range(N):
            if i != j and video_ids[i] != video_ids[j]:
                d = abs(lengths[i] - lengths[j])
                if d < best_diff and j not in used_j:
                    best_diff = d
                    best_j = j
        if best_j is None:
            for j in range(N):
                if i != j and video_ids[i] != video_ids[j]:
                    d = abs(lengths[i] - lengths[j])
                    if d < best_diff:
                        best_diff = d
                        best_j = j
        length_swap_indices.append(best_j)
        used_j.add(best_j)
        
    length_swap_features = [orig_features[j] for j in length_swap_indices]
    hyp_len_swap = decode_feature_list(length_swap_features)
    bleu_len_swap = compute_corpus_bleu(true_references, hyp_len_swap)
    rep_len_swap = sum(1 for h in hyp_len_swap if any(h.split()[i] == h.split()[i+1] == h.split()[i+2] for i in range(len(h.split())-2)))
    identical_to_orig_len_swap = sum(1 for i in range(N) if hyp_orig[i].strip() == hyp_len_swap[i].strip())
    results["c7_length_matched_swap"] = {
        "bleu": bleu_len_swap,
        "repetition_pct": round(rep_len_swap / N * 100.0, 2),
        "identical_to_orig_pct": round(identical_to_orig_len_swap / N * 100.0, 2),
        "hypotheses": hyp_len_swap
    }
    print(f"  Condition 7: BLEU-1={bleu_len_swap['bleu1']}%, BLEU-4={bleu_len_swap['bleu4']}%, IdenticalToOrig={results['c7_length_matched_swap']['identical_to_orig_pct']}%")

    # Sample detailed qualitative predictions (first 10 clips)
    qualitative_samples = []
    for i in range(10):
        qualitative_samples.append({
            "idx": i,
            "sample_name": sample_names[i],
            "video_id": video_ids[i],
            "ref": true_references[i],
            "hyp_orig": hyp_orig[i],
            "hyp_zero": hyp_zero[i],
            "hyp_shuf": hyp_shuf[i],
            "hyp_roll1": hyp_roll1[i],
            "hyp_static": hyp_static[i],
            "hyp_len_swap": hyp_len_swap[i],
            "len_swap_partner_name": sample_names[length_swap_indices[i]],
            "len_swap_partner_len": orig_features[length_swap_indices[i]].size(0),
            "orig_len": orig_features[i].size(0)
        })
    results["qualitative_samples"] = qualitative_samples

    # Save complete diagnostic results
    out_file = exp28_dir / "semantic_dependence_results.json"
    save_obj = {
        "c1_original": {k: v for k, v in results["c1_original"].items() if k != "hypotheses"},
        "c2_zeroed": {k: v for k, v in results["c2_zeroed"].items() if k != "hypotheses"},
        "c3_shuffled": {k: v for k, v in results["c3_shuffled"].items() if k != "hypotheses"},
        "c4_rolled_1": {k: v for k, v in results["c4_rolled_1"].items() if k != "hypotheses"},
        "c5_seeded_derangements": results["c5_seeded_derangements"],
        "c6_static_frame": {k: v for k, v in results["c6_static_frame"].items() if k != "hypotheses"},
        "c7_length_matched_swap": {k: v for k, v in results["c7_length_matched_swap"].items() if k != "hypotheses"},
        "qualitative_samples": results["qualitative_samples"]
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(save_obj, f, indent=2)
    print(f"\nSaved semantic dependence diagnostic results to {out_file}")

if __name__ == "__main__":
    run_semantic_diagnostics()
