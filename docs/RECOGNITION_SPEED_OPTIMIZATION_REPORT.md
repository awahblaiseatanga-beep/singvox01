# SignVox — Real-Time Recognition Speed Optimization (2026-10-16)

Scope: make camera detection, temporal buffering, recognition and avatar response
noticeably faster in the browser app at `Singvox/web`, without disturbing the
recovered 79-class baseline, the 3-class pilot, the model registry, the output-size
guard, the recognition gate, the frozen vocabulary, the 366-D SPOTER V2 feature
contract, `V2_SCALARS`, the class-index mapping, `AvatarController` or the
production GLB.

Everything below is measured on this machine. Where a number is arithmetic on
measured values rather than a direct measurement, it says so. Nothing was
retrained, re-exported or replaced; no threshold was lowered.

---

## 1. Headline result

| Claim | Evidence type | Result |
|---|---|---|
| The 60-frame window is now written on the contract's fixed 125 ms grid | live production build, real camera, diagnostics screen | `Duration 7375 ms`, `Cadence 125 ± 0 ms/frame` (was 60 × the detection interval, i.e. 9.5–22.2 s with jitter) |
| The window is complete sooner | recorded-clip replay (`temporal_sampling_parity.test.ts`) | window ready at **7375 ms** instead of **8875 ms** with device observations every 150 ms; at the live observation rates actually measured (2.7/s and 6.3/s) the old loop needed **22.2 s** and **9.5 s** (arithmetic on measured rates) |
| Landmarkers are faster | recorded replay, 40 frames, 3 repeats | CPU delegate **186.7–195.0 ms**/frame → GPU delegate **152.2–160.8 ms**/frame (−18 %) |
| Interpolated grid frames do not degrade recognition | recorded-clip replay with the real model + stabilizer | HELLO: commits `[HELLO]`, final window `HELLO 0.982` (held grid at the same cadence drifted to `CHILD 0.897`); YES: commits `[YES]`, final `YES 0.927` vs `0.945` held |
| Recognition no longer blocks the detector (available, not shipped as default) | live dev-server A/B | **6.3** landmark observations/s with the ORT worker vs **2.8** in-page |
| No regressions | `tsc -b`, `npm run build`, `npx vitest run` | exit 0 / exit 0 / exit 0 — 29 files, 164 tests, 0 failures |

The 79-class baseline still returns 79 logits and the pilot 3 (asserted on every
prediction in the replay tests and on the live `#diagnostics` model test).

---

## 2. Instrumentation used

The existing profiler (`web/src/lib/latencyProfiler.ts`, the 10-stage cold-start /
steady-state table on `#diagnostics`) was reused, not replaced. Two additions were
needed and are kept:

- `web/bench/recognition-bench.html` — dev-only harness (not part of the build) that
  replays recorded 1280×720 frames through the app's real MediaPipe options and the
  app's real ONNX session code, and reports per-model latency, detections, landmark
  agreement between variants, main-thread blocking, ONNX session/warm-up/steady
  timings. Reproduce with the dev server running and clicking **Run benchmark** at
  `/bench/recognition-bench.html`.
- `Metrics.observationFps`, `Metrics.interpolated` and `Metrics.mpDelegate`, surfaced
  on `#diagnostics` so the two clocks (observations vs buffer writes) and the active
  delegate are visible during the demo.

Recorded clips used by the harness/test live in `web/bench/clips/` (outside
`public/`, so they are never shipped in a build).

---

## 3. Measured bottlenecks, in order of impact

### 3.1 The buffer was written at the detection rate, not on the contract's grid

`processLoop` pushed one buffer frame per *completed detection* (gated only by
`elapsedSinceBufferPush >= 125 ms`, which is always true when a detection costs
>125 ms). With live observations measured at **2.7–6.3/s**, the 60-frame window
therefore needed **9.5–22.2 s** of wall-clock time to fill, and consecutive buffered
frames sat 159–370 ms apart while the model was trained on frames 100 ms apart
(`docs/ai-ml/LANDMARK_PIPELINE_SPEC.md`: 10 fps extraction). Two consequences: the
first possible recognition of a session arrived long after the sign, and live motion
was temporally over-stretched relative to training.

