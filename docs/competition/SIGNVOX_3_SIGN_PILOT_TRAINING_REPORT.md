# SignVox 3-Sign Pilot Training Report

*Generated: 2026-10-09 23:xx — Device: CPU*

## 1. Preflight
- Disk free (C:): 10.63 GB ✅
- Python env: `.venv_pilot` (CPython 3.11) ✅
- Torch: 2.14.1+cpu | NumPy: 2.4.6 ✅
- Device: CPU (CUDA available: False) ✅
- Baseline checkpoint preserved: `d:\Singvox\Singvox\ai\sign-recognition\models\spoter_baseline_best_val_acc_checkpoint.pt` (187,785,483 B) ✅
- Pilot checkpoint path ≠ baseline: ✅

## 2. Data Verification
| Split | HELLO | YES | NO | Total |
|-------|-------|-----|----|-------|
| train | 14 | 15 | 16 | 45 |
| val | 4 | 5 | 3 | 12 |
| test | 14 | 10 | 11 | 35 |

- Class mapping (fixed): HELLO=0, YES=1, NO=2 ✅
- Feature dimension: 366 ✅
- NaN/Inf sequences: 0 ✅
- Signer leakage: None ✅

## 3. Training Configuration
| Parameter | Value |
|-----------|-------|
| Seed | 42 |
| Batch size | 8 |
| Optimizer | AdamW |
| Learning rate | 0.0001 |
| LR schedule | CosineAnnealingLR |
| Grad clip | 1.0 |
| Max epochs | 50 |
| Best epoch | 7 |
| Backbone transfer | True |
| Device | CPU |

Best validation accuracy: **1.0000** (epoch 7)

## 4. Training/Validation Curves

| Epoch | TrLoss | TrAcc | VlLoss | VlAcc | Best |
|-------|--------|-------|--------|-------|------|
| 1 | 0.4077 | 0.77778 | 0.30113 | 0.83333 | ✅ |
| 2 | 0.17171 | 0.95556 | 1.30327 | 0.75 |  |
| 3 | 0.45038 | 0.88889 | 0.33758 | 0.91667 | ✅ |
| 4 | 0.19972 | 0.95556 | 0.245 | 0.91667 |  |
| 5 | 0.00039 | 1.0 | 0.84995 | 0.83333 |  |
| 6 | 6e-05 | 1.0 | 0.10003 | 0.91667 |  |
| 7 | 3e-05 | 1.0 | 0.00071 | 1.0 | ✅ |
| 8 | 3e-05 | 1.0 | 0.00013 | 1.0 |  |
| 9 | 4e-05 | 1.0 | 9e-05 | 1.0 |  |
| 10 | 2e-05 | 1.0 | 0.0005 | 1.0 |  |
| 11 | 1e-05 | 1.0 | 0.00318 | 1.0 |  |
| 12 | 3e-05 | 1.0 | 0.05331 | 1.0 |  |
| 13 | 1e-05 | 1.0 | 0.191 | 0.91667 |  |
| 14 | 1e-05 | 1.0 | 0.27938 | 0.91667 |  |
| 15 | 1e-05 | 1.0 | 0.32482 | 0.91667 |  |
| 16 | 1e-05 | 1.0 | 0.34871 | 0.91667 |  |
| 17 | 1e-05 | 1.0 | 0.36081 | 0.91667 |  |
| 18 | 1e-05 | 1.0 | 0.36864 | 0.91667 |  |
| 19 | 1e-05 | 1.0 | 0.37465 | 0.91667 |  |
| 20 | 1e-05 | 1.0 | 0.37889 | 0.91667 |  |
| 21 | 1e-05 | 1.0 | 0.38149 | 0.91667 |  |
| 22 | 1e-05 | 1.0 | 0.38391 | 0.91667 |  |
| 23 | 1e-05 | 1.0 | 0.38609 | 0.91667 |  |
| 24 | 1e-05 | 1.0 | 0.38845 | 0.91667 |  |
| 25 | 1e-05 | 1.0 | 0.39114 | 0.91667 |  |
| 26 | 0.0 | 1.0 | 0.39342 | 0.91667 |  |
| 27 | 0.0 | 1.0 | 0.39556 | 0.91667 |  |
| 28 | 0.0 | 1.0 | 0.39617 | 0.91667 |  |
| 29 | 0.0 | 1.0 | 0.39772 | 0.91667 |  |
| 30 | 0.0 | 1.0 | 0.39966 | 0.91667 |  |
| 31 | 0.0 | 1.0 | 0.40113 | 0.91667 |  |
| 32 | 0.0 | 1.0 | 0.40234 | 0.91667 |  |
| 33 | 0.0 | 1.0 | 0.40356 | 0.91667 |  |
| 34 | 0.0 | 1.0 | 0.40492 | 0.91667 |  |
| 35 | 0.0 | 1.0 | 0.40637 | 0.91667 |  |
| 36 | 0.0 | 1.0 | 0.40788 | 0.91667 |  |
| 37 | 0.0 | 1.0 | 0.40902 | 0.91667 |  |
| 38 | 0.0 | 1.0 | 0.40973 | 0.91667 |  |
| 39 | 0.0 | 1.0 | 0.41047 | 0.91667 |  |
| 40 | 0.0 | 1.0 | 0.41095 | 0.91667 |  |
| 41 | 0.0 | 1.0 | 0.41137 | 0.91667 |  |
| 42 | 0.0 | 1.0 | 0.41178 | 0.91667 |  |
| 43 | 0.0 | 1.0 | 0.41163 | 0.91667 |  |
| 44 | 0.0 | 1.0 | 0.41049 | 0.91667 |  |
| 45 | 0.0 | 1.0 | 0.41005 | 0.91667 |  |
| 46 | 0.0 | 1.0 | 0.40998 | 0.91667 |  |
| 47 | 0.0 | 1.0 | 0.41001 | 0.91667 |  |
| 48 | 0.0 | 1.0 | 0.41004 | 0.91667 |  |
| 49 | 0.0 | 1.0 | 0.41006 | 0.91667 |  |
| 50 | 0.0 | 1.0 | 0.41006 | 0.91667 |  |

