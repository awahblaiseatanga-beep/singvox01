"""
SignVox SPOTER V3 Standalone Evaluation Script
Evaluates a trained SPOTER V3 checkpoint across 100 canonical classes.
Computes Top-1, Top-3, Macro accuracy, per-class accuracy, and confusion matrix.
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn

SCRIPT_DIR = Path(__file__).resolve().parent
EXP_DIR = SCRIPT_DIR.parent
ROOT_DIR = EXP_DIR.parent.parent

sys.path.append(str(EXP_DIR / "models"))
sys.path.append(str(SCRIPT_DIR))

from spoter_v3 import SpoterV3
from dataloaders_v3 import (
    SpoterV3Dataset,
    spoter_v3_collate_fn,
    apply_groupnorm_scaling
)
from torch.utils.data import DataLoader

def parse_args():
    parser = argparse.ArgumentParser(description="SignVox SPOTER V3 Evaluation Script")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to checkpoint .pt")
    parser.add_argument("--split", type=str, default="test", choices=["train", "val", "test"], help="Dataset split")
    parser.add_argument("--manifest_path", type=str, default=str(EXP_DIR / "manifests" / "spoter_v3_matched_manifest.csv"))
    parser.add_argument("--features_dir", type=str, default=str(ROOT_DIR / "ai" / "sign-recognition" / "data" / "dataset_extracted"))
    parser.add_argument("--mapping_path", type=str, default=str(EXP_DIR / "config" / "asl100_v3_class_mapping.json"))
    parser.add_argument("--output_json", type=str, default=None, help="Path to save evaluation report JSON")
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()

def main():
    args = parse_args()
    print("=" * 70)
    print("SignVox SPOTER V3 Evaluation Protocol")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Evaluating Split: {args.split}")
    print("=" * 70)
    
    # 1. Load Checkpoint
    checkpoint = torch.load(args.checkpoint, map_location=args.device, weights_only=False)
    scalars = checkpoint.get("scalars", {"left_hand": 1.0, "right_hand": 1.0, "pose_xyz": 1.0, "face": 1.0})
    
    # 2. Instantiate Model
    config = checkpoint.get("config", {})
    hidden_dim = config.get("hidden_dim", 512)
    num_encoder_layers = config.get("num_encoder_layers", 6)
    num_decoder_layers = config.get("num_decoder_layers", 6)
    
    model = SpoterV3(
        num_classes=100,
        input_dim=366,
        hidden_dim=hidden_dim,
        num_encoder_layers=num_encoder_layers,
        num_decoder_layers=num_decoder_layers
    ).to(args.device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    
    # 3. Load Mapping
    with open(args.mapping_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    index_to_name = {data["class_index"]: data["canonical_name"] for data in mapping.values()}
    index_to_asl = {data["class_index"]: data["asl_id"] for data in mapping.values()}
    
    # 4. Load Dataset
    dataset = SpoterV3Dataset(args.manifest_path, args.features_dir, args.mapping_path, split=args.split)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, collate_fn=spoter_v3_collate_fn)
    print(f"Loaded {len(dataset)} samples for split '{args.split}'.")
    
    all_preds = []
    all_labels = []
    all_top3_correct = 0
    total = 0
    
    with torch.no_grad():
        for batch in loader:
            seqs = batch["padded_sequences"].to(args.device)
            mask = batch["attention_mask"].to(args.device)
            targets = batch["class_indices"].to(args.device)
            
            scaled_seqs = apply_groupnorm_scaling(seqs, scalars).to(args.device)
            logits = model(scaled_seqs, attention_mask=mask)
            
            preds = logits.argmax(dim=-1)
            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(targets.cpu().tolist())
            
            top3 = torch.topk(logits, k=3, dim=-1).indices
            targets_exp = targets.unsqueeze(-1).expand_as(top3)
            all_top3_correct += (top3 == targets_exp).any(dim=-1).sum().item()
            total += targets.size(0)
            
    # Metrics
    num_classes = 100
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for p, l in zip(all_preds, all_labels):
        cm[l, p] += 1
        
    per_class_results = []
    per_class_accs = []
    
    for i in range(num_classes):
        support = int(cm[i, :].sum())
        correct = int(cm[i, i])
        acc = (correct / support) if support > 0 else None
        if acc is not None:
            per_class_accs.append(acc)
            
        cname = index_to_name.get(i, f"CLASS_{i}")
        asl_id = index_to_asl.get(i, f"ASL_{i:03d}")
        per_class_results.append({
            "class_index": i,
            "asl_id": asl_id,
            "canonical_name": cname,
            "support": support,
            "correct": correct,
            "accuracy": round(acc, 4) if acc is not None else "N/A"
        })
        
    top1_acc = (np.array(all_preds) == np.array(all_labels)).mean() if total > 0 else 0.0
    top3_acc = (all_top3_correct / total) if total > 0 else 0.0
    macro_acc = np.mean(per_class_accs) if per_class_accs else 0.0
    
    report = {
        "checkpoint": args.checkpoint,
        "split": args.split,
        "total_samples": total,
        "overall_top1_accuracy": round(float(top1_acc), 4),
        "overall_top3_accuracy": round(float(top3_acc), 4),
        "macro_average_accuracy": round(float(macro_acc), 4),
        "evaluated_classes_count": len(per_class_accs),
        "total_classes": num_classes,
        "per_class_metrics": per_class_results
    }
    
    print("\n" + "=" * 70)
    print(f"EVALUATION SUMMARY ({args.split.upper()} SPLIT)")
    print(f"Total Samples: {total}")
    print(f"Top-1 Overall Accuracy: {top1_acc*100:.2f}%")
    print(f"Top-3 Overall Accuracy: {top3_acc*100:.2f}%")
    print(f"Macro Average Accuracy: {macro_acc*100:.2f}%")
    print("=" * 70)
    
    if args.output_json:
        out_p = Path(args.output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Saved evaluation report to {out_p}")

if __name__ == "__main__":
    main()
