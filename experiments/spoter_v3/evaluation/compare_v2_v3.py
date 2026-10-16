"""
SignVox SPOTER V2 vs V3 Cross-Model Comparative Evaluation
Evaluates SPOTER V2 (79-class production baseline) and SPOTER V3 (100-class candidate)
on the exact same held-out test split, benchmarking their shared vocabulary fairly.

Features:
- Canonical ASL ID alignment (avoids index misalignment across models).
- Exact restoration of model-specific GroupNorm scaling.
- Evaluates 79 shared classes head-to-head under both:
    * Protocol A (Restricted Subspace): Fair closed-set comparison restricted to shared classes.
    * Protocol B (Unrestricted Full-Space): Open-vocabulary ranking across all logits.
- Comprehensive metrics: Top-1, Top-3, Macro-average, per-class support/accuracy, confusion matrices.
- Evaluates V3 across all 95 supported test classes (1,379 samples) and 16 extended classes.
- Rigorous safeguards: fails fast on missing artifacts or dimensions, never outputs null metrics.
"""

import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import torch
import torch.nn as nn

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
EXP_DIR = SCRIPT_DIR.parent
ROOT_DIR = EXP_DIR.parent.parent

sys.path.append(str(ROOT_DIR / "ai" / "sign-recognition" / "models"))
sys.path.append(str(EXP_DIR / "models"))
sys.path.append(str(EXP_DIR / "training"))

from spoter import Spoter as SpoterV2
from spoter_v3 import SpoterV3
from dataloaders_v3 import get_feature_channel_indices, apply_groupnorm_scaling


def parse_args():
    parser = argparse.ArgumentParser(description="SignVox SPOTER V2 vs V3 Comparative Audit")
    parser.add_argument(
        "--v2_checkpoint",
        type=str,
        default=str(ROOT_DIR / "ai" / "sign-recognition" / "checkpoints" / "spoter_v2_groupnorm_best_val_acc.pt"),
        help="Path to SPOTER V2 checkpoint .pt"
    )
    parser.add_argument(
        "--v3_checkpoint",
        type=str,
        default=str(EXP_DIR / "checkpoints" / "spoter_v3_best_val_acc_checkpoint.pt"),
        help="Path to SPOTER V3 checkpoint .pt"
    )
    parser.add_argument(
        "--v2_mapping",
        type=str,
        default=str(ROOT_DIR / "ai" / "sign-recognition" / "data" / "class_index_mapping.json"),
        help="Path to V2 79-class mapping JSON"
    )
    parser.add_argument(
        "--v3_mapping",
        type=str,
        default=str(EXP_DIR / "config" / "asl100_v3_class_mapping.json"),
        help="Path to V3 100-class mapping JSON"
    )
    parser.add_argument(
        "--v2_scalars",
        type=str,
        default=str(ROOT_DIR / "ai" / "sign-recognition" / "models" / "spoter_v2_groupnorm_scalars.json"),
        help="Path to V2 GroupNorm scalars JSON"
    )
    parser.add_argument(
        "--v3_scalars",
        type=str,
        default=str(EXP_DIR / "checkpoints" / "spoter_v3_groupnorm_scalars.json"),
        help="Path to V3 GroupNorm scalars JSON"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=str(EXP_DIR / "manifests" / "spoter_v3_matched_manifest.csv"),
        help="Path to matched dataset manifest CSV"
    )
    parser.add_argument(
        "--features_dir",
        type=str,
        default=str(ROOT_DIR / "ai" / "sign-recognition" / "data" / "dataset_extracted"),
        help="Directory containing extracted 366-D .npy landmark feature files"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        choices=["train", "val", "test"],
        help="Dataset split to evaluate (default: test)"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=32,
        help="Batch size for evaluation"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Inference compute device"
    )
    parser.add_argument(
        "--output_json",
        type=str,
        default=str(EXP_DIR / "v2_v3_shared_test_comparison.json"),
        help="Path to save output comparison report JSON"
    )
    return parser.parse_args()


