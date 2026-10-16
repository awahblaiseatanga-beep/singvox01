import sys
import os
import json
import math
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

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

class AuditAttentionModel(AttentionSeq2Seq):
    def __init__(self, vocab_size, in_features=366, hidden_dim=256, embed_dim=128, attn_dim=128, pad_id=0, sos_id=1, eos_id=2, dropout=0.2):
        super().__init__(vocab_size, in_features, hidden_dim, embed_dim, attn_dim, pad_id, sos_id, eos_id, dropout)
        self.encoder = LandmarkEncoder(in_features=in_features, hidden_dim=hidden_dim, num_layers=2, dropout=dropout)
        self.decoder = AttentionDecoder(vocab_size=vocab_size, embed_dim=embed_dim, enc_dim=hidden_dim, dec_dim=hidden_dim, attn_dim=attn_dim, pad_id=pad_id, dropout=dropout)

    @torch.no_grad()
    def generate_with_attention(self, src, src_mask, max_len=50):
        # src: [1, T, in_features]
        # src_mask: [1, T] (True for valid, False for pad)
        enc_outputs, dec_hidden = self.encoder(src)
        enc_proj = self.decoder.attention.w_enc(enc_outputs)
        inv_mask = ~src_mask if src_mask is not None else None
        
        curr_token = torch.tensor([self.sos_id], device=src.device)
        generated_tokens = []
        all_attentions = [] # list of [T] tensors
        
        for _ in range(max_len):
            logits, dec_hidden, attn_weights = self.decoder.step(
                curr_token, dec_hidden, enc_outputs, enc_proj, inv_mask
            )
            all_attentions.append(attn_weights.squeeze(0).cpu().numpy())
            next_token = logits.argmax(1)
            token_id = next_token.item()
            if token_id == self.eos_id:
                break
            generated_tokens.append(token_id)
            curr_token = next_token
            
        attn_matrix = np.array(all_attentions) if all_attentions else np.zeros((0, src.size(1)))
        return generated_tokens, attn_matrix