This is the biggest user-visible defect and the one that was fixed.

### 3.2 MediaPipe landmarker cost

Bench, 40 recorded frames, 1280×720 source (table says median total / effective fps):

| Variant | pose | hands | face | total | fps |
|---|---:|---:|---:|---:|---:|
| CPU delegate, native | 81–84 ms | 83–86 ms | 14–15 ms | **186.7–195.0 ms** | 5.1–5.4 |
| GPU delegate, native | 62–64 ms | 73–75 ms | 11–12 ms | **152.2–160.8 ms** | 6.2–6.6 |
| GPU delegate, 640×360 | 54–62 ms | 67–72 ms | 10–12 ms | **135.5–148.8 ms** | 6.7–7.4 |
| CPU delegate, 640×360 | 80–82 ms | 79–80 ms | 8–12 ms | **176.7–180.5 ms** | 5.5–5.7 |

Detection counts were unchanged on GPU (pose 40/40, hands 39/40) and the
**face landmarker returned 0 landmarks on this recorded clip at every resolution**
(live camera: face present in 78 % of the live window, so this is clip framing, not
a pipeline fault — see §8).

### 3.3 ONNX inference on the main thread

Bench (in-page, HTTP cache warm):

| Model | session create | warm-up | steady inference (median / p95) |
|---|---:|---:|---:|
| 79-class baseline | 1673–1865 ms | 190–236 ms | **158.2–161.2 / 166.4–181.3 ms** |
| 3-class pilot | 1196–1296 ms | 192–235 ms | 162.3–181.5 / 174.5–203.9 ms |

During a ~2 s burst of 12 inferences the page delivered **0 MessageChannel macrotasks
and 0 animation frames** — the WASM compute monopolises the main thread. Combined with
§3.2, detector and recognizer serialise: live, one cycle costs MediaPipe(133–176 ms) +
inference(175–293 ms), which is exactly why the measured observation rate was only
2.7/s in the in-page configuration.

`crossOriginIsolated` is `false`, `SharedArrayBuffer` is unavailable and
`navigator.hardwareConcurrency` is 8, so ORT Web runs **single-threaded** even though
8 cores exist. Multi-threaded WASM needs COOP/COEP headers, which would also gate the
cross-origin MediaPipe CDN assets; not attempted tonight (see §8).

### 3.4 Cold start

| Stage | Dev server | Production build (fresh origin) |
|---|---:|---:|
| Camera + video readiness | 3965–5141 ms | 6794 ms |
| MediaPipe initialisation | 1184–1944 ms | 1944 ms |
| ONNX model initialisation | 3431–3763 ms | **17645 ms** |
| ONNX kernel warm-up | 181–248 ms | 248 ms |
| Sequence buffer ready (60 frames) | **7435–7497 ms** | **7420 ms** |

The 187 MB `spoter_v2_model.onnx.data` external-data file dominates cold start: the
17.6 s production figure is the same model on an origin that had not cached it yet.
Buffer readiness is now close to the arithmetic minimum (60 × 125 ms = 7.5 s).

### 3.5 Resolution is not a bottleneck

640×360 with the CPU delegate is 180.5 ms vs 186.7 ms native (+3 % throughput) — far
too small to justify the measured landmark drift (§7).

---

## 4. Changes made

