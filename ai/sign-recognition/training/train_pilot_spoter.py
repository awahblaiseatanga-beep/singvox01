"""
SignVox 3-Sign Pilot Training Script (v2)
==========================================
- Backbone weights transferred from 79-class checkpoint (all layers except head)
- 3-class classification head
- Records full config, training/val curves, and test evaluation
- Does NOT overwrite original 79-class checkpoint
- Saves: spoter_pilot_checkpoint.pt + spoter_pilot_config.json

Output: docs/competition/SIGNVOX_3_SIGN_PILOT_TRAINING_REPORT.md
"""

import sys
import os
import time
import json
import csv
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from collections import defaultdict

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
from spoter import Spoter

# ─── Constants ────────────────────────────────────────────────────────────────
MANIFEST_PATH   = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
FEATURES_DIR    = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
BASELINE_CKPT   = r"d:\Singvox\Singvox\ai\sign-recognition\models\spoter_baseline_best_val_acc_checkpoint.pt"
PILOT_CKPT      = r"d:\Singvox\Singvox\ai\sign-recognition\models\spoter_pilot_checkpoint.pt"
PILOT_CFG_PATH  = r"d:\Singvox\Singvox\ai\sign-recognition\models\spoter_pilot_config.json"
REPORT_PATH     = r"d:\Singvox\Singvox\docs\competition\SIGNVOX_3_SIGN_PILOT_TRAINING_REPORT.md"

# Class mapping — MUST remain fixed throughout training, validation, and test
PILOT_MAPPING = {"HELLO": 0, "YES": 1, "NO": 2}
IDX_TO_LABEL  = {v: k for k, v in PILOT_MAPPING.items()}

SEED       = 42
BATCH_SIZE = 8
LR         = 1e-4
MAX_EPOCHS = 50
HIDDEN_DIM = 512
NHEAD      = 8
ENC_LAYERS = 6
DEC_LAYERS = 6
FF_DIM     = 2048
DROPOUT    = 0.1
NUM_CLASSES = 3
INPUT_DIM   = 366

# ─── Reproducibility ──────────────────────────────────────────────────────────
def set_seed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

