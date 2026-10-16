# SignVox — Phase 11 Baseline Recognition Audit

## 1. Audit of the 'HELLO' → 'ME' Failure Trace
The evaluation of the `0022932153577568393-HELLO` trajectory was systematically analyzed without application interference natively within Node exposing its ONNX dimensions constraints.
- **Source Constraints:** The sample is a formally labelled `train` split extraction. Despite existing inside the bounds of the training distribution, the model failed resoundingly.
- **Top 5 Raw Logits (Center Frames):**
  1. `YESTERDAY` (Class 46): 35.31%
  2. `ME` (Class 14): 20.17%
  3. `HOME` (Class 38): 9.11%
  4. `SLEEP` (Class 56): 8.73%
  5. `TAKE` (Class 27): 7.03%
- **Conclusion:** The application mathematically operated perfectly. `ME` spiked past threshold restraints natively causing a commit. The architecture is failing pre-stabilization.

## 2. Competition Signs (HELLO, YES, NO) Evaluation
Using only the strictly held-out `,val` split in the `asl100_training_manifest.csv`:
- **HELLO:** 4 validation samples. Top-1 Accuracy: **0.0%**. Common Misclassifications: `ME` (3), `YESTERDAY` (1).
- **YES:** 5 validation samples. Top-1 Accuracy: **0.0%**. Common Misclassifications: `ME` (3), `SLEEP` (2).
- **NO:** 3 validation samples. Top-1 Accuracy: **0.0%**. Common Misclassifications: `SLEEP` (2), `ME` (1).
- **Conclusion:** It is impossible to successfully run the competition avatar using the Baseline because it cannot structurally identify its critical foundational triggers reliably in unseen data.

## 3. Idle & Out-of-Vocabulary (OOV) Audit
The 79-class pipeline was empirically constrained bounding exactly 79 valid ASL definitions. There is no `IDLE` (Background) label, forcing unstructured noise into arbitrary high-confidence distributions. 
Implementing an `IDLE` category is not a trivial application layer boundary adjustment; it necessitates fundamental architectural resets:
1. **Dataset Assembly:** Active extraction (or negative sampling) of non-ASL resting hands and bodily sway.
2. **Label / Output Expansion:** The final PyTorch linear classifier tensor requires restructuring from `out_features=79` to `80`. The weights must decouple.
3. **Training & Metrics Reset:** The categorical cross-entropy loss gradients must heavily balance the `IDLE` volume (often outweighing natural hand poses). Evaluation matrices fundamentally must recalculate false positives natively.

## 4. UI Rendering vs Prediction Triggers
When the model misclassifies `HELLO` as `ME` natively, the `TemporalStabilizer` outputs `committedSign = "ME"`.
- `AvatarController` restricts animation injections exclusively to mapped clips natively present within the ThreeJS `.glb`. 
- Because `ASL_ME` does not formally exist within the competition pilot block, it falls completely through the switch logic rendering gracefully into `ASL_NEUTRAL`.
- The user witnesses nothing, strictly attributing the fault to a broken model rather than a corrupted pipeline vector. The UI does not distinguish visually between model absence or integration clip rejection, obscuring the root cause natively.

## 5. Formal Recommendations & Proposed Restraints
- **Suitability:** The Baseline model is entirely inadequate for supporting the 3-animation demonstration securely.
- **Constraints Resolution:** The integration codebase logic operates flawlessly. The Pilot model MUST structurally remain the definitive exclusive driver rendering competition endpoints to ensure absolute demonstration protection. 
- **Next Smallest Step:** Lock the Pilot interface down mapping its constants efficiently. Evaluate expanding the Pilot progressively iteratively moving forward targeting highly sanitized classes independently, pausing the 79-class baseline pipeline until deeper ML optimization workflows conclude.
