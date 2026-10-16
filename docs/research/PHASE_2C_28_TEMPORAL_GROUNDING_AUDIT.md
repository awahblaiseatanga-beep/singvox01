# Phase 2C.28 — Temporal Grounding and Input-Dependence Audit Report

**Date:** October 11, 2026  
**Status:** Completed & Validated  
**Scope Boundary:** Isolated under `experiments/continuous-asl/phase_2c_28/`  
**Governing Principle:** Rule 5 (*Acknowledge and respect technical reality — Do not fake AI*)

---

## 1. Executive Summary

Phase 2C.28 was commissioned to perform a forensic, mathematically controlled audit of the continuous ASL-to-English translation model developed in Phase 2C.27. Specifically, it investigated why the Phase 2C.27 model produced nearly identical English hypotheses when video landmark features were original, temporally shuffled, or cross-matched against random sign videos.

### Key Audit Findings

1. **The Model Functions as an Ungrounded Language Prior:**  
   The Phase 2C.27 model does not learn fine-grained temporal-visual alignment. Instead, it operates almost entirely as an autoregressive English language prior triggered by the mere presence of landmark coordinates.
   - **Temporal Frame Shuffling:** Yields **91.86% byte-for-byte identical output sentences** to the original video sequences. Frame order has negligible effect on the generated translation.
   - **Static Input (Zero Motion):** Replicating the very first frame across all timesteps produces **60.47% byte-for-byte identical hypotheses** to full dynamic video.
   - **Cross-Video Swapped Features:** Feeding landmark features from completely unrelated videos (different topic, speaker, and vocabulary) produces **48.45% byte-for-byte identical hypotheses**.
   - **Random Derangements:** In controlled pairwise comparisons across 5 seeded derangements, pairing a video with an arbitrary random sentence beats the true reference sentence **20.2% of the time** (and ties **36.4% of the time**).

2. **Attention Masks are Airtight, but Attention is Completely Diffuse:**  
   The attention mask implementation was audited across 107,302 padded elements. Padding leakage is **0.00** (zero leakage). However, over valid frames, the attention distribution is mathematically uniform:
   - Mean normalized attention entropy: **0.9999** ($\text{std} = 0.0000$).
   - Mean temporal coverage: **99.96%** of sequence frames.
   - Attention center of mass is permanently frozen at the sequence midpoint ($T/2$), displaying zero monotonic progression across decoding steps.

3. **Data Reconciliation Resolved:**  
   Discrepancies in historical logs between 1,739, 1,399, 1,048, 1,004, and 964 were traced directly to extraction progress snapshots. 1,048 feature arrays exist on disk; 1,004 are valid non-empty arrays; 964 fall into active train/val splits (706 train, 258 validation).

---

## 2. Dataset Reconciliation Audit

An audit was conducted across the How2Sign expanded manifest, feature arrays on disk, dataset loader code, and split assignments.

### 2.1 Audit Reconciliation Table

| Metric / Stage | Count | Source / Audit Verification |
| :--- | :--- | :--- |
| **Manifest Rows (Raw CSV)** | **1,739** | `experiments/continuous-asl/phase_2c_26/dataset_manifest.csv` |
| **Unique Sentence IDs** | **1,739** | Verified column `SENTENCE_NAME` uniqueness |
| **Unique Source Video IDs** | **110** | Verified column `VIDEO_ID` |
| **Feature Files Present on Disk** | **1,048** | Filesystem audit of `phase_2c_26/features/*.npy` |
| **Successfully Loadable Files** | **1,004** | Validated via `np.load()` (44 files were 0-byte corrupt stubs) |
| **Total Filtered Samples** | **40** | Empty token strings / non-alphanumeric transcripts |
| **Active Usable Samples Across Splits** | **964** | Clean, non-empty samples across grouped train and val splits |
| **Training Split Samples** | **706** | Split: `train` (77 source `VIDEO_ID` groups) |
| **Validation Split Samples** | **258** | Split: `val` (22 source `VIDEO_ID` groups) |
| **Test Split Samples** | **0** | Reserved for final blind testing (11 `VIDEO_ID` groups, 0 features on disk) |