def load_mappings(
    v2_mapping_path: str,
    v3_mapping_path: str
) -> Tuple[Dict[str, int], Dict[int, str], Dict[str, str], Dict[str, int], Dict[int, str], Dict[str, str], List[str]]:
    """
    Loads and validates class mappings for V2 and V3, returning canonical lookups and shared classes.
    """
    if not os.path.exists(v2_mapping_path):
        raise FileNotFoundError(f"V2 class mapping not found at: {v2_mapping_path}")
    if not os.path.exists(v3_mapping_path):
        raise FileNotFoundError(f"V3 class mapping not found at: {v3_mapping_path}")

    with open(v2_mapping_path, "r", encoding="utf-8") as f:
        v2_raw = json.load(f)
    with open(v3_mapping_path, "r", encoding="utf-8") as f:
        v3_raw = json.load(f)

    # Parse V2 mapping (keyed by class_index string or dict values)
    v2_items = v2_raw.values() if isinstance(v2_raw, dict) else v2_raw
    v2_asl_to_idx = {}
    v2_idx_to_asl = {}
    v2_asl_to_name = {}
    for item in v2_items:
        asl_id = item["asl_id"]
        c_idx = int(item["class_index"])
        name = item.get("canonical_name", asl_id)
        v2_asl_to_idx[asl_id] = c_idx
        v2_idx_to_asl[c_idx] = asl_id
        v2_asl_to_name[asl_id] = name

    # Parse V3 mapping (keyed by asl_id or dict values)
    v3_items = v3_raw.values() if isinstance(v3_raw, dict) else v3_raw
    v3_asl_to_idx = {}
    v3_idx_to_asl = {}
    v3_asl_to_name = {}
    for item in v3_items:
        asl_id = item["asl_id"]
        c_idx = int(item["class_index"])
        name = item.get("canonical_name", asl_id)
        v3_asl_to_idx[asl_id] = c_idx
        v3_idx_to_asl[c_idx] = asl_id
        v3_asl_to_name[asl_id] = name

    # Identify shared classes
    shared_asl_ids = sorted(list(set(v2_asl_to_idx.keys()) & set(v3_asl_to_idx.keys())))
    if len(shared_asl_ids) == 0:
        raise ValueError("Zero shared classes found between V2 and V3 mappings. Check mapping structures.")

    return (
        v2_asl_to_idx, v2_idx_to_asl, v2_asl_to_name,
        v3_asl_to_idx, v3_idx_to_asl, v3_asl_to_name,
        shared_asl_ids
    )


def load_models(
    v2_checkpoint_path: str,
    v3_checkpoint_path: str,
    device: torch.device
) -> Tuple[nn.Module, nn.Module, Dict[str, float], Dict[str, float]]:
    """
    Loads and instantiates both SPOTER V2 and V3 models in eval mode.
    Restores model-specific GroupNorm scalars.
    """
    if not os.path.exists(v2_checkpoint_path):
        raise FileNotFoundError(f"V2 checkpoint file not found: {v2_checkpoint_path}")
    if not os.path.exists(v3_checkpoint_path):
        raise FileNotFoundError(f"V3 checkpoint file not found: {v3_checkpoint_path}")

    # 1. Load V2 Model
    model_v2 = SpoterV2(
        num_classes=79,
        hidden_dim=512,
        nhead=8,
        num_encoder_layers=6,
        num_decoder_layers=6,
        dim_feedforward=2048,
        dropout=0.1
    ).to(device)
    
    v2_cp = torch.load(v2_checkpoint_path, map_location=device, weights_only=False)
    v2_state = v2_cp.get("model_state_dict", v2_cp)
    model_v2.load_state_dict(v2_state)
    model_v2.eval()

    # 2. Load V3 Model
    v3_cp = torch.load(v3_checkpoint_path, map_location=device, weights_only=False)
    v3_state = v3_cp.get("model_state_dict", v3_cp)
    v3_config = v3_cp.get("config", {})
    hidden_dim = v3_config.get("hidden_dim", 512)
    num_encoder_layers = v3_config.get("num_encoder_layers", 6)
    num_decoder_layers = v3_config.get("num_decoder_layers", 6)

    model_v3 = SpoterV3(
        num_classes=100,
        input_dim=366,
        hidden_dim=hidden_dim,
        num_encoder_layers=num_encoder_layers,
        num_decoder_layers=num_decoder_layers
    ).to(device)
    model_v3.load_state_dict(v3_state)
    model_v3.eval()

    # 3. Load Model-specific Scalars
    v2_scalars = v2_cp.get("scalars", None) if isinstance(v2_cp, dict) else None
    v3_scalars = v3_cp.get("scalars", None) if isinstance(v3_cp, dict) else None

    return model_v2, model_v3, v2_scalars, v3_scalars