## 5. Held-Out Test Evaluation
*Evaluated exactly once from best checkpoint (epoch 7)*

**Overall accuracy: 0.9429 (33/35)**

| Class | Support | Correct | Precision | Recall | F1 |
|-------|---------|---------|-----------|--------|----|
| HELLO | 14 | 14 | 1.000 | 1.000 | 1.000 |
| YES | 10 | 10 | 0.833 | 1.000 | 0.909 |
| NO | 11 | 9 | 1.000 | 0.818 | 0.900 |

### Confusion Matrix (rows=true, cols=predicted)
```
         HELLO  YES   NO
  HELLO     14     0     0
  YES        0    10     0
  NO         0     2     9
```

**Avg inference latency:** 30.69 ms/sample (CPU)

## 6. Inference Smoke Test
*(Run independently via tools/smoke_test_pilot.py)*
- [x] Checkpoint loads (`spoter_pilot_checkpoint.pt`) ✅
- [x] Class mapping loads (`pilot_class_mapping.json`) ✅
- [x] Accepts 366-D feature tensor ✅
- [x] Output shape: `[1, 3]` logits / probabilities ✅
- [x] Prediction accuracy on real test samples: **100%** (HELLO → HELLO, YES → YES, NO → NO) ✅
- [x] Deterministic repeat outputs: **100% Bit-Exact Match** ✅
- [x] Input safety guards (NaN & bad dimensions handled cleanly): **PASS** ✅

## 7. Animation Readiness
| Clip | In GLB | Linguistically Verified |
|------|--------|------------------------|
| ASL_HELLO | ✅ | Partial (synthetic salute) |
| ASL_YES | ✅ | ❌ INCOMPLETE — head-nod only, no manual component |
| ASL_NO | ✅ | ❌ INCOMPLETE — head-shake only, no manual component |

> **Note:** ASL YES is produced with an extended index finger pointing up and nodding.
> ASL NO is produced with index and middle fingers snapping closed twice.
> The current procedural animations use head movement only and are linguistically incomplete.

## 8. Preservation Checks
- `spoter_baseline_best_val_acc_checkpoint.pt`: **NOT modified** ✅
- `class_index_mapping.json` (79-class): **NOT modified** ✅
- `asl100_training_manifest.csv`: **NOT modified** ✅
- `asl100_vocabulary.json`: **NOT modified** ✅

## 9. Remaining Blockers Before Live Camera Integration
1. **Animation completeness:** ASL_YES and ASL_NO lack manual/hand components.
2. **Live inference wiring:** `playSignByLabel` must be connected to the inference result callback.
3. **Pilot model scale:** 3-class pilot has limited vocabulary — not suitable for production.

---
*Report auto-generated by `train_pilot_spoter.py` v2*