| File | Change |
|---|---|
| `web/src/lib/temporalSampler.ts` **(new)** | `TemporalSampler`: keeps the two most recent real observations and emits buffer frames on the fixed 125 ms grid. A grid point between two observations is the per-group linear blend of exactly those two; a grid point at/after the newest observation is that observation itself. A group missing in either bracketing observation is **held** from the newest one (never blended towards the zero fill). Pose visibility/presence are copied, never blended. A page stalled past catch-up (8 grid points) restarts the grid instead of emitting a burst of stale motion. |
| `web/src/engine/useSignVoxEngine.ts` | Feature assembly + V2 normalization now run once per real detection; their result is handed to the sampler, and the sampler's output is what is pushed into the `SequenceBuffer` (same 366-D vectors, same `FrameMetadata` presence fields, grid timestamps instead of detection timestamps). Metrics now report buffer frames/s, landmark observations/s, whether the newest frame is interpolated, and the MediaPipe delegate. Sampler + counters reset on start/stop. The `PROCESS_INTERVAL_MS` push gate and `lastBufferPushRef` are gone. |
| `web/src/lib/mediapipe.ts` | Landmarkers are created with the **GPU** delegate, each with an independent automatic fallback to CPU if creation fails, and the pipeline reports which delegate it actually got (`pipeline.delegates`). Model URLs, running modes and frame input are unchanged. |
| `web/src/lib/inference.ts` | `wasmPaths` are resolved to absolute URLs (required by any worker-hosted loader); the ORT proxy worker is available as an opt-in (`VITE_ORT_WASM_PROXY=1`, default **off**) with a best-effort in-page retry; `provider` reports `wasm (worker)` when it is used. Nothing about tensor creation, softmax, or the output-size guard changed. |
| `web/src/components/DiagnosticDashboard.tsx` | Shows buffer frames/s (target 8), landmark observations/s, whether the newest buffer frame is interpolated, and the delegate (pose/hands/face). |
| `web/src/lib/temporalSampler.test.ts` **(new)** | 9 tests: grid start/cadence, blend maths, "never half-fill a missing hand", "hold a lost group rather than blend it away", pose confidences not blended, stall restart, reset, 366-D finiteness. |
| `web/src/tests/temporal_sampling_parity.test.ts` **(new)** | 3-arm recorded-clip replay (old per-observation window / fixed grid with hold / fixed grid with the shipped sampler) through the real `SequenceBuffer`, `TemporalStabilizer` and ONNX session. |
| `web/src/tests/baseline_threshold_eval.test.ts` | Declares an explicit 300 s timeout for the existing ~108 s ONNX trace (test configuration only — **no assertion was changed**). Needed because the new parity replay runs in parallel with it. |
| `web/bench/recognition-bench.html` **(new)** | Measurement harness (dev-only, not shipped). |
| `web/bench/clips/*.mp4` | Recorded replay clips moved out of `public/` so they are not deployed. |

Deliberately **not** changed: model weights, ONNX exports, `ASL_VOCAB`/`PILOT_VOCAB`,
the 366-D layout, `V2_SCALARS`, `class_index_mapping.json`, the model registry, the
output-size guard, the recognition gate thresholds, `TemporalStabilizer` configs,
`AvatarController`, the production GLB, the five routes, and the waiting-list form.

---

## 5. Before/after per stage (live sessions, real camera, `#diagnostics`)

Two live runs of the dev server on the 79-class baseline. Both are after the grid
change (that is the shipped state); they differ only in whether the ONNX worker was
enabled, which is the A/B reported in §7.

| Measurement | In-page inference | ORT worker |
|---|---:|---:|
| Buffer frames/s (target 8) | 8.4 | 7.9 |
| **Landmark observations/s** | **2.8** | **6.3** |
| Camera FPS | 2.9 | 6.4 |
| MediaPipe detect (median / p95) | 156.8 / 226.1 ms | 154.9 / 211.5 ms |
| ├ pose | 56.1 ms | 54.5 ms |
| ├ hands | 78.6 ms | 76.2 ms |
| └ face | 25.4 ms | 25.2 ms |
| ONNX inference (median / p95) | 174.8 / 198.7 ms | 292.7 / 395.3 ms |
| End-to-end frame (median / p95) | 157.2 / 226.4 ms | 155.3 / 211.8 ms |
| Cold: ONNX init / buffer ready | 3431 / 7435 ms | 3763 / 7497 ms |

Before this pass the same loop pushed one frame per detection instead of one per
125 ms, so at the measured observation rates the window spanned **~21.4 s** (in-page,
2.8/s) or **~9.5 s** (worker, 6.3/s) instead of the contract's 7.5 s. The live
production run reports the resulting window as `Duration 7375 ms`,
`Cadence 125 ± 0 ms/frame`, 0 non-finite frames.

