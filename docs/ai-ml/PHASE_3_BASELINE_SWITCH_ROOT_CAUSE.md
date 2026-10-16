# PHASE 3 BASELINE SWITCH: ROOT CAUSE ANALYSIS

## 1. Reproduction Result
**Result:** Reproduced. 
**Evidence:** The manual tracing logic confirms that when the application switches from the `pilot` (3-class) model to the `baseline` (79-class) model, identical confidence strength inside the ONNX model fails to trigger the avatar due to a mathematical artifact in the pipeline's stabilization thresholds. The inference and visualization pipeline continue running normally, but animations drop out.

## 2. Root Cause
The root cause is located in **C. Temporal stabilization and commitment**.

When switching from the 3-class Pilot to the 79-class Baseline, the `minimumCommitEvidence` threshold configured in `TemporalStabilizer` (`0.65`) becomes significantly harder—and in some standard ranges, impossible—for the Baseline model to reach.

Because Softmax distributes the total probability mass (sum = 1.0) among all available classes, the 79-class Baseline inherently spreads out the confidence baseline. Even if the actual target logit signal is strong (e.g., 5.0 vs 1.0 for all others), the 78 non-target classes accumulate enough denominator mass to dilute the top prediction's final probability score to roughly `~0.41`. 

Because `0.41` is greater than `minimumStableEvidence` (`0.40`) but less than `minimumCommitEvidence` (`0.65`), the Stabilizer enters a `Stable` state (showing the recognized sign in the UI) but **never commits the sign** (`committedSign = null`). 

Because `committedSign` is never populated, `AvatarController.playSignByLabel()` is never called, leaving the avatar permanently in its `ASL_NEUTRAL` resting pose.

## 3. Evidence
- **File:** `web/src/lib/inference.ts` calculates standard Softmax: `const exps = logits.map((x) => Math.exp(x - maxLogit));`
- **File:** `web/src/lib/temporalStabilizer.ts` restricts committing based on `stabilityEvidence >= this.config.minimumCommitEvidence` (default `0.65`).
- **File:** `web/src/App.tsx` routes to the avatar strictly gated by `if (state.committedSign)`.
- **Diagnostic Test (`web/src/tests/softmax_trace.test.ts`):** 
  - Using a mock logit size of `5.0` against a noise floor of `1.0`:
  - **Pilot (3 classes):** Reaches **96.47%**. Surpasses `0.65`. Avatar plays.
  - **Baseline (79 classes):** Dilutes to **41.18%**. Falls below `0.65`. Avatar stalls.

## 4. Pilot versus Baseline Comparison
| Stage | Pilot (3 Classes) | Baseline (79 Classes) |
| :--- | :--- | :--- |
| **Logit Output Strength** | Target: 5.0, Noise: 1.0 | Target: 5.0, Noise: 1.0 |
| **Softmax Probability** | ~96% | ~41% |
| **Stabilizer State** | `Stable` | `Stable` |
| **Committed Label** | `"YES"` | `null` |
| **Avatar controller logic** | Plays `ASL_YES` | Never called, remains `ASL_NEUTRAL` |

## 5. Failure Boundary
The earliest pipeline stage where correct behavior breaks is inside `web/src/lib/temporalStabilizer.ts` during the **Evaluate commits** logic. The inference produces valid vocab classes, the mapping aligns correctly, but the state refuses to transition from `Stable` to `Committed`.

## 6. Contributing Factors
- **Proven:** Logit-to-Softmax expansion dynamically penalizes larger vocabularies at arbitrary confidence thresholds.
- **Proven:** `minimumCommitEvidence` is currently a monolithic threshold, ignorant of the active model's underlying vocabulary count.
- **Ruled out (Candidate B):** Class indexing misalignments do not exist. Class 0 maps to `HELLO`, class 9 maps to `YES`, and class 10 maps to `NO` exactly matching `ASL_VOCAB`.
- **Ruled out (Candidate D/E):** `AvatarController` accurately delegates unknown signs to `ASL_NEUTRAL` without corrupting internal mixer looping state, provided it actually receives a commit event.

## 7. Minimal Fix Proposal
Dynamically adjust the `minimumCommitEvidence` and `minimumStableEvidence` thresholds when initializing the `SpoterInferenceSession` based on the vocabulary size. 

For example, in `App.tsx`:
```tsx
const isPilot = activeModelRef.current === 'pilot';
stabilizerRef.current = new TemporalStabilizer({
    minimumStableEvidence: isPilot ? 0.40 : 0.15,
    minimumCommitEvidence: isPilot ? 0.65 : 0.25,
});
```
(Exact mathematical scaling factors should be derived from the model's test validation logits).

## 8. Regression Tests
To ensure the fix does not break existing pilot logic:
1. `tests/stabilizer.test.ts`: Ensure dynamic initialization properties load correctly.
2. Ensure the Pilot model still actively rejects false positives at `0.65` instead of globally lowering all logic to `0.25`.

## 9. Unresolved Limitations
Even with this fix, the 79-class Baseline will inevitably commit valid ASL classes (e.g. `GOOD`, `BATHROOM`) that lack corresponding ThreeJS animation clips. The `AvatarController` will smoothly fall back to `ASL_NEUTRAL` for these words, but the user experience will appear frozen despite the AI genuinely recognizing the sign. Expanding the asset library is ultimately required to capitalize on the baseline.
