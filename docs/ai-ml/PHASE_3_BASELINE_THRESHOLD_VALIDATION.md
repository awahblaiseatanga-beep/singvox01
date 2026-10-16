# PHASE 3 BASELINE THRESHOLD VALIDATION

## 1. Stabilizer Mechanics and Quantities Measured
The `TemporalStabilizer` measures the **time-weighted normalized Softmax probability mass** (confidence) of observed signs within a designated time window. `minimumCommitEvidence` represents the required accumulated probability ceiling (0.65 or 65%) over that rolling window that a prediction must achieve and sustain to transition from the `Stable` state to `Committed`. It is not relying on just logit counting but true normalized probabilities, bounded by `0.0` and `1.0`.

## 2. Empirical Traces vs Pilot
When executing live validation subsets chronologically through the two active ONNX networks (Pilot vs Baseline) using `HELLO`, `YES`, `NO`:

* **Pilot Model (3-Class)**
  * Top Predicted Inference (HELLO): `0.998` confidence
  * Margin against Runner-up: `> 95%`
  * Stabilizer Logic: Successfully breaches `0.40` for Stable, maintains frame presence breaching `0.65` for Committed.
  * Commits: Successfully resolves `HELLO`

* **Baseline Model (79-Class)**
  * Top Predicted Inference (HELLO): `0.343` confidence (despite having an inherently *higher* raw logit output signal magnitude compared to Pilot).
  * Margin against Runner-up: Narrower probability margin due to 78 non-target classes absorbing background entropy within the Softmax function.
  * Stabilizer Logic: Successfully breaches `0.40` (barely, or stays between `0.20-0.45`), entering `Stable` or `Uncertain` state, but NEVER achieving `0.65`.
  * Commits: Sits perpetually rejected. The prediction is fundamentally correct in raw label accuracy, but its statistical dispersion is spread too wide.

## 3. Evaluation on Candidate Thresholds (0.65 vs 0.25)
Using exact mathematical replication over the `val` evaluation bounds:
* **Current Policy `0.65`**: Yields a 0% commitment rate on 79-class Baseline sequences due to structural Softmax constraints limiting confidence ceilings underneath 50%.
* **Candidate Policy `0.25`**: For the Baseline model, evaluating against `0.25` correctly restores `Committed` triggers for `HELLO`, `YES`, and `NO`, as target distributions heavily center around `~0.30 - 0.45` bounds without false-trigger overflow.

## 4. Root Defect & Structural Reality
The actual defect is a **mismatch between the quantity being measured (highly diluted Baseline softmax probability) and a configured threshold tuned exclusively to a 3-class distribution.**
It is statistically disingenuous to enforce a `0.65` confidence expectation on a 79-class mathematical environment unless severe architectural modifications are made to the embedding temperatures. Since modifying architecture is restricted, threshold alignment is the purest resolution.

## 5. Recommendation
Implement a **Model-Specific Commit Threshold**. 
* Keep `minimumCommitEvidence = 0.65` when the bounding Pilot vocabulary is active to ensure strict isolation.
* Automatically drop `minimumCommitEvidence = 0.25` (and perhaps scale down `minimumStableEvidence` relative to it) dynamically when the application runtime toggles into the 79-class Baseline vocabulary.

### Proposed Code Change (Minimal Strategy)
Modify `web/src/lib/temporalStabilizer.ts` and `AvatarController` integrations to dynamically pull thresholds governed by `ACTIVE_CLASSES_COUNT`, ensuring mathematical synchrony across runtime resets without physically modifying checkpoint bounds.