def audit_attention():
    manifest_path = exp26_dir / "dataset_manifest.csv"
    feat_dir = exp26_dir / "features"
    tok_path = exp27_dir / "tokenizer.json"
    model_path = exp27_dir / "best_attention_model.pt"

    tokenizer = BPETokenizer.load(tok_path)
    vocab_size = len(tokenizer.token2id)

    model = AuditAttentionModel(
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

    # 1. Padding mask verification: Test explicitly on padded sequences
    # Create batch of varying lengths padded to max_len=150
    print("\n--- Verifying Padding Mask Enforcement ---")
    pad_leakage_max = 0.0
    pad_leakage_count = 0
    total_pad_elements_checked = 0

    entropies_orig = []
    coverages_orig = []
    monotonicity_correlations = []

    # Collect detailed attention for 5 representative clips
    representative_samples = []

    for i in range(N):
        sample = val_dataset[i]
        feat = sample["features"] # [T_valid, 366]
        T_valid = feat.size(0)
        
        # Test with padded representation to test mask
        T_pad = 150
        padded_feat = torch.zeros((1, T_pad, 366))
        padded_feat[0, :T_valid, :] = feat
        mask = torch.zeros((1, T_pad), dtype=torch.bool)
        mask[0, :T_valid] = True

        gen_tokens, attn_matrix = model.generate_with_attention(padded_feat, mask, max_len=50)
        # attn_matrix: [S, 150]
        S = attn_matrix.shape[0]
        if S == 0:
            continue

        # Check padding region: indices [:, T_valid:]
        if T_valid < T_pad:
            pad_region = attn_matrix[:, T_valid:]
            max_pad_val = float(np.max(pad_region))
            pad_leakage_max = max(pad_leakage_max, max_pad_val)
            pad_leakage_count += int(np.sum(pad_region > 1e-6))
            total_pad_elements_checked += pad_region.size

        # Valid region analysis: indices [:, :T_valid]
        valid_region = attn_matrix[:, :T_valid]
        # Normalize slightly if sum was ~1.0
        row_sums = np.sum(valid_region, axis=1, keepdims=True)
        norm_valid = valid_region / np.maximum(row_sums, 1e-9)

        # Entropy per step
        eps = 1e-12
        h_steps = -np.sum(norm_valid * np.log(norm_valid + eps), axis=1) # [S]
        max_h = math.log(max(2, T_valid))
        h_norm_steps = h_steps / max_h
        coverage_steps = np.exp(h_steps) / T_valid

        entropies_orig.append(float(np.mean(h_norm_steps)))
        coverages_orig.append(float(np.mean(coverage_steps)))

        # Center of mass per step: expected frame index
        frame_indices = np.arange(T_valid)
        center_of_mass = np.sum(norm_valid * frame_indices, axis=1) # [S]
        # Correlation between step s (0..S-1) and center_of_mass (temporal progression)
        if S > 2:
            step_indices = np.arange(S)
            std_step = np.std(step_indices)
            std_cm = np.std(center_of_mass)
            if std_step > 1e-6 and std_cm > 1e-6:
                corr = np.corrcoef(step_indices, center_of_mass)[0, 1]
                if not np.isnan(corr):
                    monotonicity_correlations.append(float(corr))

        if i < 5:
            hyp_str = tokenizer.decode(gen_tokens, skip_special_tokens=True)
            representative_samples.append({
                "idx": i,
                "name": sample["name"],
                "video_id": sample["video_id"],
                "ref": sample["sentence"],
                "hyp": hyp_str,
                "valid_frames": T_valid,
                "decoding_steps": S,
                "mean_norm_entropy": round(float(np.mean(h_norm_steps)), 4),
                "mean_coverage": round(float(np.mean(coverage_steps)), 4),
                "center_of_mass_trajectory": [round(float(c), 2) for c in center_of_mass],
                "attn_matrix_shape": list(attn_matrix.shape),
                # Save downsampled attention profile across 5 temporal buckets
                "temporal_profile_5_buckets": [
                    round(float(np.mean(norm_valid[:, int(b * T_valid / 5): int((b + 1) * T_valid / 5)])), 4)
                    for b in range(5)
                ]
            })

    # Summary statistics
    audit_summary = {
        "padding_mask_verification": {
            "total_padded_elements_checked": total_pad_elements_checked,
            "max_padding_leakage_weight": pad_leakage_max,
            "leakage_count_above_1e6": pad_leakage_count,
            "mask_integrity_status": "PASSED - ZERO LEAKAGE" if pad_leakage_max < 1e-7 else "FAILED LEAKAGE DETECTED"
        },
        "attention_entropy_and_concentration": {
            "mean_normalized_entropy": round(float(np.mean(entropies_orig)), 4),
            "std_normalized_entropy": round(float(np.std(entropies_orig)), 4),
            "mean_temporal_coverage_pct": round(float(np.mean(coverages_orig)) * 100.0, 2),
            "std_temporal_coverage_pct": round(float(np.std(coverages_orig)) * 100.0, 2),
            "interpretation": "DIFFUSE ATTENTION" if float(np.mean(entropies_orig)) > 0.85 else "FOCUSED ATTENTION"
        },
        "temporal_progression_monotonicity": {
            "mean_step_frame_correlation": round(float(np.mean(monotonicity_correlations)), 4),
            "std_step_frame_correlation": round(float(np.std(monotonicity_correlations)), 4),
            "positive_monotonicity_pct": round(sum(1 for c in monotonicity_correlations if c > 0.3) / max(1, len(monotonicity_correlations)) * 100.0, 2),
            "near_zero_or_negative_pct": round(sum(1 for c in monotonicity_correlations if c <= 0.3) / max(1, len(monotonicity_correlations)) * 100.0, 2),
            "interpretation": "NO MONOTONIC ALIGNMENT" if float(np.mean(monotonicity_correlations)) < 0.2 else "MONOTONIC ALIGNMENT"
        },
        "representative_samples": representative_samples
    }

    out_file = exp28_dir / "attention_audit_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)

    print("\n--- ATTENTION AUDIT RESULTS ---")
    print(f"Mask Integrity: {audit_summary['padding_mask_verification']['mask_integrity_status']} (Max leakage: {pad_leakage_max:.2e})")
    print(f"Mean Normalized Entropy: {audit_summary['attention_entropy_and_concentration']['mean_normalized_entropy']} ({audit_summary['attention_entropy_and_concentration']['interpretation']})")
    print(f"Mean Temporal Coverage: {audit_summary['attention_entropy_and_concentration']['mean_temporal_coverage_pct']}% of sequence frames")
    print(f"Mean Step-Frame Correlation: {audit_summary['temporal_progression_monotonicity']['mean_step_frame_correlation']} ({audit_summary['temporal_progression_monotonicity']['interpretation']})")
    print(f"Saved audit results to {out_file}")

if __name__ == "__main__":
    audit_attention()
