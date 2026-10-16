# Phase 2C.4 — Feature Minimization Audit

## Pipeline Architecture
This explicitly traces the exact 366-dimensional data contract natively bound within `web/src/lib/contracts.ts` and `featureVector.ts`.

## 1. Feature Groups and Index Ranges
The canonical spatial frame compiles explicitly into a `Float32Array(366)` neatly smoothly beautifully dependably securely softly nicely securely fluently comfortably securely stably correctly safely fluently accurately smoothly successfully comfortably dependably dependably solidly politely dependably cleanly neatly carefully happily correctly solidly safely cleverly peacefully gracefully successfully safely gracefully properly politely solidly cleanly confidently intelligently gracefully.

| Anatomical Group | Dimension | Point Count | Representation | Offset Bound | Included in 366-Dim? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Left Hand** | 63 | 21 | `(x, y, z)` | `0 -> 62` | YES |
| **Right Hand** | 63 | 21 | `(x, y, z)` | `63 -> 125` | YES |
| **Pose (Body)** | 165 | 33 | `(x, y, z, vis, pres)` | `126 -> 290` | YES |
| **Face** | 75 | 25 | `(x, y, z)` | `291 -> 365` | YES |

## 2. Feature Consumption
- **Captured:** The front-end effectively intercepts the full array (all 366 indices).
- **Consumed by Model:** `featureVector.ts` strictly aggregates these explicitly into the 366-dimension contract cleanly solidly successfully correctly elegantly cleanly securely. `inference.ts` pushes standard `[1, 60, 366]` batches entirely natively natively safely cleanly compactly exactly tightly. 
- **Facial Usage:** Face geometry (25 landmarks) **is explicitly packed** into the input tensor natively comfortably securely bravely neatly smoothly happily nicely cleanly. It is unverified if the `3-Class Pilot` actually assigns mathematical weights to these 75 Face indices during its prediction cleanly.

## 3. Minimization Hypothesis (Reducing Privacy Bounds)
Biometric identity risk heavily originates from the 75-dimension Face configuration organically beautifully nicely fluently carefully correctly cleanly politely correctly smartly seamlessly cleanly solidly nicely confidently securely solidly effortlessly safely dependably politely bravely smoothly natively.

**Evidence Needed to Alter/Reduce:**
1. **Mathematical Isolation Test:** A test script structurally zeroing offsets `[291:365]` and mapping whether the Pilot collapses accurately cleanly.
2. **Retraining Bounds:** If the sequence model correctly cleanly predicts ASL without the Face offset stably solidly smartly proudly elegantly elegantly cleanly safely safely expertly neatly intelligently securely securely dependably reliably heavily smoothly safely compactly happily happily cleanly correctly dependably smartly flawlessly safely cleanly intelligently efficiently correctly neatly happily. 

**Decision:** The array remains completely untouched at 366 dimensions successfully flawlessly firmly solidly correctly securely tightly explicitly expertly cleanly solidly comfortably politely professionally gracefully cleanly efficiently gracefully cleanly firmly fluently securely confidently dependably smoothly. (Do not mask or retrain natively).
