# Phase 2C.29 — Rapid Continuous Translation Improvement Sprint Report

**Date:** October 11, 2026  
**Status:** Completed & Validated  
**Scope Boundary:** Isolated under `experiments/continuous-asl/phase_2c_29/`  
**Governing Principle:** Rule 5 (*Acknowledge and respect technical reality — Do not fake AI*)

---

## 1. Executive Summary

Phase 2C.29 executed a rapid, time-boxed improvement sprint to test whether combining an auxiliary **Connectionist Temporal Classification (CTC)** objective with the existing Bahdanau attention decoder could resolve the attention collapse and ungrounded language prior defects identified in Phase 2C.28.

### Key Empirical Findings:

1. **Repetition Completely Eradicated:**  
   The baseline Phase 2C.27 model suffered from an extreme **92.25% repetition rate** (infinite n-gram loops). Under Phase 2C.29's Joint CTC-Attention model with repetition-penalized inference, the repetition rate dropped to **0.00%**.
2. **Attention Map Sharpened:**  
   The baseline attention map was virtually uniform ($\bar{H}_{\text{norm}} = 0.9999$, 99.96% coverage). CTC frame-level gradients successfully sharpened the attention distribution: mean normalized entropy decreased to **0.9097**, and temporal coverage concentrated to **71.08%** with a measured center-of-mass progression of $-5.57$ frames.
3. **Temporal Invariance Persists (Ungrounded Prior):**  
   Despite attention sharpening and repetition elimination, the model remains predominantly ungrounded:
   - Temporally shuffling video frames yields **87.60% identical output sentences** to the original video sequences (down slightly from 90.31% in baseline).
   - In pairwise comparisons against mismatched random sentences, the matched video-reference pair only wins **51.94% of the time** (effectively a coin flip against 46.12% mismatched wins).
4. **Honest Target Assessment vs. 70% Target:**  
   - **Exact Sentence Match:** **0.00%** (Gap to 70%: 70.00%)
   - **Token Precision:** **28.12%** (Gap to 70%: 41.88%)
   - **Token F1:** **17.36%** (Gap to 70%: 52.64%)
   - **Token Levenshtein Accuracy:** **8.56%** (Gap to 70%: 61.44%)
   - **BLEU-1:** **6.54%** (Gap to 70%: 63.46%)
   - **BLEU-4:** **1.64%** (Gap to 70%: 68.36%)
   - The target of ~70% on continuous ASL-to-English translation is **not achievable** with the current unsegmented landmark dataset and edge architecture without ground-truth sign gloss alignments or large-scale pretrained pose representations.

---

## 2. Fast Data Provenance Verification (Step 1)

Within the time-box, dataset provenance was cross-referenced across the filesystem, manifests, and split assignments:

| Provenance Item | Value / Finding | Audit Verification |
| :--- | :--- | :--- |
| **Manifest Path** | `experiments/continuous-asl/phase_2c_26/dataset_manifest.csv` | 1,739 rows |
| **Feature Directory** | `experiments/continuous-asl/phase_2c_26/features/` | 1,048 `.npy` files present |
| **Readable Arrays** | **1,004 valid arrays** | 44 files were 0-byte interrupted writes |
| **Filtered Samples** | **40 samples** | Excluded for empty/non-alphanumeric transcripts |
| **Active Split Samples** | **964 total** | 706 Train, 258 Validation, 0 Test |
| **Grouped Split Isolation** | **100% Disjoint (0% Leakage)** | 77 Train `VIDEO_ID`s, 22 Val `VIDEO_ID`s (0 overlap) |
| **Feature Dimension** | **366 landmarks per frame** | 75 Pose + 42 LH + 42 RH coordinates |

---

## 3. Verified Phase 2C.27 Baseline (Step 2)

The actual trained Phase 2C.27 checkpoint (`best_attention_model.pt`, 2,084,931 parameters) was evaluated on the identical 258 validation samples across 4 conditions using the frozen model architecture:

| Condition | BLEU-1 (%) | BLEU-4 (%) | Repetition Rate (%) | Output Identity to Normal (%) | Mean Length (Ref=17.62) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Normal Input** | 13.49 | 1.66 | **92.25** | 100.0 (Reference) | 15.53 |
| **Zeroed Input** | 14.37 | 1.90 | 0.00 | 0.00 | 12.81 |
| **Shuffled Input** | 13.60 | 1.66 | 92.25 | **90.31** | 15.53 |
| **Mismatched Pair** | 14.75 | 1.82 | 92.25 | — | 15.53 |

*Baseline Failure Modes:* Extreme repetition loops ("you you can the to the..."), permutation invariance (90.31% identical outputs when frames are shuffled), and higher BLEU scores on mismatched or zeroed inputs due to common function word emissions.

---

## 4. Joint CTC-Attention Experiment (Step 3)

### 4.1 Architecture Design (`experiments/continuous-asl/phase_2c_29/model.py`)

