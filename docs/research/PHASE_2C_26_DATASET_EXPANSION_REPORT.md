# Phase 2C.26 — How2Sign Continuous Dataset Expansion and Quality Validation Report

**Date:** October 11, 2026  
**Status:** Completed & Validated  
**Workspace:** Isolated under `experiments/continuous-asl/phase_2c_26/` and `data/continuous_how2sign_val/`  
**Scope:** Dataset Acquisition, Landmark Extraction Pipeline, Group-Split Manifest Construction, and OOV Quality Audit (No model training or tuning performed)

---

## Executive Summary

Phase 2C.25 identified that our initial continuous ASL translation baseline suffered from severe mode collapse, zero validation exact match accuracy, a crippling 31.8% validation word-level OOV rate, and extreme training data sparsity (only 61 training sentences).

In **Phase 2C.26**, we resolved this data starvation by successfully scaling the dataset to the full available How2Sign validation subset:
1. **Video Acquisition:** Acquired all 18 shards from Hugging Face (`aipieces/How2Sign/val_rgb_front_clips`), extracting **1,739 continuous signing video clips** (2.74 total hours of video, 100% cv2 decode success, 0 corrupt files).
2. **Deterministic Group-Split:** Replaced unconstrained random splitting with a **strict session/signer-isolated group split by `VIDEO_ID`** across 115 unique source videos. Train, validation, and test sets have **0% session overlap**.
3. **Scale & Vocabulary Expansion:**
   - Training clips increased **20-fold**: from **61 to 1,215 clips**.
   - Training vocabulary expanded **10.4-fold**: from **249 to 2,582 unique words**.
   - Validation word-level Out-of-Vocabulary (OOV) rate dropped by **59% relatively**: from **31.8% down to 13.04%**.
   - Test word-level OOV rate dropped from **28.5% down to 10.90%**.
4. **Extraction Architecture:** Built an isolated, resumable, parallel landmark extraction pipeline adhering to the `[T, 366]` float32 contract using MediaPipe Tasks (Pose 33, Left Hand 21, Right Hand 21, Face 25). Audited sequences show **0 NaN / Infinity occurrences** and **0 shape mismatches**.

---

## 1. Acquisition Audit & Integrity Verification

### 1.1 Source and Transfer Verification
- **Source Repository:** Hugging Face `aipieces/How2Sign` (`val_rgb_front_clips/`)
- **Total Shards Processed:** 18 of 18 shards (`shard_001_018.zip` through `shard_018_018.zip`, totaling ~1.66 GB).
- **Disk Utilization:** Acquired on Drive D (which maintains >133 GB free headroom). Shard archives were unzipped and cleaned dynamically to prevent disk bloat.
- **Sandbox Sample Reuse:** Reused all 100 verified clips from `data/sandbox_continuous/how2sign_sample/` to eliminate duplicate network transfers.

### 1.2 Decoding and Annotation Verification
Every downloaded MP4 was tested via OpenCV (`cv2.VideoCapture`) and joined against `how2sign_val.csv`:

| Parameter | Count / Status | Notes |
| :--- | :--- | :--- |
| **Total Annotations in Official CSV** | 1,741 | Sentence-level How2Sign validation subset |
| **Total Downloaded Video Files** | 1,739 | 99.88% coverage of validation split |
| **Successful OpenCV Decodes** | 1,739 (100.0%) | Zero unreadable or truncated video files |
| **Decode Failures** | 0 (0.0%) | All files verified readable frame-by-frame |
| **Missing CSV Annotations** | 0 | Every video maps to a verified transcript |
| **Unmatched CSV Records** | 2 | Only 2 clips were not present in the 18 shards |
| **Total Video Duration** | 2.74 Hours | 9,864 seconds of continuous sign video |

---

## 2. Leakage-Resistant Group-Split Manifest

### 2.1 Why Group-Level Splitting Matters
In continuous sign language corpora, multiple sentence clips originate from a single continuous recording session with the same signer, identical camera background, clothing, and lighting. Random clip-level splitting leaks signer appearance and contextual biases across train and validation sets, producing deceptive evaluation metrics.

In Phase 2C.26, clips were grouped strictly by the source video identifier (`VIDEO_ID`):
- All sentences originating from a specific `VIDEO_ID` are assigned exclusively to either Train, Validation, or Test.
- **Session Leakage:** Exactly **0.0%**.

### 2.2 Split Summary (by `VIDEO_ID`)

| Split | Source Videos (`VIDEO_ID`) | Clips / Sentences | Percentage | Total Duration (s) | Mean Sentence Len (words) | Median Sentence Len (words) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train** | 83 | 1,215 | 69.9% | 6,864.2 s | 17.52 | 15.0 |
| **Validation** | 16 | 258 | 14.8% | 1,482.9 s | 17.65 | 15.0 |
| **Test** | 16 | 266 | 15.3% | 1,516.9 s | 17.78 | 15.0 |
| **Total** | **115** | **1,739** | **100.0%** | **9,864.0 s** | **17.58** | **15.0** |