Production build, live camera (`vite preview`, default configuration): delegate
`GPU/GPU/GPU`, detect median 166.45 ms (p95 229.4), ONNX inference median 181.35 ms
(p95 228), buffer frames/s 8.0, observations 2.7/s, window `125 ± 0 ms/frame`, and
live commits flowing (`LOVE`, `FATHER`, `SLOW` were committed by the model during the
session, with the avatar correctly refusing to animate them because only HELLO/YES/NO
have clips).

---

## 6. Recognition comparison on identical samples

`temporal_sampling_parity.test.ts` replays the same recorded clip through three
framings, using the recorded 10 fps features as ground truth and modelling a device
that observes the signer every 150 ms (the measured landmarker cost on the GPU
delegate). Timeline = 2 s neutral hold + clip, padded to 12 s.

| Clip | Arm | Window ready | Inferences | Commits | Final window |
|---|---|---:|---:|---|---|
| HELLO (3.1 s) | per-observation (old) | 8875 ms | 26 | `[HELLO]` | HELLO 0.998 |
| HELLO | fixed grid, hold | 7375 ms | 38 | `[HELLO]` | **CHILD 0.897** |
| HELLO | **fixed grid, interpolated (shipped)** | **7375 ms** | 38 | `[HELLO]` | **HELLO 0.982** |
| YES (10.0 s) | per-observation (old) | 8875 ms | 26 | `[YES]` | YES 0.956 |
| YES | fixed grid, hold | 7375 ms | 38 | `[YES]` | YES 0.945 |
| YES | **fixed grid, interpolated (shipped)** | **7375 ms** | 38 | `[YES]` | **YES 0.927** |

Reading: the fixed grid completes the window 1500 ms sooner on a 150 ms-observation
device, both framings still commit the clip's own sign, and on HELLO the interpolated
framing resolves a decision the held grid gets wrong. This is the check the task asked
for before enabling a temporal change: the recorded sign is still recognised, and no
new class is invented.

---

## 7. Experiments run and **not** adopted

**640×360 detector input.** Faster (GPU: 135.5 ms vs 154.9 ms native, −12 %) with the
same pose detections, but landmark agreement against the native run degrades:
mean absolute difference of normalized coordinates 0.0081 vs 0.0055 for GPU-native,
p95 0.0354 vs 0.0258, **max 0.4809** (a single hand landmark jumping), and one hand
frame in 40 loses detection. A downscaled hand-landmark estimate feeds the hand blocks
that carry the recognition signal, so a 12 % gain does not justify that drift. **Not
adopted**; the native resolution is kept. The config remains one edit away
(`web/bench/recognition-bench.html` contains the comparison).

**ORT proxy worker as the default.** Live, it more than doubles the observation rate
(2.8 → 6.3/s) and keeps the main thread free between detects, but it cannot boot from
the Vite production bundle: ORT instantiates its worker from a URL derived from ORT's
own `import.meta.url`, which the bundler collapses onto the single application chunk;
the worker then loads the app bundle and dies with
`Uncaught ReferenceError: document is not defined`. Because ORT's WASM init is
one-shot, the in-page retry cannot recover in that page either, so the production
build lost ONNX entirely (reproduced against `vite preview`, then fixed by defaulting
the flag off and re-verified: `[ONNX] Session Initialized via wasm` and live commits
flowing). **Shipped off**, available as `VITE_ORT_WASM_PROXY=1` for development, with
the failure path now logging what to do. §8 has the fix.

**Shortened window / startup padding.** Not attempted: a partly-filled window is the
documented attractor-class failure mode from the recovery audit (§4.2 — an all-zero
window returns SICK 0.856), and the task forbids fabricating landmarks to appear
faster. The only startup acceleration kept is that the grid starts on the first
observation.

---

## 8. Remaining blockers and recommendations

1. **Cold start is now dominated by the 187 MB external-data file** (17.6 s on an
   uncached origin vs 3.4–3.8 s warm). Recommended next: serve the model and its
   `.data` with immutable caching and a preload started before the camera prompt, or
   ship a smaller graph. This is the largest remaining user-visible delay and it is
   not a code-path problem.
