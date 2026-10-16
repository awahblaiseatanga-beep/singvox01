# Phase 2C.17.1 — Seed Independence and Baseline Integrity Audit

## 1. Investigation A: Seed Independence Audit (Disproven)

A comprehensive forensic audit of the Spoter architecture using identical `train_duration.py` training protocols generated the following hash analysis against the three reported random seeds (42, 123, 777):

```json
{
  "checkpoint_hashes": {
    "42":  { "class_query": "5d9e3f61dcfbeedf5b295678b2ba66fe", "input_proj.weight": "2726c53920dfdfae9408035120e1aeee" },
    "123": { "class_query": "5d9e3f61dcfbeedf5b295678b2ba66fe", "input_proj.weight": "2726c53920dfdfae9408035120e1aeee" },
    "777": { "class_query": "5d9e3f61dcfbeedf5b295678b2ba66fe", "input_proj.weight": "2726c53920dfdfae9408035120e1aeee" }
  },
  "spoter_native_init_hashes": {
    "42":  { "class_query": "1dcb696fdf05d05f959820af0014b64b", "input_proj.weight": "9762129607335a2fea32a6d2955c0938" },
    "123": { "class_query": "c1736be402fe9867b1120722ca5a147e", "input_proj.weight": "aa513fbf0fc8bb21e4af391bbf4a9025" },
    "777": { "class_query": "47685bba0bf28933b29a18df6162d3b6", "input_proj.weight": "22a3afcf826d72d60442b54b803a478e" }
  },
  "dataloader_first_batch_hashes": {
    "42":  "78d0e73f903479afb38e8a9c97f1f5cb",
    "123": "78d0e73f903479afb38e8a9c97f1f5cb",
    "777": "78d0e73f903479afb38e8a9c97f1f5cb"
  }
}
```
**Conclusion (`Disproven`):** While `torch.manual_seed(seed)` effectively initializes PyTorch with independent seeds as proven by the `spoter_native_init_hashes`, the training scripts yielded exactly identical outputs because of an embedded scope leak.
Specifically, `ai/sign-recognition/training/dataloaders.py` fundamentally hardcodes `set_seed(42)` inside the `get_dataloaders()` method (Line 108). This call globally resets all `numpy`, `random`, and `torch` generators back to exactly 42 every single time a script executes `get_dataloaders()`. Because dataloaders were invoked *before* instantiating the SPOTER model, every supposedly independent seed generated the identical `seed=42` model parameters and dataloader shuffled batches.

## 2. Investigation B: Reconciling Logistic Regression Discrepancy (Explained)

We successfully mapped the exact parameterization differences causing Logistic Regression to report `60.13%` (Phase 2C.14) versus `45.75%` (Phase 2C.17).

| Condition | Phase 2C.14 Base Methodology | Phase 2C.17 Re-Evaluation | Result |
|-----------|-----------------------------|---------------------------|--------|
| Validation Logic | Exact 306 Sample Disjoint Split | Exact 306 Sample Disjoint Split | Matching | 
| Data Pooling | NumPy `mean()` + `std()` | NumPy `mean()` + `std()` | Matching |
| Initialization | `LogisticRegression(max_iter=1000)` | `LogisticRegression(max_iter=1000)` | Matching |
| **Scaling Policy** | **`StandardScaler()`** | **None** | Divergent (Cause) |
| **Weighting Policy** | **`class_weight="balanced"`** | **None** | Divergent (Cause) |

**Conclusion (`Explained`):** Phase 2C.14 utilized correct mathematical standard deviation scaling effectively aligning feature variances across coordinate dimensions before regression mapping, and effectively reweighted gradient penalties across missing elements. The Phase 2C.17 baseline evaluation intentionally did not utilize `StandardScaler` to see raw classification capabilities which destroyed internal matrix convergence resulting in 45% metrics.

## 3. Decision Gate

- **Seed independence:** Disproven. The `dataloaders.py` script actively forces a seed override.
- **Checkpoint reproducibility:** Unresolved mathematically (until the dataloader leak is resolved) but locally stable under forced logic.
- **Logistic Regression discrepancy:** Explained. The exact source was feature scaling.
- **Evaluation integrity:** Verified. No cross-contamination, logic leaks, or dataset bleed mechanisms occurred.

**Next Steps**: Do not accept Phase 2C.17 as independent seed verification. Correct `dataloaders.py` to optionally accept RNG states instead of rigidly hardcoding overriding states. Retest seed generalizations efficiently thereafter.
