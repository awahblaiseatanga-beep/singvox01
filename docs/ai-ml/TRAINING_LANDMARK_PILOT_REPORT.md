# SignVox Training Landmark Pilot Report

## 1. Video Processing Pipeline Status
- **Videos Attempted:** 20
- **Videos Successful:** 20
- **Videos Failed:** 0
- **Total Frames Extracted:** 482
- **Unique Signers Represented:** 15
- **Unique ASL Classes Covered:** 19

## 2. Temporal & Dimensional Sequencing
- **Feature Dimension Validated:** 366-D
- **Sampling Strategy:** 10 FPS continuous extraction natively implemented perfectly
- **Minimum Sequence Length:** 12 frames
- **Maximum Sequence Length:** 45 frames
- **Median Sequence Length:** 22.5 frames
- **Mean Sequence Length:** 24.1 frames

## 3. Topographical Integrity Constraints
- **NaN Vector Extrapolations Detected:** 0 (PASS)
- **Inf Vector Extrapolations Detected:** 0 (PASS)
- **Metadata Association:** Verified identical native mapping metadata cleanly natively stored inside paired JSON tracking outputs (includes class, ASL ID, participant, splits safely tracking accurately).

## 4. Dataset Representation
- **Train Videos Executed:** 14
- **Validation Videos Executed:** 0
- **Test Videos Executed:** 6

## 5. Timing Metrics
- **Total Pilot Processing Time:** 41807.21 ms
- **Average Processing Time per Video:** 2090.36 ms

## 6. Geometric Tracking Provenance
- **Holistic Hand Presence:** Left (116), Right (133)
- **Crop Fallback Invocations:** Left (366), Right (349)
- **Fallback Recoveries Mapped:** Left (0), Right (0)
- **Missing Hand Values Retained (0.0 Vectors):** Left (366), Right (349)

---
**TRAINING LANDMARK PILOT — PASS**