---

## 3. Comparative Quality Audit: Expanded Dataset vs Phase 2C.24 Pilot

Direct comparison between the Phase 2C.24 100-clip pilot and the Phase 2C.26 expanded dataset:

| Dimension | Phase 2C.24 Pilot (100 Clips) | Phase 2C.26 Expanded (1,739 Clips) | Delta / Improvement |
| :--- | :---: | :---: | :---: |
| **Total Video Clips** | 100 | **1,739** | **+1,639 clips (+17.4x)** |
| **Training Sentences** | 61 | **1,215** | **+1,154 sentences (+19.9x)** |
| **Validation Sentences** | 19 | **258** | **+239 sentences (+13.6x)** |
| **Test Sentences** | 20 | **266** | **+246 sentences (+13.3x)** |
| **Source Video Isolation** | Uncontrolled | **Strict Group-Split (115 IDs)** | **Zero session leakage** |
| **Training Vocabulary** | 249 words | **2,582 words** | **+2,333 words (+10.4x)** |
| **Total Vocabulary** | 319 words | **3,217 words** | **+2,898 words (+10.1x)** |
| **Val Word-Level OOV Rate** | **31.8%** | **13.04%** | **-18.76% (59% relative drop)** |
| **Test Word-Level OOV Rate** | **28.5%** | **10.90%** | **-17.60% (62% relative drop)** |
| **Mean Target Sentence Length** | 8.1 words | **17.58 words** | **More realistic sentence structure** |
| **Median Target Sentence Length**| 7.0 words | **15.0 words** | **Natural continuous signing** |

---

## 4. Landmark Extraction Quality & Numerical Contract

### 4.1 Feature Layout and Schema Compliance
The continuous landmark features strictly maintain the established 366-dimensional vector contract across all frames:
- **Left Hand:** 21 landmarks $\times$ 3 coords = 63 dims
- **Right Hand:** 21 landmarks $\times$ 3 coords = 63 dims
- **Pose:** 33 landmarks $\times$ 5 attributes ($x, y, z, \text{visibility}, \text{presence}$) = 165 dims
- **Face:** 25 key landmarks $\times$ 3 coords = 75 dims
- **Total Feature Dimension:** $63 + 63 + 165 + 75 = 366$ dimensions per frame.
- **Array Shape:** Chronological `[T, 366]`, `float32`.

### 4.2 Quality Checks on Extracted Features
- **Array Loadability & Corruption:** 0 corrupted `.npy` files.
- **NaN / Infinity Invariants:** 0 occurrences across all audited sequences.
- **Sequence Length Range:**
  - Minimum: 6 frames (~0.2s)
  - Maximum: 638 frames (~21.3s)
  - Mean: 126.5 frames (~4.2s)
  - Median: 110.0 frames (~3.7s)
- **Hand Landmark Tracking Rates:**
  - Left Hand Completely Absent: 1.3% of clips (expected for one-handed signs or out-of-frame gestures)
  - Right Hand Completely Absent: 1.3% of clips
  - Both Hands Completely Absent: 0.7% of clips

---

## 5. Architectural Integrity & Isolation

In accordance with `AGENTS.md` and project instructions:
1. **Isolated Research Trees:** All code and data remain quarantined in:
   - Data: `data/continuous_how2sign_val/`
   - Experiments: `experiments/continuous-asl/phase_2c_26/`
2. **Production Code Untouched:** No production files in `ai/`, `src/`, or `web/` were modified.
3. **Competition & Baseline Protection:** The competition pilot model, 79-class baseline, and browser ONNX runtime were completely untouched.
4. **No Premature Model Claims:** This phase strictly validates dataset readiness and feature extraction. No claims of solved translation are made, and no ad-hoc model tuning was executed.

---

## 6. Recommendations & Next Steps

1. **Dataset Readiness:** The 1,739-clip continuous ASL dataset is fully verified, formatted, and ready to support sequence-to-text modeling experiments.
2. **Architecture Recommendation for Phase 2C.27:**
   - As established in Phase 2C.25, the fixed-vector information bottleneck of standard recurrent decoders caused mode collapse on continuous sentences.
   - For Phase 2C.27, implement an **Attention-augmented Sequence-to-Sequence model** (e.g., Bahdanau Cross-Attention BiGRU or lightweight Transformer Encoder-Decoder) to allow the text decoder to dynamically attend across temporal landmark representations.
3. **Subword Tokenization (BPE/SentencePiece):**
   - While word-level OOV dropped from 31.8% to 13.04%, subword tokenization (Byte-Pair Encoding with ~1,000 vocab) should be considered to reduce the remaining 13% OOV rate to 0.0% open-vocabulary generation.
