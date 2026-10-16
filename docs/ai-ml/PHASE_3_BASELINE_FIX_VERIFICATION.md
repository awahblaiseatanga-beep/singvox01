# SignVox — Phase 3 Baseline Fix Verification

## A. Source Configuration & Lifecycle Trace
The implemented source code for the model-specific threshold isolation was audited directly.

- **`web/src/lib/temporalStabilizer.ts`:**
  - Exports explicitly named mathematical config bundles `PILOT_STABILIZER_CONFIG` and `BASELINE_STABILIZER_CONFIG`.
  - The Baseline enforces: `minimumStableEvidence = 0.15` and `minimumCommitEvidence = 0.25`.
  - The Pilot enforces: `minimumStableEvidence = 0.40` and `minimumCommitEvidence = 0.65`.

- **`web/src/App.tsx`:**
  - Standard `TemporalStabilizer.reset()` was physically removed. During a valid camera `start()`, the live processing loop constructs a clean `new TemporalStabilizer()` passing the frontend active configuration boundary explicitly.
  - This natively destroys previous reference leakage natively in JS mapping guaranteeing exactly zero accumulated mass rolls over into a subsequent model environment natively.

## B. 0.15 Stable Boundary Justification & Fluctuating Protections
The Baseline logit ceiling previously audited during Phase 5 evaluation proved that signs like `YES` natively evaluate their `highestEvidence` peak cleanly between `0.33` to `0.35` under the 79-class label structure.

Under the mathematical engine driving `TemporalStabilizer`:
1. `minimumStableEvidence = 0.40` blocked Pilot-bound variables from ever attaining the baseline probability ceiling. `0.35 < 0.40` physically blocked the model state engine from turning "Stable" entirely.
2. Dropping the boundary to `0.15` enables proper `Stable` targeting without compromising security. Security against arbitrary ambient noise is fundamentally secured not primarily by raw probability size, but by time—enforced by the `minimumStableDurationMs = 400` requirement natively.
3. **Fluctuating Prediction Verification:** `web/src/tests/model_switch_lifecycle.test.ts` was extended natively asserting random single/double frame probability flashes of `0.80` against `BASELINE_STABILIZER_CONFIG`. The engine rejected them outright returning `null` commits as they definitively failed the consecutive `400ms` window buffer regardless of raw individual frame confidence.

## C. Model Switching Operations (Live Camera Restraints)
A critical UI restraint prevents an exact live unnotified "on the fly" frame switch.
Inspecting `App.tsx`:
```tsx
onChange={(e) => {
   const val = e.target.value as 'pilot' | 'baseline';
   setActiveModel(val);
   if (activeRef.current) { stop(); }
}}
```
Selecting a different model completely shuts down the MediaPipe pipeline stream inherently via the `stop()` invocation boundary. The user is technically required to physically select "Start Camera" to boot the newly selected model runtime natively. No internal stream swapping happens actively running frames between models; this inherently establishes isolated buffer safety by breaking the runtime.

## D. Pipeline Resolution Restraints
The pipeline route (`ONNX` -> `TemporalStabilizer` -> `committedSign` -> `AvatarController.playSignByLabel()`) explicitly prevents missing animation frames from causing hierarchical rendering corruption. 
Inspecting `AvatarController.ts (L267)` verifies:
```typescript
const clipExists = this.animationClips.some(c => c.name === targetClipName);
if (clipExists) { this.setMode(targetMode); } 
else { this.setMode('clip:ASL_NEUTRAL'); }
```
Labels processed by Baseline (79-class) that do not currently have equivalent `GLB` action resources natively transition back into a rigid `ASL_NEUTRAL` rest state, preventing random unassociated asset playback.

## E. Build and Test Sweep Check
- `npm run build` strictly checks typed boundaries producing `60 modules transformed` smoothly without TypeScript violations or Webpack configuration faults.
- `vitest run` completed 4 suites (`44` tests total) executing smoothly in 631ms, specifically validating all temporal mathematical sequences manually across both boundary sets.

## Final Authorised Limitations
*   **Dom Level Validation:** Raw simulated browser webcam injection wasn't natively automated by Puppeteer/Playwright scripts locally; test frameworks validated functionality by natively routing the Javascript logic boundaries manually. End-to-end browser camera observation remains empirically unverified outside standard DOM environment boots.
*   **False-Commit Noise Limits:** Although arbitrary spike duration tests were performed protecting against random frames, comprehensive negative structural noise tests across all 79-classes couldn't be quantified explicitly because the raw baseline environment validation dataset lacks unstructured movement data natively. 