A compact Joint CTC-Attention model was built respecting edge CPU inference constraints:
- **Input Contract:** `[B, T, 366]` MediaPipe coordinates.
- **Landmark Encoder:**
  - Linear input projection: `Linear(366, 256)` + LayerNorm + Dropout(0.2).
  - Recurrent Backbone: 2-layer Bidirectional GRU (`hidden_dim=256`).
  - Bridge & Normalization: `Linear(512, 256)` + LayerNorm.
- **CTC Prediction Head:**
  - `Linear(256, vocab_size + 1)`, where `blank_id = vocab_size` (dedicated extra class).
  - Loss: `nn.CTCLoss(blank=blank_id, zero_infinity=True)`.
  - Target: BPE subword token sequence stripped of `<sos>` and `<eos>`. Stride 1 guarantees $T_{\text{enc}} \ge L_{\text{tgt}}$ for 100% of samples.
- **Attention Decoder:**
  - Embedding: `Embedding(vocab_size, 128, padding_idx=0)`.
  - Bahdanau Attention: `attn_dim=128`.
  - Recurrent Cell: `GRUCell(128 + 256, 256)`.
  - Loss: `nn.CrossEntropyLoss(ignore_index=0)`.
- **Combined Training Objective:**
  $$\mathcal{L} = 0.7 \cdot \mathcal{L}_{\text{CE}} + 0.3 \cdot \mathcal{L}_{\text{CTC}}$$
- **Total Parameters:** **3,849,297 (3.85M parameters)**.

### 4.2 Training Progression (`experiments/continuous-asl/phase_2c_29/train.py`)

- **Pilot Sanity Check:** Passed on step 1 (CE Loss: 6.9829, CTC Loss: 25.6381, Max Gradient: 10.5176).
- **Training Epochs:** 6 epochs on CPU before early stopping (patience=4):
  - **Epoch 1:** Train Loss = 6.3127 | Val Loss = 6.0858 (CE: 5.9777, CTC: 6.3378) — Saved Best Checkpoint
  - **Epoch 2:** Train Loss = 5.9617 | Val Loss = **6.0615** (CE: 5.9587, CTC: 6.3012) — **Saved Best Checkpoint**
  - **Epoch 3:** Train Loss = 5.8588 | Val Loss = 6.0687 (CE: 5.9825, CTC: 6.2697)
  - **Epoch 4:** Train Loss = 5.7786 | Val Loss = 6.0755 (CE: 5.9981, CTC: 6.2560)
  - **Epoch 5:** Train Loss = 5.7092 | Val Loss = 6.0954 (CE: 6.0026, CTC: 6.3118)
  - **Epoch 6:** Train Loss = 5.6147 | Val Loss = 6.0750 (CE: 6.0031, CTC: 6.2429) — Early Stopping Triggered
- **Best Checkpoint:** `experiments/continuous-asl/phase_2c_29/best_ctc_attention_model.pt` (Val Loss: 6.0615).

---

## 5. Input-Dependence & Semantic Grounding Diagnostics (Step 4)

The best model was evaluated across 4 controlled conditions on the full 258-clip validation split:

| Evaluation Metric | Phase 2C.27 Baseline | Phase 2C.29 Joint CTC-Attention | Improvement / Delta |
| :--- | :--- | :--- | :--- |
| **Normal Input BLEU-1** | 13.49% | 6.54% | $-6.95\%$ (Brevity Penalty = 0.2287) |
| **Normal Input BLEU-4** | 1.66% | 1.64% | $-0.02\%$ |
| **Repetition Rate** | **92.25%** | **0.00%** | **$-92.25\%$ (Completely Eliminated)** |
| **Mean Hypothesis Length** | 15.53 tokens | 7.12 tokens | Shorter, non-repetitive sentences |
| **Shuffled Input Identity** | **90.31%** | **87.60%** | $-2.71\%$ |
| **Pairwise Matched Win Rate** | 43.41% | **51.94%** | $+8.53\%$ |
| **Pairwise Mismatched Win Rate**| 20.16% | 46.12% | Near 50/50 coin flip |
| **Mean Attention Entropy** | **0.9999** (Uniform) | **0.9097** | **Sharpened towards specific frames** |
| **Mean Attention Coverage** | **99.96%** | **71.08%** | **$-28.88\%$ reduction in diffuse spread** |
| **Center of Mass Progression** | 0.0 frames (Frozen) | **$-5.57$ frames** | Active temporal drift |
| **Mean Inference Latency** | 85.3 ms | **35.45 ms** | **$2.4\times$ faster CPU inference** |

---

## 6. Honest Metric Evaluation & Target Analysis (Step 5)

The user prompt established a practical target of **~70% on a clearly defined, valid evaluation metric**. In adherence to Rule 5, here is the honest evaluation of all candidate metrics:

| Metric Name | Mathematical Definition | Phase 2C.29 Result | Target | Gap to 70% Target | Status / Assessment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Exact Sentence Match** | $\frac{\text{Exact Matches}}{N}$ | **0.00%** | 70.00% | $-70.00\%$ | Not achieved. Zero validation sentences matched reference 100%. |
| **Token Precision** | $\frac{\sum \text{overlap}}{\sum \text{len}(\text{hyp})}$ | **28.12%** | 70.00% | **$-41.88\%$** | Best unigram metric. 28.1% of generated tokens appear in reference. |
| **Token F1 Score** | $\frac{2 \cdot P \cdot R}{P + R}$ | **17.36%** | 70.00% | $-52.64\%$ | Low recall (12.56%) due to concise hypotheses. |
| **Token Levenshtein Accuracy**| $1 - \frac{\text{Lev}(hyp, ref)}{\max(L_{\text{ref}}, L_{\text{hyp}})}$ | **8.56%** | 70.00% | $-61.44\%$ | Word-order sensitive subword sequence alignment. |
| **Corpus BLEU-1** | Modified unigram precision $\times \text{BP}$ | **6.54%** | 70.00% | $-63.46\%$ | Penalized by brevity penalty ($\text{BP} = 0.2287$). |
| **Corpus BLEU-4** | 4-gram geometric mean $\times \text{BP}$ | **1.64%** | 70.00% | $-68.36\%$ | Fluent phrase matching remains limited. |
| **Repetition Suppression** | $1 - \text{Repetition Rate}$ | **100.00%** | 70.00% | **$+30.00\%$ (Exceeded)** | Perfect score on cycle suppression, but not translation accuracy. |

### Summary on the 70% Target:
The highest achieved translation accuracy metric is **Token Precision at 28.12%** (leaving a **41.88% gap** to 70%). Continuous translation cannot be claimed as solved or approaching 70% on this benchmark.

---

## 7. Frontend Handoff Specification (Step 6)

For the frontend team beginning work tomorrow, this section establishes the verified model contract, loading interface, runtime expectations, and operational guardrails.

### 7.1 Verified Checkpoint Details
- **Checkpoint File:** `experiments/continuous-asl/phase_2c_29/best_ctc_attention_model.pt`
- **Tokenizer File:** `experiments/continuous-asl/phase_2c_27/tokenizer.json`
- **Model Definition:** `experiments/continuous-asl/phase_2c_29/model.py` (`JointCTCAttentionModel`)
- **Total Parameters:** 3,849,297 FP32 parameters (~15.4 MB memory footprint)

### 7.2 Model Loading & Inference Interface

```python
import torch
from tokenizer import BPETokenizer
from model import JointCTCAttentionModel

def load_continuous_translator(model_path, tokenizer_path, device="cpu"):
    tokenizer = BPETokenizer.load(tokenizer_path)
    model = JointCTCAttentionModel(
        vocab_size=len(tokenizer.token2id),
        in_features=366,
        hidden_dim=256,
        embed_dim=128,
        attn_dim=128,
        pad_id=tokenizer.pad_id,
        sos_id=tokenizer.sos_id,
        eos_id=tokenizer.eos_id,
        dropout=0.0
    )
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model, tokenizer

def translate_landmark_clip(model, tokenizer, landmarks_tensor):
    """
    landmarks_tensor: torch.Tensor of shape [1, T, 366], float32.
    Returns: decoded English string.
    """
    mask = torch.ones((1, landmarks_tensor.size(1)), dtype=torch.bool)
    with torch.no_grad():
        token_ids = model.generate(
            landmarks_tensor,
            mask,
            max_len=50,
            repetition_penalty=1.2
        )
    return tokenizer.decode(token_ids, skip_special_tokens=True)
```

### 7.3 Input & Output Specifications
- **Input Shape:** `[1, T, 366]`, `torch.float32`.
  - Frame length $T \in [5, 150]$ frames (~0.2 to 5.0 seconds at 30 FPS).
  - 366 features: 75 Pose landmarks (25 points $\times$ [x, y, visibility]), 42 Left Hand landmarks (21 points $\times$ [x, y]), 42 Right Hand landmarks (21 points $\times$ [x, y]), normalized relative to shoulder/nose anchors.
- **Output Format:** Clean UTF-8 English string (e.g., `"so you want to the a little"`).
- **Execution Mode:** **Batch Clip-Level Only**.
  - Inference requires the **completed sign gesture clip**. The bidirectional GRU encoder requires future frames to compute contextual representations; it does **not** support incremental frame-by-frame streaming.
- **Measured Latency:**
  - Mean CPU latency: **35.45 ms** per clip.
  - Median CPU latency: **37.56 ms** per clip.
  - 95th Percentile latency: **55.52 ms** per clip.
  - Well within interactive threshold for completed clip evaluation.

### 7.4 Critical Frontend UI & UX Guardrails

1. **Do Not Direct-Connect to Speech Synthesis:**  
   Because the model has an 87.6% frame-shuffling invariance and generates high-frequency instructional fragments ("so you want to the a little"), directly speaking its raw output will lead to poor user experience.
2. **Display as "Experimental Continuous Translation (Beta)":**  
   The UI should visually distinguish the continuous translation output from the high-confidence isolated sign classifier (the 3-sign Pilot / 79-class Baseline).
3. **Trigger Inference on Gesture Completion:**  
   The frontend should use an activity detector (e.g. hand velocity threshold or silence boundary) to segment completed signing gestures before passing the accumulated $[T, 366]$ array to the translation engine.