2. **The ORT worker needs a production-safe URL.** Writing our own module worker
   (`new Worker(new URL('./inferenceWorker.ts', import.meta.url), { type: 'module' })`,
   which Vite emits and rewrites correctly) would recover the measured 6.3 vs 2.8
   observations/s in a build. Verify in dev *and* against `vite preview` before
   flipping the default, because the failure mode is total loss of ONNX.
3. **Single-threaded ORT.** `crossOriginIsolated` is false, so the 8 available cores
   are unused by recognition. COOP/COEP headers would enable multi-threaded WASM but
   also gate the cross-origin MediaPipe CDN assets; whitelist or self-host those first,
   and measure before/after with the harness.
4. **Live-signer accuracy is still unverified for every class** — unchanged from the
   recovery audit. The live commits observed tonight belong to an uncontrolled,
   unintentional performance test; they are evidence that the path *runs*, not that it
   is accurate. The next real step is the controlled 5-trial recorder on
   `#diagnostics` with one signer, one sign at a time.
5. **Face landmarks.** The face landmarker returned 0 landmarks on the recorded
   1280×720 bench clip at every resolution (`faceFramesDetected: 0`), while the live
   camera filled the face slot in 78 % of the window. Confirm on the demo device that a
   distant/downscaled signer still yields face landmarks, because the face block is 75
   of the 366 features and was present during training.
6. **No idle/rejection path and only 3 of 79 avatar clips** remain the product-level
   blockers (unchanged): a rest pose can still produce a confident class, which is why
   the recognition gate and the text-only avatar honesty exist.
7. **Suite runtime.** The new parity replay adds ~31 s and, running in parallel, slows
   the pre-existing ~108 s ONNX trace to ~180 s (total ~185 s). A `singleFork`/serial
   pool configuration for the two ONNX-heavy files is the obvious follow-up; it was not
   changed tonight because it affects every test file.

---

## 9. Build and test results

| Command (from `D:/Singvox/Singvox/web`) | Result |
|---|---|
| `npx tsc -b` | exit 0 |
| `npm run build` | exit 0 — `dist/assets/index-C5qcbcrO.js` 1 482.68 kB (was 1 477 kB), CSS unchanged |
| `npx vitest run` | exit 0 — **29 files, 164 tests passed, 0 failed** (was 27 files / 154 tests before this pass) |
| Browser, dev server `127.0.0.1:5177`, `#diagnostics`, live camera | delegate `GPU/GPU/GPU`, buffer 8/s, window `125 ± 0 ms`, no NaN/Inf |
| Browser, `vite preview` `localhost:4179`, `#diagnostics`, live camera | ONNX initialises in-page, 79 logits, live commits, avatar refuses uncovered signs |
| Routes `#welcome`, `#live`, `#avatar`, `#vision`, `#join` | all render; `#join` waiting-list form present and untouched |

Pre-existing failures: none. Two test-harness notes, both recorded above rather than
hidden: the ~108 s ONNX trace now declares an explicit 300 s timeout (no assertion
changed), and the recorded-clip replay is truncated to the first 12 s of each clip to
keep the default suite affordable.

## 10. What is measured vs assumed

- Measured: every latency, rate, detection count, landmark-agreement figure, cold-start
  figure, window duration/cadence and recognition outcome in this document — from the
  benchmark harness, the profiler, the replay tests and live browser sessions (dev
  server and production preview, real camera).
- Arithmetic on measured values (labelled as such): the before/after wall-clock window
  span in §5, which multiplies the measured number of buffer frames by the measured
  observation interval of the *previous* code path (that code path no longer exists,
  so it cannot be re-measured directly).
- Not separately instrumented: the time from an *accepted* prediction to visible text
  and avatar response. The commit path itself was not changed and is synchronous
  (`setTranscript` + `playSignByLabel` inside the inference callback), and its
  neighbouring stages are measured — `stabilizerProcess` median 0.0 ms / p95 0.1 ms and
  `overlayRender` median 0.3–0.85 ms / p95 0.7–3.4 ms — but no timer wraps the commit
  itself, so no end-to-end commit→pixels figure is claimed. Adding one is a small
  follow-up in `latencyProfiler.ts`.
- Not measured: live-signer accuracy for any sign, and the recognition effect of the
  ORT worker (only its throughput effect was measured).