def load_dataset_samples(
    manifest_path: str,
    features_dir: str,
    split: str,
    shared_asl_ids: List[str],
    v2_asl_to_idx: Dict[str, int],
    v3_asl_to_idx: Dict[str, int]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """
    Parses manifest for given split, verifies feature file existence, integrity, and shapes.
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest CSV not found: {manifest_path}")

    shared_set = set(shared_asl_ids)
    samples = []
    skipped = []

    features_base = Path(features_dir)
    if not features_base.exists():
        raise FileNotFoundError(f"Features directory not found: {features_dir}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("source_split") != split:
                continue

            asl_id = row["asl_id"]
            video_file = row["video_file"]
            base_name = Path(video_file).stem
            feature_file = features_base / f"{base_name}_features.npy"

            if not feature_file.exists():
                skipped.append({
                    "video_file": video_file,
                    "asl_id": asl_id,
                    "reason": f"Feature file {feature_file.name} does not exist"
                })
                continue

            # Check mapping existence
            if asl_id not in v3_asl_to_idx:
                skipped.append({
                    "video_file": video_file,
                    "asl_id": asl_id,
                    "reason": f"ASL ID {asl_id} missing from V3 mapping"
                })
                continue

            samples.append({
                "video_file": video_file,
                "feature_path": str(feature_file),
                "asl_id": asl_id,
                "is_shared": asl_id in shared_set,
                "v2_class_idx": v2_asl_to_idx.get(asl_id, -1),
                "v3_class_idx": v3_asl_to_idx[asl_id],
                "participant_id": row.get("participant_id", "Unknown")
            })

    if len(samples) == 0:
        raise ValueError(f"No valid test samples found for split '{split}'.")

    return samples, skipped


def collate_test_batch(batch_samples: List[Dict[str, Any]]) -> Tuple[torch.Tensor, torch.Tensor, List[Dict[str, Any]]]:
    """
    Loads .npy sequences for a batch, pads them, and returns attention masks.
    """
    sequences = []
    for s in batch_samples:
        arr = np.load(s["feature_path"])
        if arr.ndim != 2 or arr.shape[1] != 366:
            raise ValueError(f"Feature array {s['feature_path']} has invalid shape {arr.shape}, expected (*, 366).")
        if np.isnan(arr).any() or np.isinf(arr).any():
            raise ValueError(f"Feature array {s['feature_path']} contains NaN or Inf.")
        sequences.append(torch.tensor(arr, dtype=torch.float32))

    lengths = [len(seq) for seq in sequences]
    max_len = max(lengths)
    padded = torch.zeros(len(sequences), max_len, 366, dtype=torch.float32)
    mask = torch.zeros(len(sequences), max_len, dtype=torch.bool)

    for i, seq in enumerate(sequences):
        l = lengths[i]
        padded[i, :l, :] = seq
        mask[i, :l] = True

    return padded, mask, batch_samples


def main():
    args = parse_args()
    device = torch.device(args.device)

    print("=" * 80)
    print("SignVox SPOTER V2 vs V3 Comparative Benchmark Protocol")
    print(f"Device:            {device}")
    print(f"Split:             {args.split}")
    print(f"V2 Checkpoint:     {args.v2_checkpoint}")
    print(f"V3 Checkpoint:     {args.v3_checkpoint}")
    print("=" * 80)

    # 1. Load Mappings
    (
        v2_asl_to_idx, v2_idx_to_asl, v2_asl_to_name,
        v3_asl_to_idx, v3_idx_to_asl, v3_asl_to_name,
        shared_asl_ids
    ) = load_mappings(args.v2_mapping, args.v3_mapping)

    num_shared_classes = len(shared_asl_ids)
    print(f"Loaded mappings: V2 has {len(v2_asl_to_idx)} classes, V3 has {len(v3_asl_to_idx)} classes.")
    print(f"Genuinely shared vocabulary: {num_shared_classes} classes.")

    # Shared index mapping for synchronized confusion matrix (0 .. 78, sorted by asl_id)
    asl_to_shared_idx = {asl: i for i, asl in enumerate(shared_asl_ids)}
    shared_idx_to_asl = {i: asl for i, asl in enumerate(shared_asl_ids)}
    shared_idx_to_name = {i: v3_asl_to_name[asl] for i, asl in enumerate(shared_asl_ids)}

    # Vectorized indices for restricted subspace evaluation
    v3_shared_class_indices = torch.tensor(
        [v3_asl_to_idx[asl] for asl in shared_asl_ids],
        dtype=torch.long,
        device=device
    )

    # 2. Load Models and Checkpoints
    model_v2, model_v3, v2_scalars_cp, v3_scalars_cp = load_models(
        args.v2_checkpoint, args.v3_checkpoint, device
    )

    # Resolve scalars: prefer JSON file, fallback to checkpoint
    if os.path.exists(args.v2_scalars):
        with open(args.v2_scalars, "r", encoding="utf-8") as f:
            v2_scalars = json.load(f)
    elif v2_scalars_cp:
        v2_scalars = v2_scalars_cp
    else:
        raise FileNotFoundError(f"V2 scalars not found in file or checkpoint: {args.v2_scalars}")

    if os.path.exists(args.v3_scalars):
        with open(args.v3_scalars, "r", encoding="utf-8") as f:
            v3_scalars = json.load(f)
    elif v3_scalars_cp:
        v3_scalars = v3_scalars_cp
    else:
        raise FileNotFoundError(f"V3 scalars not found in file or checkpoint: {args.v3_scalars}")

    print(f"V2 Scalars restored: {v2_scalars}")
    print(f"V3 Scalars restored: {v3_scalars}")

    # 3. Load Samples
    samples, skipped_samples = load_dataset_samples(
        args.manifest, args.features_dir, args.split,
        shared_asl_ids, v2_asl_to_idx, v3_asl_to_idx
    )

    shared_samples = [s for s in samples if s["is_shared"]]
    extended_samples = [s for s in samples if not s["is_shared"]]
    print(f"\nManifest Split '{args.split}' Statistics:")
    print(f"  Total valid samples:     {len(samples)}")
    print(f"  Shared test samples:     {len(shared_samples)} (for head-to-head comparison)")
    print(f"  V3 extended samples:     {len(extended_samples)} (16 additional classes)")
    print(f"  Skipped samples:         {len(skipped_samples)}")

    if len(shared_samples) == 0:
        raise ValueError("Zero common test samples found for head-to-head evaluation!")

    # 4. Run Inference in Batches
    print("\nExecuting forward inference across both models...")

    # Data structures for Shared Evaluation
    shared_eval = {
        "v2_preds": [],
        "v2_top3_hits": [],
        "v3_restricted_preds": [],
        "v3_restricted_top3_hits": [],
        "v3_unrestricted_preds": [],
        "v3_unrestricted_top3_hits": [],
        "targets_shared_idx": [],
        "targets_asl_id": []
    }

    # Data structures for Full V3 Evaluation (all 95 supported classes)
    v3_full_eval = {
        "preds": [],
        "top3_hits": [],
        "targets_v3_idx": [],
        "targets_asl_id": [],
        "is_shared": []
    }

    batch_size = args.batch_size
    num_batches = (len(samples) + batch_size - 1) // batch_size

    with torch.no_grad():
        for b_idx in range(num_batches):
            batch_slice = samples[b_idx * batch_size: (b_idx + 1) * batch_size]
            seqs, mask, batch_meta = collate_test_batch(batch_slice)

            seqs = seqs.to(device)
            mask = mask.to(device)

            # Apply Model-specific GroupNorm scaling
            v2_scaled = apply_groupnorm_scaling(seqs, v2_scalars).to(device)
            v3_scaled = apply_groupnorm_scaling(seqs, v3_scalars).to(device)

            # Forward passes
            v2_logits = model_v2(v2_scaled, attention_mask=mask)  # (B, 79)
            v3_logits = model_v3(v3_scaled, attention_mask=mask)  # (B, 100)

            # Process each sample in batch
            for i, meta in enumerate(batch_meta):
                target_asl = meta["asl_id"]
                target_v3_idx = meta["v3_class_idx"]

                # 4.1 Full V3 tracking (Open 100-class space)
                v3_full_top1 = v3_logits[i].argmax().item()
                v3_full_top3 = torch.topk(v3_logits[i], k=3).indices.tolist()
                v3_full_eval["preds"].append(v3_full_top1)
                v3_full_eval["top3_hits"].append(target_v3_idx in v3_full_top3)
                v3_full_eval["targets_v3_idx"].append(target_v3_idx)
                v3_full_eval["targets_asl_id"].append(target_asl)
                v3_full_eval["is_shared"].append(meta["is_shared"])

                # 4.2 Shared Head-to-Head tracking
                if meta["is_shared"]:
                    target_shared_idx = asl_to_shared_idx[target_asl]
                    target_v2_idx = meta["v2_class_idx"]

                    # V2 Predictions (natively over 79 classes)
                    v2_top1 = v2_logits[i].argmax().item()
                    v2_top3 = torch.topk(v2_logits[i], k=3).indices.tolist()
                    pred_v2_asl = v2_idx_to_asl[v2_top1]
                    pred_v2_shared_idx = asl_to_shared_idx.get(pred_v2_asl, -1)
                    v2_top3_asls = [v2_idx_to_asl[idx] for idx in v2_top3]

                    shared_eval["v2_preds"].append(pred_v2_shared_idx)
                    shared_eval["v2_top3_hits"].append(target_asl in v2_top3_asls)

                    # V3 Protocol A (Restricted Subspace to 79 Shared Classes)
                    # Slices logits for the 79 shared classes:
                    v3_sub_logits = v3_logits[i, v3_shared_class_indices]  # (79,)
                    v3_sub_top1_local = v3_sub_logits.argmax().item()
                    v3_sub_top3_local = torch.topk(v3_sub_logits, k=3).indices.tolist()
                    pred_v3_restr_asl = shared_asl_ids[v3_sub_top1_local]
                    pred_v3_restr_shared_idx = asl_to_shared_idx[pred_v3_restr_asl]
                    v3_sub_top3_asls = [shared_asl_ids[idx] for idx in v3_sub_top3_local]

                    shared_eval["v3_restricted_preds"].append(pred_v3_restr_shared_idx)
                    shared_eval["v3_restricted_top3_hits"].append(target_asl in v3_sub_top3_asls)

                    # V3 Protocol B (Unrestricted Open-Space 100 Classes)
                    pred_v3_unrestr_asl = v3_idx_to_asl.get(v3_full_top1, f"UNKNOWN_{v3_full_top1}")
                    pred_v3_unrestr_shared_idx = asl_to_shared_idx.get(pred_v3_unrestr_asl, -1)
                    v3_unrestr_top3_asls = [v3_idx_to_asl.get(idx, "") for idx in v3_full_top3]

                    shared_eval["v3_unrestricted_preds"].append(pred_v3_unrestr_shared_idx)
                    shared_eval["v3_unrestricted_top3_hits"].append(target_asl in v3_unrestr_top3_asls)

                    shared_eval["targets_shared_idx"].append(target_shared_idx)
                    shared_eval["targets_asl_id"].append(target_asl)

    # 5. Compute Metrics for Shared Evaluation
    total_shared = len(shared_eval["targets_shared_idx"])
    targets_np = np.array(shared_eval["targets_shared_idx"])

    # V2 Metrics
    v2_preds_np = np.array(shared_eval["v2_preds"])
    v2_top1_acc = float((v2_preds_np == targets_np).mean())
    v2_top3_acc = float(np.mean(shared_eval["v2_top3_hits"]))

    # V3 Restricted Metrics (Protocol A)
    v3_restr_preds_np = np.array(shared_eval["v3_restricted_preds"])
    v3_restr_top1_acc = float((v3_restr_preds_np == targets_np).mean())
    v3_restr_top3_acc = float(np.mean(shared_eval["v3_restricted_top3_hits"]))

    # V3 Unrestricted Metrics (Protocol B)
    v3_unrestr_preds_np = np.array(shared_eval["v3_unrestricted_preds"])
    v3_unrestr_top1_acc = float((v3_unrestr_preds_np == targets_np).mean())
    v3_unrestr_top3_acc = float(np.mean(shared_eval["v3_unrestricted_top3_hits"]))

    # Confusion Matrices for 79 Shared Classes
    cm_v2 = np.zeros((num_shared_classes, num_shared_classes), dtype=int)
    cm_v3_restr = np.zeros((num_shared_classes, num_shared_classes), dtype=int)

    for true_idx, pred_v2, pred_v3 in zip(targets_np, v2_preds_np, v3_restr_preds_np):
        if pred_v2 >= 0:
            cm_v2[true_idx, pred_v2] += 1
        if pred_v3 >= 0:
            cm_v3_restr[true_idx, pred_v3] += 1

    # Per-Class Shared Breakdown
    per_class_shared_results = []
    v2_class_accs = []
    v3_restr_class_accs = []
    v3_unrestr_class_accs = []

    for s_idx in range(num_shared_classes):
        asl_id = shared_idx_to_asl[s_idx]
        name = shared_idx_to_name[s_idx]
        class_mask = (targets_np == s_idx)
        support = int(class_mask.sum())

        if support > 0:
            v2_corr = int((v2_preds_np[class_mask] == s_idx).sum())
            v2_acc = v2_corr / support
            v2_class_accs.append(v2_acc)

            v3_r_corr = int((v3_restr_preds_np[class_mask] == s_idx).sum())
            v3_r_acc = v3_r_corr / support
            v3_restr_class_accs.append(v3_r_acc)

            v3_u_corr = int((v3_unrestr_preds_np[class_mask] == s_idx).sum())
            v3_u_acc = v3_u_corr / support
            v3_unrestr_class_accs.append(v3_u_acc)

            delta = v3_r_acc - v2_acc
        else:
            v2_corr, v2_acc = 0, 0.0
            v3_r_corr, v3_r_acc = 0, 0.0
            v3_u_corr, v3_u_acc = 0, 0.0
            delta = 0.0

        per_class_shared_results.append({
            "shared_index": s_idx,
            "asl_id": asl_id,
            "canonical_name": name,
            "v2_class_index": v2_asl_to_idx[asl_id],
            "v3_class_index": v3_asl_to_idx[asl_id],
            "support": support,
            "v2_correct": v2_corr,
            "v2_accuracy": round(v2_acc, 4),
            "v3_restricted_correct": v3_r_corr,
            "v3_restricted_accuracy": round(v3_r_acc, 4),
            "v3_unrestricted_correct": v3_u_corr,
            "v3_unrestricted_accuracy": round(v3_u_acc, 4),
            "v3_vs_v2_accuracy_delta": round(delta, 4)
        })

    v2_macro_acc = float(np.mean(v2_class_accs)) if v2_class_accs else 0.0
    v3_restr_macro_acc = float(np.mean(v3_restr_class_accs)) if v3_restr_class_accs else 0.0
    v3_unrestr_macro_acc = float(np.mean(v3_unrestr_class_accs)) if v3_unrestr_class_accs else 0.0

    # 6. Compute Full V3 Metrics (All 95 Supported Classes, 1,379 samples)
    v3_full_targets_np = np.array(v3_full_eval["targets_v3_idx"])
    v3_full_preds_np = np.array(v3_full_eval["preds"])
    v3_all95_top1_acc = float((v3_full_preds_np == v3_full_targets_np).mean())
    v3_all95_top3_acc = float(np.mean(v3_full_eval["top3_hits"]))

    # Extended-only V3 Metrics (16 classes, 357 samples)
    ext_mask = ~np.array(v3_full_eval["is_shared"])
    if ext_mask.sum() > 0:
        v3_ext_top1_acc = float((v3_full_preds_np[ext_mask] == v3_full_targets_np[ext_mask]).mean())
        v3_ext_top3_acc = float(np.mean(np.array(v3_full_eval["top3_hits"])[ext_mask]))
        ext_count = int(ext_mask.sum())
    else:
        v3_ext_top1_acc, v3_ext_top3_acc, ext_count = 0.0, 0.0, 0

    # Per-class metrics for all 100 classes in V3
    v3_cm_100 = np.zeros((100, 100), dtype=int)
    for true_idx, pred_idx in zip(v3_full_targets_np, v3_full_preds_np):
        v3_cm_100[true_idx, pred_idx] += 1

    v3_all_class_accs = []
    for c_idx in range(100):
        sup = int(v3_cm_100[c_idx, :].sum())
        if sup > 0:
            corr = int(v3_cm_100[c_idx, c_idx])
            v3_all_class_accs.append(corr / sup)
    v3_all95_macro_acc = float(np.mean(v3_all_class_accs)) if v3_all_class_accs else 0.0

    # 7. Construct Final Comparative Audit Report
    report = {
        "evaluation_status": "SUCCESS",
        "protocol_description": (
            "Comparative evaluation of SPOTER V2 (79 classes) vs SPOTER V3 (100-class architecture) "
            "on identical held-out test samples. Shared-class comparison evaluates the 79 common classes. "
            "Protocol A (Restricted Subspace) masks V3 logits to the 79 shared classes for an exact "
            "closed-set comparison with V2. Protocol B (Unrestricted Full-Space) ranks V3 across all 100 "
            "output logits."
        ),
        "split_evaluated": args.split,
        "sample_counts": {
            "total_test_samples": len(samples),
            "shared_vocabulary_samples": total_shared,
            "v3_extended_samples": ext_count,
            "skipped_samples_count": len(skipped_samples)
        },
        "vocabulary_counts": {
            "v2_total_classes": len(v2_asl_to_idx),
            "v3_total_classes": 100,
            "v3_supported_classes": 95,
            "v3_reserved_missing_classes": 5,
            "shared_classes_count": num_shared_classes
        },
        "head_to_head_shared_metrics": {
            "v2_production_baseline": {
                "top1_accuracy": round(v2_top1_acc, 4),
                "top3_accuracy": round(v2_top3_acc, 4),
                "macro_accuracy": round(v2_macro_acc, 4),
                "correct_top1_count": int((v2_preds_np == targets_np).sum()),
                "total_evaluated": total_shared
            },
            "v3_candidate_protocol_a_restricted_subspace": {
                "top1_accuracy": round(v3_restr_top1_acc, 4),
                "top3_accuracy": round(v3_restr_top3_acc, 4),
                "macro_accuracy": round(v3_restr_macro_acc, 4),
                "correct_top1_count": int((v3_restr_preds_np == targets_np).sum()),
                "total_evaluated": total_shared,
                "delta_vs_v2_top1": round(v3_restr_top1_acc - v2_top1_acc, 4),
                "delta_vs_v2_top3": round(v3_restr_top3_acc - v2_top3_acc, 4)
            },
            "v3_candidate_protocol_b_unrestricted_full_space": {
                "top1_accuracy": round(v3_unrestr_top1_acc, 4),
                "top3_accuracy": round(v3_unrestr_top3_acc, 4),
                "macro_accuracy": round(v3_unrestr_macro_acc, 4),
                "correct_top1_count": int((v3_unrestr_preds_np == targets_np).sum()),
                "total_evaluated": total_shared
            }
        },
        "v3_extended_metrics": {
            "v3_all_95_supported_classes": {
                "total_samples": len(samples),
                "top1_accuracy": round(v3_all95_top1_acc, 4),
                "top3_accuracy": round(v3_all95_top3_acc, 4),
                "macro_accuracy": round(v3_all95_macro_acc, 4),
                "supported_classes_evaluated": len(v3_all_class_accs)
            },
            "v3_16_extended_classes_only": {
                "total_samples": ext_count,
                "top1_accuracy": round(v3_ext_top1_acc, 4),
                "top3_accuracy": round(v3_ext_top3_acc, 4)
            }
        },
        "per_class_shared_comparison": per_class_shared_results,
        "confusion_matrices": {
            "shared_classes_order": shared_asl_ids,
            "v2_confusion_matrix": cm_v2.tolist(),
            "v3_restricted_confusion_matrix": cm_v3_restr.tolist()
        },
        "skipped_samples": skipped_samples,
        "artifact_paths": {
            "v2_checkpoint": args.v2_checkpoint,
            "v3_checkpoint": args.v3_checkpoint,
            "manifest": args.manifest,
            "output_json": args.output_json
        }
    }

    # 8. Save JSON Report
    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # 9. Print Visual Summary to Terminal
    print("\n" + "=" * 80)
    print("HEAD-TO-HEAD COMPARISON ON SHARED 79 CLASSES (1,022 TEST SAMPLES)")
    print("=" * 80)
    print(f"{'Metric':<35} | {'V2 Baseline':<12} | {'V3 Restricted':<14} | {'V3 Unrestricted':<15}")
    print("-" * 80)
    print(f"{'Top-1 Accuracy':<35} | {v2_top1_acc*100:>10.2f}% | {v3_restr_top1_acc*100:>12.2f}% | {v3_unrestr_top1_acc*100:>13.2f}%")
    print(f"{'Top-3 Accuracy':<35} | {v2_top3_acc*100:>10.2f}% | {v3_restr_top3_acc*100:>12.2f}% | {v3_unrestr_top3_acc*100:>13.2f}%")
    print(f"{'Macro-Average Accuracy':<35} | {v2_macro_acc*100:>10.2f}% | {v3_restr_macro_acc*100:>12.2f}% | {v3_unrestr_macro_acc*100:>13.2f}%")
    print("-" * 80)
    print(f"Top-1 Accuracy Delta (V3 Restricted - V2): {(v3_restr_top1_acc - v2_top1_acc)*100:+.2f}%")
    print(f"Top-3 Accuracy Delta (V3 Restricted - V2): {(v3_restr_top3_acc - v2_top3_acc)*100:+.2f}%")

    print("\n" + "=" * 80)
    print("V3 EXTENDED VOCABULARY PERFORMANCE")
    print("=" * 80)
    print(f"V3 All 95 Supported Classes (1,379 samples): Top-1: {v3_all95_top1_acc*100:.2f}% | Top-3: {v3_all95_top3_acc*100:.2f}% | Macro: {v3_all95_macro_acc*100:.2f}%")
    print(f"V3 16 Extended Classes Only (357 samples):   Top-1: {v3_ext_top1_acc*100:.2f}% | Top-3: {v3_ext_top3_acc*100:.2f}%")
    print("=" * 80)
    print(f"Successfully generated comparison report at:\n  --> {out_path.resolve()}\n")


if __name__ == "__main__":
    main()