### 2.2 Forensic Explanation of Historical Log Discrepancies

- **1,739 vs. 1,399:** The total number of sentences in the How2Sign validation subset manifest is 1,739. The number 1,399 cited in early Phase 2C.26 notes represented an intermediate checkpoint taken during batch landmark extraction before the remaining clips completed.
- **1,399 vs. 1,048:** Extraction was terminated when disk allocation limits were reached, leaving 1,048 `.npy` files written to disk.
- **1,048 vs. 1,004:** 44 `.npy` files were interrupted during writing and remained as 0-byte files. The loader skips non-readable files, yielding 1,004 loadable files.
- **1,004 vs. 964:** 40 samples had empty transcripts after punctuation stripping or duration below threshold ($T < 5$ frames). 706 were grouped into train, and 258 were grouped into validation.
- **Split Leakage Check:** Split verification confirmed that no source `VIDEO_ID` appears in both train and validation splits (**0% split leakage**, strict speaker/clip grouping preserved).

---

## 3. Forensic Model Architecture & Latency Audit

### 3.1 Checkpoint Architecture Mismatch

A structural discrepancy was discovered between the class definition defaults in `phase_2c_27/model.py` and the saved weights in `phase_2c_27/best_attention_model.pt`:

```
Definition in model.py (default args):
  hidden_dim = 128, num_layers = 1 -> Total Parameters: 585,027 (0.58M)

Saved Checkpoint (best_attention_model.pt):
  hidden_dim = 256, num_layers = 2 -> Total Parameters: 2,084,931 (2.08M)
```

Attempting to evaluate `best_attention_model.pt` with default arguments caused a PyTorch `size mismatch for encoder.rnn.weight_ih_l0` error. To preserve Phase 2C.27 code while auditing the actual trained model, an isolated class `FrozenPhase27Model` was instantiated in `phase_2c_28/semantic_dependence.py` with `hidden_dim=256` and `num_layers=2`.

### 3.2 Evaluation Latency Optimization

Evaluation initially suffered from an extreme CPU latency bottleneck:
- **Baseline Latency:** ~17.5 seconds per clip on Windows host CPU. For 258 clips, this would require 75 minutes per condition (nearly 9 hours for the diagnostic suite).
- **Root Cause:** OpenMP/MKL thread contention within the autoregressive decoding loop on Windows multi-core architecture.
- **Resolution:** Enforcing `torch.set_num_threads(1)` and vectorizing the attention mask projection reduced latency to **85.3 ms per clip** (a **205x speedup**), allowing the complete 7-condition diagnostic suite across 258 validation samples to run in under 4 minutes.

---

## 4. Controlled Semantic-Dependence Diagnostics

The validation split (258 clips) was evaluated across 7 controlled conditions to isolate the sources of model output variation.

### 4.1 Seven Diagnostic Conditions Summary

