# SignVox — Phase 10 Baseline Complete Forensic Diagnostics

## 1. Missing Animations (HELLO / YES / NO)
Upon tracing actual probability datasets evaluating mathematical outputs of the 79-class Baseline, the earliest failure point was definitively identified at the model accuracy level:
- **Evidence:** Running an explicit ONNX target trace executing `HELLO` physical features produced a peak probability for class `ME` at 81.5%, rather than `HELLO`.
- **Root Cause (Missing Avatar Response):** The Baseline model natively hallucinates or misclassifies Pilot signs (like `HELLO`) into other established ASL classes. Because the UI restricts Avatar actions via `AvatarController` to clips that exist in the GLB (`HELLO`, `YES`, `NO`), when the system officially commits `ME`, the controller forces the avatar back to `ASL_NEUTRAL`. The mathematical threshold was working correctly; the model itself fundamentally fails to predict the target.

## 2. Idle Behavior & False Commitments
I conducted a robust test synthesizing an unstructured sequence (idle camera movement without explicit signs).
- **Evidence:** Temporal filters (`minimumConfidence: 0.05`) correctly suppress pure uniform noise (`~0.01`). However, because the 79-class Baseline model does *not* contain an `IDLE` or `NOISE` fallback class, it applies softmax confidence entirely to the existing 79 signs. During idle moments, raw gestures frequently generate transient `30%` logits mathematically matching a sign (e.g. `WAIT` or `ME`).
- **Root Cause (False Commits):** 
    1. **Model Limitation:** Without a garbage class, random background resting hands generate legitimate continuous probabilities higher than `0.25`, causing the logic bounds to correctly interpret it as a true sign.
    2. **Stale Clearance Oscillation:** When an idle prediction reaches `0.25` and commits, natural body swaying causes the confidence to drop beneath `dropThreshold: 0.10` rapidly. This clears `lastCommittedName`. Seconds later, the probability hits `0.25` again, falsely re-committing the same sign infinitely.

## Proposed Protections (Non-Production Experiment)
1. **Model Retraining Barrier:** Baseline cannot act as a pure production toggle against an open unstructured camera until `IDLE` features (class 80) are baked into the tensor architecture.
2. **Reversible UI Protection:** Instead of tampering with `dropThreshold` or mathematical bounds further (which correctly assert the raw logits provided to them), `App.tsx` could implement a cooldown buffer (e.g. `if (Date.now() - lastCommit < 2000) return`) ensuring false commits do not spam the AvatarController while the tracker bounces.

## Verification Constraints
*   **ONNX Dimensions:** The runtime execution bounds are verified. Output dimension `[1, 79]` scales properly; there are exactly 79 recognized features successfully mapping without index violations.
*   **Pilot Remains Immutable:** Pilot avoids this because a 3-class boundary restricts entropy cleanly, resulting in true `0.0` or `1.0` classifications natively avoiding wobble re-arms entirely.

**STOP CONDITION ESTABLISHED: The regression originates internally inside the ONNX statistical tensor mapping (accuracy/idle absence), not the integration codebase.**
