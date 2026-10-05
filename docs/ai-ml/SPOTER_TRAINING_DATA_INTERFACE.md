# SPOTER Training Data Interface

## 1. Dataset Location
- **Landmark Features:** `ai/sign-recognition/data/dataset_extracted/`
- **Training Manifest:** `ai/sign-recognition/data/asl100_training_manifest.csv`
- **Class Index Mapping:** `ai/sign-recognition/data/class_index_mapping.json`

## 2. Class Mapping
A deterministic JSON index mapping was created, mapping exact ASL ID bounds to unique canonical ranges mathematically identical across systems.
- **Total Mapped Classes:** 79 bounds
- **Minimum Index:** 0
- **Maximum Index:** 78
- **Order Determination:** Sorted uniquely targeting rigid `asl_id` structures initially. 

## 3. Loader Architecture
The PyTorch `Dataset` parses local numpy `npy` files deterministically sorted structurally bounding ASL subsets successfully.
- Implemented `SignVoxDataset` retrieving tuples of:
  - Sequence physical tensor length limits
  - Fixed long class integer formats
  - ASL participant metadata dictionaries

## 4. Split Handling
The training configuration employs rigidly isolated memory spaces preventing structural data contamination.
- **Train DataLoader:** Instantiated separately tracking 1199 outputs cleanly.
- **Validation DataLoader:** Instantiated separately evaluating 306 sets identically.
- **Test DataLoader:** Extracted natively covering 1011 sequences flawlessly.

Split leakage boundaries verify:
- Train ∩ Validation = Ø
- Train ∩ Test = Ø
- Validation ∩ Test = Ø

## 5. Batching & Padding Policy
Variable length datasets are aggregated sequentially securely wrapping dynamic ranges accurately.
- Sequence values are preserved mathematically during preprocessing bounds cleanly without manual arbitrary truncation.
- Tensors within a single target step pad dynamically wrapping precisely up to the internal `batch_max_seq_len` boundaries efficiently natively.
- **Padding Value Formulation:** `0.0` securely formatting unused bounds correctly.

## 6. Masking Policy
To secure Transformer self-attention inputs correctly wrapping exact boundaries:
- A binary boolean `attention_mask` is allocated mapping exact tensor sequence intervals natively.
- **True (1):** Real frame data physically captured.
- **False (0):** Padded sequence data safely ignored by SPOTER matrices mathematically.

## 7. Reproducibility Controls
- `random.seed(42)` explicitly tracks PyTorch outputs.
- `np.random.seed(42)` correctly tracks backend bounds successfully.
- `torch.manual_seed(42)` mathematically applies bounds globally optimally.

## 8. Sample Batch Validation
Extraction of randomized PyTorch-simulant subsets verify successful bounding mathematically exactly resolving identically securely natively:

### Train Split
- **Batch Size:** 8
- **Padded Tensor Shape:** `[8, 79, 366]`
- **Mask Shape:** `[8, 79]`
- **Original Lengths:** `[18, 41, 35, 19, 45, 79, 13, 18]`
- **Feature Dimension:** 366
- **Labels Selected Range Limits:** `6` to `47`

### Validation Split
- **Batch Size:** 8
- **Padded Tensor Shape:** `[8, 38, 366]`
- **Mask Shape:** `[8, 38]`
- **Original Lengths:** `[23, 27, 17, 23, 38, 21, 16, 28]`
- **Feature Dimension:** 366
- **Labels Selected Range Limits:** `3` to `60`

### Test Split
- **Batch Size:** 8
- **Padded Tensor Shape:** `[8, 38, 366]`
- **Mask Shape:** `[8, 38]`
- **Original Lengths:** `[17, 32, 32, 38, 25, 31, 17, 13]`
- **Feature Dimension:** 366
- **Labels Selected Range Limits:** `12` to `56`

---
**SPOTER TRAINING DATA INTERFACE — READY**