| Condition | Description | BLEU-1 (%) | BLEU-2 (%) | BLEU-4 (%) | Repetition Rate (%) | Hypothesis Identity to Cond 1 (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Original** | Real, unperturbed landmark sequences | 13.90 | 2.21 | 0.00 | 58.91 | **100.00** (Reference) |
| **2. Zeroed** | All landmark coordinates set to 0.0 | 14.20 | 3.71 | 0.52 | 0.00 | 0.00 |
| **3. Shuffled** | Temporal frame order randomly permuted | 13.96 | 2.19 | 0.00 | 58.91 | **91.86** |
| **4. Rolled** | Frames rolled by $T/2$ timesteps | 13.96 | 2.19 | 0.00 | 58.91 | **91.86** |
| **5. Deranged (Mean)** | Mismatched video-target pairings (5 seeds) | 12.63 | 1.86 | 0.00 | 58.91 | 20.62 |
| **6. Static Input** | First frame replicated across all timesteps | 14.19 | 2.37 | 0.00 | 59.30 | **60.47** |
| **7. Cross Swap** | Length-matched swap from different video | 13.99 | 2.28 | 0.00 | 58.91 | **48.45** |

### 4.2 Detailed Analysis of Diagnostic Conditions

#### Condition 3 & 4: Frame Shuffling and Temporal Rolling (91.86% Identity)
When video frames are shuffled into random order, **237 out of 258 generated sentences (91.86%) are 100% byte-for-byte identical** to the output from the original, un-shuffled video. The BLEU score remains virtually unchanged (13.90% vs 13.96%). This demonstrates that the model is temporally invariant.

#### Condition 6: Static Zero-Motion Input (60.47% Identity)
When all motion is removed by replicating the initial frame across time, **156 out of 258 sentences (60.47%) remain completely identical** to the dynamic video output. The model does not require gesture dynamics to produce its hypotheses.

#### Condition 7: Cross-Video Swapped Features (48.45% Identity)
When the video feature sequence is replaced with landmarks from a completely different video (different speaker, different topic), **125 out of 258 sentences (48.45%) are identical**. The model's predictions are broadly invariant to the sign being performed.

#### Condition 2: Zeroed Input Anomaly
Zeroing the input vectors shifts the decoder away from its repetitive loop, producing short, common English words ("and", "to", "you"). Because reference sentences in How2Sign contain many common function words, zeroed inputs achieve a **higher BLEU-1 (14.20%) and higher BLEU-4 (0.52%)** than genuine sign video features.

### 4.3 Pairwise Win / Tie / Loss Diagnostics (5 Seeded Derangements)

To determine whether the model exhibits clip-specific preference, matched video-reference pairs were compared against 5 deterministic derangements (seeded circular permutations, guaranteed zero self-matching):

| Seed | Matched Win Rate (%) | Tie Rate (%) | Mismatched Win Rate (%) | Mean $\Delta$ BLEU-1 | 95% CI |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Seed 42** | 43.80 | 36.43 | 19.77 | +1.27 | [0.74, 1.80] |
| **Seed 101** | 43.41 | 36.05 | 20.54 | +1.28 | [0.74, 1.81] |
| **Seed 202** | 43.02 | 36.43 | 20.54 | +1.26 | [0.73, 1.80] |
| **Seed 303** | 43.41 | 36.82 | 19.77 | +1.27 | [0.74, 1.81] |
| **Seed 404** | 43.41 | 36.43 | 20.16 | +1.26 | [0.73, 1.79] |
| **Aggregate Mean** | **43.41** | **36.43** | **20.16** | **+1.27** | **[0.74, 1.80]** |

#### Findings:
1. In **36.4% of cases**, the model generates an identical score regardless of which sentence it is paired with.
2. In **20.2% of cases**, an arbitrary mismatched reference achieves a *higher* BLEU score than the genuine ground truth sentence.
3. The matched pair only outperforms a random pairing 43.4% of the time, with a marginal mean advantage of only **+1.27 BLEU-1 points**.

---

## 5. Attention Mechanism & Masking Audit

To understand the mathematical mechanism underlying temporal invariance, the attention distribution of `FrozenPhase27Model` was audited across the validation set.

### 5.1 Padding Mask Verification

The decoder's Bahdanau attention mechanism was checked for attention leakage into padded frames ($t \ge T_{\text{valid}}$):
- **Total Padded Elements Evaluated:** 107,302
- **Maximum Attention Weight on Padding:** **0.00e+00**
- **Padding Elements with Weight $> 10^{-6}$:** **0**
- **Status:** **PASSED — Zero Padding Leakage.** The inverted boolean mask with $-10^9$ fill is mathematically intact.

### 5.2 Attention Entropy and Temporal Concentration

Over valid sequence frames ($t < T_{\text{valid}}$), attention weights were analyzed for entropy and dispersion:

$$\bar{H}_{\text{norm}} = \frac{1}{S} \sum_{s=1}^S \frac{H_s}{\log(T_{\text{valid}})}, \quad \text{where } H_s = -\sum_{t=0}^{T_{\text{valid}}-1} \alpha_{s, t} \log(\alpha_{s, t})$$

- **Mean Normalized Attention Entropy:** **0.9999** ($\text{std} = 0.0000$)
- **Mean Temporal Coverage:** **99.96%** of sequence frames ($\text{std} = 0.01\%$)
- **Interpretation:** **DIFFUSE UNIFORM ATTENTION.**

The attention weights across any sequence of length $T$ are uniformly distributed:

$$\alpha_{s, t} \approx \frac{1}{T_{\text{valid}}} \quad \forall t \in [0, T_{\text{valid}}-1]$$

For example, on clip `f5EGPzGSCJs_0-8-rgb_front` ($T=78$ frames), the empirical attention profile across 5 temporal quintiles is:
`[0.0134, 0.0129, 0.0128, 0.0127, 0.0124]` (where uniform expectation is $1/78 = 0.0128$).

### 5.3 Monotonic Alignment Trajectory

The attention center of mass $\bar{t}_s = \sum_{t=0}^{T-1} t \cdot \alpha_{s, t}$ was tracked across decoding steps $s=1 \dots S$:
- For a 78-frame clip (midpoint = 38.5), the center of mass trajectory across 11 decoding steps is:
  `[37.98, 37.96, 37.87, 37.91, 37.92, 37.95, 37.97, 37.91, 37.98, 37.92, 37.91]`
- For a 134-frame clip (midpoint = 66.5), the trajectory across 20 decoding steps is:
  `[65.68, 65.68, 65.56, 65.61, 65.63, 65.70, ..., 65.83]`

The attention center of mass is **frozen at the exact temporal midpoint** of the video. It exhibits zero progression from start to finish.

### 5.4 Mathematical Explanation of Observed Failure Modes

Because $\alpha_{s, t} \approx \frac{1}{T}$ for all $s, t$, the context vector $c_s$ supplied to the decoder at every step is simply the sequence-level global mean of encoder hidden states:

$$c_s = \sum_{t=1}^T \alpha_{s, t} h_t \approx \frac{1}{T} \sum_{t=1}^T h_t = \bar{h}$$

1. **Why Shuffled and Dynamic Inputs are Identical:**  
   The mean of a sequence is permutation-invariant: $\frac{1}{T} \sum h_{\pi(t)} = \frac{1}{T} \sum h_t$. Permuting frames leaves the context vector $c_s$ largely unchanged.
2. **Why the Model Degenerates into Repetition:**  
   Since $c_s \approx \bar{h}$ is static across all decoding steps, the autoregressive decoder receives no temporal progress signal indicating which sign has been completed and which sign comes next. As a result, the decoder defaults to its dominant language model prior, falling into repetitive n-gram loops ("and you you to to a to a a little").

---

## 6. Training Hypotheses Feasibility Assessment

Before designing future phases, four candidate training paradigms were evaluated against the empirical constraints of the How2Sign expanded dataset.

### 6.1 Connectionist Temporal Classification (CTC) Auxiliary Loss

- **Sequence Length Feasibility:**  
  CTC requires $T_{\text{enc}} \ge L_{\text{target}}$. Across all 1,739 samples in the dataset:
  - Median frame length $T = 124.0$ (mean $107.5$).
  - Median target token length $L = 21.0$ (mean $24.8$).
  - Median ratio $T/L = 4.69$ (mean $5.36$, min $1.16$).
  - **At Stride 1 (no temporal pooling):** **0 violations (0.00%)**. $T \ge L$ holds universally.
  - **At Stride 2 ($T/2$ pooling):** **32 violations (1.84%)**. Easily accommodated with length filtering.
  - **At Stride 4 ($T/4$ pooling):** **557 violations (32.03%)**. Infeasible without subword truncation.
- **Monotonic Alignment Dynamics:**  
  ASL grammar differs from English word order (Topic-Comment structure). CTC assumes monotonic alignment, so standalone CTC cannot solve full ASL-to-English translation. However, **Joint CTC-Attention** (where CTC is applied as an auxiliary objective on encoder representations with loss weight $\lambda_{\text{ctc}} \in [0.1, 0.3]$) enforces monotonic temporal emissions, directly preventing the encoder from collapsing into the uniform diffuse state ($\bar{H} = 0.9999$) identified in this audit.
- **Verdict:** **HIGH FEASIBILITY & SCIENTIFICALLY JUSTIFIED.** Minimal compute overhead, directly targets the entropy collapse.

### 6.2 Visual-Text Contrastive Learning (InfoNCE / CLIP-style)

- **Hardware & Batch Constraints:**  
  Effective contrastive learning requires large batches ($N \ge 128$) or large negative queues (MoCo). On our CPU development setup, batch size is constrained to 16. With $N=16$, only 15 negative samples are available per batch.
- **Semantic Overlap in Instructional Corpora:**  
  How2Sign transcripts share repetitive formulaic phrases across clips ("Now we're going to...", "Make sure that you..."). In small batches, random negatives frequently share high semantic overlap, creating severe false negative penalties.
- **Verdict:** **LOW FEASIBILITY UNDER CURRENT HARDWARE.** Would require synthetic hard negative mining or external pretraining.

### 6.3 Gloss-Supervised or Alignment-Guided Pre-Training

- **Annotation Availability:**  
  Audit of the How2Sign manifest and source files confirms that **zero gloss annotations exist**. Only full English sentence transcripts are provided.
- **External Corpora:**  
  Datasets containing glosses (e.g., PHOENIX-Weather 2014T, CSL-Daily) are in German Sign Language (DGS) or Chinese Sign Language (CSL), not American Sign Language (ASL).
- **Verdict:** **FACTUALLY INFEASIBLE.** Lack of ASL gloss annotations makes gloss-supervised pretraining impossible without manual annotation.

### 6.4 Pretrained Visual Encoders (Video Backbones vs. Isolated Pose Checkpoints)

- **RGB Video Backbones (S3D / I3D / VideoMAE):**  
  Processing 1,739 raw RGB MP4s would require ~40–80 GB storage and GPU infrastructure that is unavailable under current local edge constraints. Furthermore, heavy 3D CNNs violate SignVox's mandate for client-side MediaPipe execution.
- **Pose-Based Isolated Sign Pretrained Encoders:**  
  Using a lightweight landmark encoder pretrained on isolated ASL signs (e.g., WLASL or MS-ASL 100–1000 sign classification) maintains client-side MediaPipe compatibility while supplying the continuous translation model with semantically grounded frame representations.
- **Verdict:** **RGB BACKBONES INFEASIBLE; ISOLATED POSE ENCODERS FEASIBLE.**

---

## 7. Audit Recommendations & Proposed Next Steps

| Recommendation | Rationale | Priority |
| :--- | :--- | :--- |
| **1. Discontinue Vanilla Attention Seq2Seq Training** | Unconstrained Bahdanau attention collapses into diffuse uniform context on unsegmented continuous ASL landmark streams. | Immediate |
| **2. Implement Joint CTC-Attention Architecture** | CTC auxiliary loss ($T/L \approx 4.7$) forces encoder representations to remain temporally grounded and prevents uniform attention collapse. | High |
| **3. Test Temporal Stride 2 Convolutional Front-End** | Downsampling landmarks by $2\times$ reduces sequence length to ~62 frames while maintaining $T \ge L$ for 98.16% of samples. | High |
| **4. Implement Length-Normalized Repetition Penalties** | Suppressing 3-gram and 4-gram repetition during autoregressive beam search will prevent loops without altering model weights. | Medium |
| **5. Pretrain Landmark Encoder on Isolated ASL (WLASL)** | Initializing landmark encoder weights on isolated sign classification provides gesture semantics before continuous translation. | Long-term |

---

## 8. Artifact Verification Log

All diagnostic scripts, raw JSON metrics, and frozen models are permanently archived and auditable under:
- `experiments/continuous-asl/phase_2c_28/semantic_dependence.py`: 7-condition diagnostic and 5-derangement evaluation suite.
- `experiments/continuous-asl/phase_2c_28/semantic_dependence_results.json`: Full numerical results and per-condition metrics.
- `experiments/continuous-asl/phase_2c_28/attention_audit.py`: Attention mask verification, normalized entropy, and trajectory audit.
- `experiments/continuous-asl/phase_2c_28/attention_audit_results.json`: Numerical entropy and padding leakage audit results.
- `experiments/continuous-asl/phase_2c_28/hypothesis_feasibility.py`: Sequence length and CTC downsampling feasibility script.
- `experiments/continuous-asl/phase_2c_28/hypothesis_feasibility.json`: Sequence distribution and CTC violation rates.