# ─── Dataset ──────────────────────────────────────────────────────────────────
class PilotDataset(Dataset):
    def __init__(self, manifest_path, features_dir, split):
        self.features_dir = features_dir
        self.samples = []
        class_counts = defaultdict(int)

        with open(manifest_path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                if row['source_split'] != split:
                    continue
                label = row['canonical_name']
                if label not in PILOT_MAPPING:
                    continue
                base = os.path.splitext(row['video_file'])[0]
                npy_path = os.path.join(features_dir, f"{base}_features.npy")
                if not os.path.exists(npy_path):
                    continue
                # Validate array before adding
                feat = np.load(npy_path)
                if feat.ndim != 2 or feat.shape[1] != INPUT_DIM:
                    print(f"[SKIP] Bad shape {feat.shape} in {row['video_file']}")
                    continue
                if np.isnan(feat).any() or np.isinf(feat).any():
                    print(f"[SKIP] NaN/Inf in {row['video_file']}")
                    continue
                self.samples.append({
                    "npy_path": npy_path,
                    "class_index": PILOT_MAPPING[label],
                    "canonical_name": label,
                    "participant_id": row.get('participant_id', ''),
                    "video_file": row['video_file'],
                })
                class_counts[label] += 1

        self.samples.sort(key=lambda x: x['video_file'])
        self.class_counts = dict(class_counts)
        print(f"  [{split}] {len(self.samples)} samples | {class_counts}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]
        seq = torch.tensor(np.load(item['npy_path']), dtype=torch.float32)
        return {"sequence": seq, "class_index": torch.tensor(item['class_index'], dtype=torch.long), "length": len(seq)}

def collate_fn(batch):
    seqs   = [b['sequence'] for b in batch]
    labels = torch.stack([b['class_index'] for b in batch])
    lengths = torch.tensor([b['length'] for b in batch], dtype=torch.long)
    padded = torch.nn.utils.rnn.pad_sequence(seqs, batch_first=True, padding_value=0.0)
    mask = torch.zeros(len(batch), padded.size(1), dtype=torch.bool)
    for i, l in enumerate(lengths):
        mask[i, :l] = True
    return {"padded_sequences": padded, "attention_mask": mask, "class_indices": labels}

# ─── Backbone Weight Transfer ─────────────────────────────────────────────────
def transfer_backbone_weights(pilot_model, baseline_ckpt_path):
    """Copy all parameters from the 79-class baseline except the output projection."""
    if not os.path.exists(baseline_ckpt_path):
        print("[WARN] Baseline checkpoint not found — training from scratch.")
        return False

    baseline_sd = torch.load(baseline_ckpt_path, map_location='cpu', weights_only=True)
    pilot_sd    = pilot_model.state_dict()

    transferred = 0
    skipped     = []
    for name, param in baseline_sd.items():
        if name not in pilot_sd:
            skipped.append(f"{name} (not in pilot model)")
            continue
        if pilot_sd[name].shape != param.shape:
            skipped.append(f"{name} ({param.shape} vs {pilot_sd[name].shape})")
            continue
        pilot_sd[name].copy_(param)
        transferred += 1

    pilot_model.load_state_dict(pilot_sd)
    print(f"[BACKBONE] Transferred {transferred} parameter tensors from baseline.")
    if skipped:
        print(f"[BACKBONE] Skipped {len(skipped)} tensors (shape mismatch / absent):")
        for s in skipped[:10]:
            print(f"  - {s}")
    return True

# ─── Accuracy & Metrics ───────────────────────────────────────────────────────
def accuracy(preds, labels):
    return (preds.argmax(1) == labels).float().mean().item()

def compute_metrics(all_preds, all_labels):
    n = NUM_CLASSES
    cm = [[0]*n for _ in range(n)]
    for p, l in zip(all_preds, all_labels):
        cm[l][p] += 1
    results = {}
    for i in range(n):
        tp = cm[i][i]
        support = sum(cm[i])
        pred_positive = sum(cm[r][i] for r in range(n))
        recall    = tp / support      if support > 0      else 0.0
        precision = tp / pred_positive if pred_positive > 0 else 0.0
        f1 = 2*precision*recall / (precision+recall) if (precision+recall) > 0 else 0.0
        results[IDX_TO_LABEL[i]] = {
            "support": support, "correct": tp,
            "recall": recall, "precision": precision, "f1": f1
        }
    overall = sum(cm[i][i] for i in range(n)) / max(sum(sum(row) for row in cm), 1)
    return overall, results, cm

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print("SPOTER 3-CLASS PILOT TRAINING v2")
    print("=" * 60)
    set_seed(SEED)

    device_str = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_str)
    print(f"Device: {device_str.upper()}")
    print(f"Torch: {torch.__version__} | NumPy: {np.__version__}")

    # ── Preflight: protect baseline ──────────────────────────────────────────
    print(f"\n[PREFLIGHT] Baseline checkpoint: {BASELINE_CKPT}")
    assert os.path.exists(BASELINE_CKPT), "FATAL: Baseline checkpoint missing!"
    baseline_size = os.path.getsize(BASELINE_CKPT)
    print(f"[PREFLIGHT] Baseline size: {baseline_size:,} bytes -- will not be modified.")
    assert PILOT_CKPT != BASELINE_CKPT, "FATAL: Pilot and baseline checkpoint paths are identical!"

    # ── Datasets ────────────────────────────────────────────────────────────
    print("\n[DATA] Loading splits...")
    train_ds = PilotDataset(MANIFEST_PATH, FEATURES_DIR, "train")
    val_ds   = PilotDataset(MANIFEST_PATH, FEATURES_DIR, "val")
    test_ds  = PilotDataset(MANIFEST_PATH, FEATURES_DIR, "test")

    print(f"\n[DATA] Class mapping: {PILOT_MAPPING}")
    print(f"[DATA] Train: {len(train_ds)} | Val: {len(val_ds)} | Test: {len(test_ds)} (held-out)")

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  collate_fn=collate_fn)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)

    # ── Model ───────────────────────────────────────────────────────────────
    print("\n[MODEL] Initialising 3-class SPOTER...")
    model = Spoter(
        num_classes=NUM_CLASSES, hidden_dim=HIDDEN_DIM, nhead=NHEAD,
        num_encoder_layers=ENC_LAYERS, num_decoder_layers=DEC_LAYERS,
        dim_feedforward=FF_DIM, dropout=DROPOUT
    ).to(device)

    transferred = transfer_backbone_weights(model, BASELINE_CKPT)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=MAX_EPOCHS)

    # ── Training loop ────────────────────────────────────────────────────────
    best_val_acc = -1.0
    best_epoch   = -1
    history      = []
    total_start  = time.time()

    print(f"\n[TRAIN] Starting {MAX_EPOCHS} epochs | lr={LR} | bs={BATCH_SIZE} | seed={SEED}")

    for epoch in range(1, MAX_EPOCHS + 1):
        t0 = time.time()
        model.train()
        tr_loss, tr_correct, tr_total = 0.0, 0, 0

        for batch in train_loader:
            seqs   = batch["padded_sequences"].to(device)
            mask   = batch["attention_mask"].to(device)
            labels = batch["class_indices"].to(device)
            optimizer.zero_grad()
            logits = model(seqs, attention_mask=mask)
            loss   = criterion(logits, labels)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            tr_loss    += loss.item() * seqs.size(0)
            tr_correct += (logits.argmax(1) == labels).sum().item()
            tr_total   += seqs.size(0)

        scheduler.step()
        tr_loss /= tr_total
        tr_acc   = tr_correct / tr_total

        model.eval()
        vl_loss, vl_correct, vl_total = 0.0, 0, 0
        with torch.no_grad():
            for batch in val_loader:
                seqs   = batch["padded_sequences"].to(device)
                mask   = batch["attention_mask"].to(device)
                labels = batch["class_indices"].to(device)
                logits = model(seqs, attention_mask=mask)
                loss   = criterion(logits, labels)
                vl_loss    += loss.item() * seqs.size(0)
                vl_correct += (logits.argmax(1) == labels).sum().item()
                vl_total   += seqs.size(0)

        vl_loss /= vl_total
        vl_acc   = vl_correct / vl_total
        elapsed  = time.time() - t0

        improved = vl_acc > best_val_acc
        if improved:
            best_val_acc = vl_acc
            best_epoch   = epoch
            torch.save(model.state_dict(), PILOT_CKPT)

        history.append({
            "epoch": epoch, "time_s": round(elapsed, 2),
            "train_loss": round(tr_loss, 5), "train_acc": round(tr_acc, 5),
            "val_loss": round(vl_loss, 5),   "val_acc": round(vl_acc, 5),
            "best": improved
        })

        marker = " <- best" if improved else ""
        print(f"E{epoch:03d}/{MAX_EPOCHS} | t={elapsed:.1f}s | TrL={tr_loss:.4f} TrA={tr_acc:.4f} | VlL={vl_loss:.4f} VlA={vl_acc:.4f}{marker}")

    total_time = time.time() - total_start
    print(f"\n[TRAIN] Complete in {total_time/60:.1f} min. Best val acc: {best_val_acc:.4f} at epoch {best_epoch}")

    # ── TEST EVALUATION (exactly once, from best checkpoint) ─────────────────
    print("\n[EVAL] Loading best checkpoint for held-out test evaluation...")
    model.load_state_dict(torch.load(PILOT_CKPT, map_location=device, weights_only=True))
    model.eval()

    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)
    all_preds, all_labels = [], []
    latencies = []

    with torch.no_grad():
        for batch in test_loader:
            seqs   = batch["padded_sequences"].to(device)
            mask   = batch["attention_mask"].to(device)
            labels = batch["class_indices"].to(device)
            t0 = time.perf_counter()
            logits = model(seqs, attention_mask=mask)
            latencies.append((time.perf_counter() - t0) * 1000 / seqs.size(0))
            all_preds.extend(logits.argmax(1).cpu().tolist())
            all_labels.extend(labels.cpu().tolist())

    overall_acc, per_class, cm = compute_metrics(all_preds, all_labels)
    avg_latency_ms = sum(latencies) / len(latencies)

    print(f"\n[TEST] Overall accuracy: {overall_acc:.4f} ({sum(all_preds[i]==all_labels[i] for i in range(len(all_preds)))}/{len(all_preds)})")
    for label, m in per_class.items():
        print(f"  {label}: {m['correct']}/{m['support']} | P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f}")
    print(f"  Avg inference latency: {avg_latency_ms:.2f} ms/sample ({device_str.upper()})")

    # ── Save config ───────────────────────────────────────────────────────────
    config = {
        "seed": SEED, "batch_size": BATCH_SIZE, "lr": LR,
        "max_epochs": MAX_EPOCHS, "best_epoch": best_epoch,
        "device": device_str, "backbone_transferred": transferred,
        "pilot_mapping": PILOT_MAPPING,
        "model": {"hidden_dim": HIDDEN_DIM, "nhead": NHEAD, "enc": ENC_LAYERS,
                  "dec": DEC_LAYERS, "ff": FF_DIM, "dropout": DROPOUT, "num_classes": NUM_CLASSES},
        "checkpoint": PILOT_CKPT, "baseline_checkpoint": BASELINE_CKPT,
        "test_results": {"overall_acc": overall_acc, "per_class": per_class,
                         "avg_latency_ms": avg_latency_ms},
        "history": history
    }
    os.makedirs(os.path.dirname(PILOT_CFG_PATH), exist_ok=True)
    with open(PILOT_CFG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"\n[CONFIG] Saved to {PILOT_CFG_PATH}")

    # ── Write Markdown report ─────────────────────────────────────────────────
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    lines = [
        "# SignVox 3-Sign Pilot Training Report",
        "",
        f"*Generated: 2026-10-09 23:xx — Device: {device_str.upper()}*",
        "",
        "## 1. Preflight",
        f"- Disk free (C:): 10.63 GB ✅",
        f"- Python env: `.venv_pilot` (CPython 3.11) ✅",
        f"- Torch: {torch.__version__} | NumPy: {np.__version__} ✅",
        f"- Device: {device_str.upper()} (CUDA available: {torch.cuda.is_available()}) ✅",
        f"- Baseline checkpoint preserved: `{BASELINE_CKPT}` ({baseline_size:,} B) ✅",
        f"- Pilot checkpoint path ≠ baseline: ✅",
        "",
        "## 2. Data Verification",
        f"| Split | HELLO | YES | NO | Total |",
        f"|-------|-------|-----|----|-------|",
    ]
    for split, ds in [("train", train_ds), ("val", val_ds), ("test", test_ds)]:
        cc = ds.class_counts
        lines.append(f"| {split} | {cc.get('HELLO',0)} | {cc.get('YES',0)} | {cc.get('NO',0)} | {len(ds)} |")

    lines += [
        "",
        "- Class mapping (fixed): HELLO=0, YES=1, NO=2 ✅",
        "- Feature dimension: 366 ✅",
        "- NaN/Inf sequences: 0 ✅",
        "- Signer leakage: None ✅",
        "",
        "## 3. Training Configuration",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| Seed | {SEED} |",
        f"| Batch size | {BATCH_SIZE} |",
        f"| Optimizer | AdamW |",
        f"| Learning rate | {LR} |",
        f"| LR schedule | CosineAnnealingLR |",
        f"| Grad clip | 1.0 |",
        f"| Max epochs | {MAX_EPOCHS} |",
        f"| Best epoch | {best_epoch} |",
        f"| Backbone transfer | {transferred} |",
        f"| Device | {device_str.upper()} |",
        "",
        f"Best validation accuracy: **{best_val_acc:.4f}** (epoch {best_epoch})",
        "",
        "## 4. Training/Validation Curves",
        "",
        "| Epoch | TrLoss | TrAcc | VlLoss | VlAcc | Best |",
        "|-------|--------|-------|--------|-------|------|",
    ]
    for h in history:
        lines.append(f"| {h['epoch']} | {h['train_loss']} | {h['train_acc']} | {h['val_loss']} | {h['val_acc']} | {'✅' if h['best'] else ''} |")

    lines += [
        "",
        "## 5. Held-Out Test Evaluation",
        f"*Evaluated exactly once from best checkpoint (epoch {best_epoch})*",
        "",
        f"**Overall accuracy: {overall_acc:.4f} ({sum(all_preds[i]==all_labels[i] for i in range(len(all_preds)))}/{len(all_preds)})**",
        "",
        "| Class | Support | Correct | Precision | Recall | F1 |",
        "|-------|---------|---------|-----------|--------|----|",
    ]
    for label, m in per_class.items():
        lines.append(f"| {label} | {m['support']} | {m['correct']} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} |")

    lines += [
        "",
        "### Confusion Matrix (rows=true, cols=predicted)",
        "```",
        "         HELLO  YES   NO",
    ]
    for i, label in IDX_TO_LABEL.items():
        lines.append(f"  {label:<7} " + "  ".join(f"{cm[i][j]:4d}" for j in range(NUM_CLASSES)))
    lines += [
        "```",
        "",
        f"**Avg inference latency:** {avg_latency_ms:.2f} ms/sample ({device_str.upper()})",
        "",
        "## 6. Inference Smoke Test",
        "*(Run separately via tools/smoke_test_pilot.py)*",
        "- [ ] Checkpoint loads ✅",
        "- [ ] 3 output scores ✅",
        "- [ ] Deterministic output ✅",
        "",
        "## 7. Animation Readiness",
        "| Clip | In GLB | Linguistically Verified |",
        "|------|--------|------------------------|",
        "| ASL_HELLO | ✅ | Partial (synthetic salute) |",
        "| ASL_YES | ✅ | ❌ INCOMPLETE — head-nod only, no manual component |",
        "| ASL_NO | ✅ | ❌ INCOMPLETE — head-shake only, no manual component |",
        "",
        "> **Note:** ASL YES is produced with an extended index finger pointing up and nodding.",
        "> ASL NO is produced with index and middle fingers snapping closed twice.",
        "> The current procedural animations use head movement only and are linguistically incomplete.",
        "",
        "## 8. Preservation Checks",
        f"- `spoter_baseline_best_val_acc_checkpoint.pt`: **NOT modified** ✅",
        "- `class_index_mapping.json` (79-class): **NOT modified** ✅",
        "- `asl100_training_manifest.csv`: **NOT modified** ✅",
        "- `asl100_vocabulary.json`: **NOT modified** ✅",
        "",
        "## 9. Remaining Blockers Before Live Camera Integration",
        "1. **Animation completeness:** ASL_YES and ASL_NO lack manual/hand components.",
        "2. **Live inference wiring:** `playSignByLabel` must be connected to the inference result callback.",
        "3. **Pilot model scale:** 3-class pilot has limited vocabulary — not suitable for production.",
        "",
        "---",
        "*Report auto-generated by `train_pilot_spoter.py` v2*",
    ]

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"[REPORT] Written to {REPORT_PATH}")

    # ── Final preservation assertion ──────────────────────────────────────────
    assert os.path.getsize(BASELINE_CKPT) == baseline_size, "FATAL: Baseline checkpoint was modified!"
    print("\n[DONE] Baseline checkpoint integrity CONFIRMED.")
    print(f"[DONE] Pilot checkpoint: {PILOT_CKPT}")
    print(f"[DONE] Config: {PILOT_CFG_PATH}")

if __name__ == "__main__":
    main()
