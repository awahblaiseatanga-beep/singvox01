# FRESH DIAGNOSTIC SAMPLE: Hand Pipeline Comparison

**Date:** 2026-10-01 19:53:03
**Environment:** Python 3.12.14, MediaPipe 0.10.21, OpenCV 4.11.0, NumPy 1.26.4
**Dataset Source:** ASL Citizen Official Dataset
**Split Files Used:** train.csv, val.csv, test.csv

*WARNING: This is a FRESH independently drafted test sweep. This data is explicitly NOT the historical 2,606-video subset extracted upstream.*

## Methodology
- **Sampling:** Random pull from official split pools constrained to mapped ASL-100 canonical gloss aliases.
- **Sample Size Target:** 40 videos
- **Actual Analyzed:** 40 videos
- **Frames per Video:** 5
- **Unique Signers:** 23
- **Total Frames Evaluated:** 200

## Configurations
- **MediaPipe Holistic:** static_image_mode=True, min_detection_confidence=0.5
- **MediaPipe Hands:** static_image_mode=True, max_num_hands=2, min_detection_confidence=0.5

## Important Caveat
DETECTION IS NOT RECALL. Detector bounding counts do NOT equate to "ground-truth visibility" inside the spatial signing volume. 
A detector flagging `False` could be a true visual occlusion or a bounding model miss. These metrics measure strictly how often the algorithms assert they see a hand.

## Aggregate Results

| Metric | Holistic Detection Rate | Dedicated Hands Detection Rate |
| --- | --- | --- |
| **Left Hand** | 53 detections | 52 detections |
| **Right Hand** | 62 detections | 49 detections |
| **Either Hand** | 82 detections | 79 detections |
| **Both Hands** | 33 detections | 22 detections |
| **Avg MS / Frame** | 69.56 ms | 31.71 ms |

## Interpreting Differences
The raw frame-checks demonstrate relative performance boundaries in strict static environments. MediaPipe Hands naturally processes faster without parsing body/pose graphs, while Holistic inherently ties vectors securely to shoulder/elbow mapping hierarchies. Evaluation points towards testing processing tradeoffs versus density gains if Hands asserts higher trigger volume under motion blur profiles.
