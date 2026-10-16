# SignVox — 79-Class Recognition Recovery Audit (2026-10-15)

Scope: investigate and restore the existing 79-class SPOTER V2 baseline recognition path
in the browser app at `Singvox/web`, while preserving the working 3-class HELLO/YES/NO
pilot as the fallback and production default.

Everything below is measured. No model was retrained, re-exported or replaced; no
vocabulary, feature contract, normalization scalar, avatar controller or GLB was changed.

## 1. Verdict

- **The 79-class baseline is not broken.** It loads, returns 79 logits, and recognises
  its own signs: 86.0% top-1 on the held-out `val` split (whole clips), 80.4% on the
  recorded test split (`docs/ai-ml/SPOTER_V2_FINAL_TEST_RESULTS.json`).
- **The earlier "baseline produces idle output" conclusion does not survive
  reproduction.** It came from evaluating hardware paths the model never trained on:
  (a) a harness that fed feature files **without the V2 group-normalization step**, and
  (b) 60-frame tensors whose missing content was **zero-filled**.
- **Three real runtime defects were found and are the actual explanation** for the live
  behaviour (section 4): unscaled-input feeding in a diagnostic harness, zero-filled
  "no landmarks detected" frames driving confident attractor predictions, and a commit
  path with no input-validity or animation-coverage honesty.
- **The baseline has 3 of 79 avatar animations** (HELLO, YES, NO). It is therefore ready
  for *controlled live testing*, not for a public multi-sign demonstration.

## 2. Artifacts identified

| Artifact | Path | Role | Verified |
|---|---|---|---|
| Baseline ONNX | `ai/sign-recognition/checkpoints/spoter_v2_model.onnx` (119 KB) | 79-class graph | input `[1,60,366]`, output `[1,79]` |
| Baseline weights | `ai/sign-recognition/checkpoints/spoter_v2_model.onnx.data` (179 MB) | external data | loaded by ORT Web WASM in the browser |
| Baseline served copy | `web/public/spoter_v2_model.onnx` + `.data` | what the app fetches | byte-identical naming to the checkpoint export |
| Baseline checkpoint | `ai/sign-recognition/checkpoints/spoter_v2_groupnorm_best_val_acc.pt` | PyTorch source of truth | loads into `Spoter(num_classes=79)` |
| Pilot ONNX | `web/public/spoter_pilot.onnx` + `.data` | 3-class production default | input `[batch,seq,366]`, output `[1,3]` |
| Pilot checkpoint | `ai/sign-recognition/models/spoter_pilot_checkpoint.pt` | pilot source | — |
| Class index mapping (79) | `ai/sign-recognition/data/class_index_mapping.json` | training-time index → name | matched to `ASL_VOCAB` exactly (test) |
| Class index mapping (3) | `ai/sign-recognition/data/pilot_class_mapping.json` | pilot index → name | matched to `PILOT_VOCAB` exactly (test) |
| V2 scalars | `ai/sign-recognition/models/spoter_v2_groupnorm_scalars.json` | group scaling | identical to `web/src/lib/contracts.ts` `V2_SCALARS` |
| Runtime loader | `web/src/lib/inference.ts` | ORT Web session + softmax | now guards output size |
| Model/class-map binding | `web/src/lib/modelRegistry.ts` (new) | one spec per model | enforced at load and per prediction |
| Frozen dataset features | `ai/sign-recognition/data/dataset_extracted/*.npy` (3 439 files) | pre-scaling extractor output | `(T, 366)`, 10 fps |
| Production avatar | `web/public/avatar/SignVox_Female_Competition_Prototype.glb` | animations | exactly `ASL_HELLO`, `ASL_NO`, `ASL_YES`, `mixamo.com` |

Class order is **not** alphabetical: index 0 = HELLO, 9 = YES, 10 = NO, 78 = COLD, matching
`class_index_mapping.json` (`ASL_001 … ASL_100`, gaps included).

## 3. Pipeline audit (browser vs training)

Traced flow: camera → MediaPipe Tasks (pose/hands/face) → `assembleCanonicalFrame` →
`applyV2Normalization` → 60-frame `SequenceBuffer` → ONNX → `TemporalStabilizer` →
transcript + avatar dispatch.

| Stage | Training side | Browser side | Verdict |
|---|---|---|---|
| Feature order | `[lh 0:63, rh 63:126, pose 126:291 (33×5), face 291:366 (25×3)]` (`extract_dataset.py`, `train_spoter_v2.py`) | identical (`contracts.ts`) | matches |
| Shoulder centering | pose 11/12 midpoint + 3-D distance (`normalize_landmarks`) | identical (`shoulderCenter`) | matches |
| Group scaling | `/left_hand .3887, /right_hand .3666, /pose_xyz 1.8127, /face .3139` | identical (`applyV2Normalization`) | matches |
| Sampling | 10 fps (`extract_frames_10fps`) | one buffered frame per 125 ms ≈ 8 fps | close; window spans 7.5 s vs ≤6.1 s of training clips |
| Sequence input | whole clip, variable length, padding **masked** | fixed 60 frames, **no mask possible** | export dropped the mask input |
| Handedness | Holistic `left_hand_landmarks` → LH; measured pose 11 x-offset +0.95 → anatomical, LH centroid +0.27 / RH −0.31 | Tasks label flipped for the unmirrored frame; LH ← anatomically left hand | **matches training; not a defect** |
| Missing landmarks | rare (fallback sweep logged ~0 recoveries) | zero-filled frame is still pushed | **defect — see 4.2** |
| ONNX provider | CPUExecutionProvider | ORT Web WASM | fine |

## 4. Root cause

### 4.1 PyTorch ↔ ONNX parity is exact — the export is not the problem

`experiments/baseline-79-audit/eval_baseline_79.py` on all 306 `val` + 1 199 `train`
samples: argmax agreement **100.0%**, max absolute logit difference **7.6e-06** (val) /
**8.6e-06** (train). The graph reproduces the checkpoint.

### 4.2 A zero-landmark window is out of distribution and does not return "nothing"

The baseline always answers. Fed windows that a live camera produces whenever landmarks
are missing (the app pushes zero-filled frames), it returns confident attractor classes:

| Input window (60 frames) | Top prediction | Confidence |
|---|---|---|
| all-zero (no landmarks detected) | **SICK** | **0.856** |
| real pose/face, hand blocks zeroed | **YESTERDAY** | 0.692 |
| real HELLO clip padded with 50 zero frames | DAY | 0.321 |
| same HELLO clip, landmarks present | HELLO | 0.416 |

`BASELINE_STABILIZER_CONFIG` (`minimumConfidence 0.05`, `minimumCommitEvidence 0.25`)
happily commits 0.86 confidence, so idle camera time produced spurious `SICK`/`YESTERDAY`/
`ME` commits, and the avatar silently fell back to neutral because those labels have no
clip. That is what "the baseline outputs idle" looks like from the outside.

### 4.3 A previous diagnostic harness fed the model un-normalized features

`web/src/tests/baseline_threshold_eval.test.ts` read `dataset_extracted` `.npy` files
(extractor output, **before** the group scalars) and passed them straight to `predict()`.
It reported `Base 0.65 : Commits=[ME] TopConf=0.000` — the origin of the "HELLO → ME,
0% accuracy, ~0.34 confidence ceiling" claims in
`PHASE_3_BASELINE_RECOGNITION_AUDIT.md` / `PHASE_3_BASELINE_THRESHOLD_VALIDATION.md`.
Measured on the same clip:

| Input | Top prediction |
|---|---|
| unscaled (old harness) | YESTERDAY 0.508, HELLO 0.185 |
| group-scaled (training + browser) | HELLO 0.416, YESTERDAY 0.395 |

With the normalization step restored, the app's own runtime path in Node now reports
`Base 0.65 : Commits=[HELLO, ME] TopConf=0.977` (HELLO), `Commits=[ME, YES] TopConf=0.988`
(YES).

### 4.4 Fair framing shows the baseline working

`experiments/baseline-79-audit/simulate_live.py` replays the actual browser pattern —
a 60-frame FIFO advanced one frame at a time at 10 fps through the app's stabilizer, with
a neutral hold before and after each clip:

- HELLO: 4/4 val clips commit the correct sign; YES 4/5; NO 2/3 (12 clips, max confidence 0.998).
- Full sweep, 237 val clips across all 79 classes: **205 correct commits (86.5%)**,
  32 wrong, 0 no-commit; 56 classes fully correct, 21 partial, 2 (HAPPY, HUNGRY) incorrect
  on every sampled clip.

By contrast, forcing the same clips into a fixed 60-frame tensor with zero padding (the
old harness framing) drops whole-split top-1 from 85.95% to 52.94%. Resampling the same
clip content across the 60 frames restores 82.68%, confirming the loss is the *empty part*
of the window, not the model.

### 4.5 What was ruled out

- **Class mapping**: `ASL_VOCAB` equals `class_index_mapping.json` for all 79 indices
  (asserted by test), and the model predicts the correct label for correctly framed input.
- **Left/right inversion**: measured cost of swapping the hand blocks is 52.94% → 4.58%,
  so handedness matters — but the training data is anatomically consistent (pose landmark
  11 always on the image-right, LH centroid +0.27 / RH −0.31) and the browser's
  label flip for unmirrored frames produces the same anatomy. No change made.
- **Threshold dilution** ("79-way softmax cannot reach 0.65"): real commits reach
  0.98–1.00 confidence, so the ceilings in the earlier reports were artifacts of 4.2/4.3.
- **Predictions are deterministic**: the repeatability test reuses one tensor and matches.

## 5. 79-class recognition and animation coverage

Generated by `experiments/baseline-79-audit/simulate_live.py` (`--limit 3`, val split) —
see `experiments/baseline-79-audit/live_simulation_results_79.json` and
`coverage_matrix.md`. Columns: measured live-path commits on up to 3 held-out clips,
and whether the production GLB can animate the sign.

| # | Sign | Held-out clips replayed | Correct commits | Wrong commits | Avatar clip | Observed wrong commits |
|---:|---|---:|---:|---:|---|---|
| 0 | HELLO | 3 | 3 | 0 | yes | - |
| 1 | GOOD | 3 | 3 | 0 | no | - |
| 2 | BAD | 3 | 3 | 0 | no | - |
| 3 | PLEASE | 3 | 3 | 0 | no | - |
| 4 | SORRY | 3 | 2 | 1 | no | ME x2, SICK x1, YESTERDAY x1 |
| 5 | HELP | 3 | 2 | 1 | no | SICK x1, YESTERDAY x1, ME x1 |
| 6 | STOP | 3 | 3 | 0 | no | - |
| 7 | WAIT | 3 | 2 | 1 | no | SICK x1, YESTERDAY x1, ME x1 |
| 8 | UNDERSTAND | 3 | 3 | 0 | no | - |
| 9 | YES | 3 | 2 | 1 | yes | SICK x1, YESTERDAY x1, ME x1 |
| 10 | NO | 3 | 2 | 1 | yes | SICK x1, YESTERDAY x1, ME x1 |
| 11 | AGAIN | 3 | 2 | 1 | no | SICK x1, YESTERDAY x1, ME x1 |
| 12 | SLOW | 3 | 3 | 0 | no | - |
| 13 | NAME | 3 | 2 | 1 | no | SICK x1, YESTERDAY x1, ME x1 |
| 14 | ME | 3 | 3 | 0 | no | - |
| 15 | YOU | 3 | 3 | 0 | no | - |
| 16 | FAMILY | 3 | 3 | 0 | no | - |
| 17 | FRIEND | 3 | 3 | 0 | no | - |
| 18 | MOTHER | 3 | 3 | 0 | no | - |
| 19 | FATHER | 3 | 3 | 0 | no | - |
| 20 | BROTHER | 3 | 3 | 0 | no | - |
| 21 | SISTER | 3 | 3 | 0 | no | - |
| 22 | CHILD | 3 | 3 | 0 | no | - |
| 23 | TEACHER | 3 | 3 | 0 | no | - |
| 24 | GO | 3 | 3 | 0 | no | - |
| 25 | COME | 3 | 3 | 0 | no | - |
| 26 | GIVE | 3 | 2 | 1 | no | SICK x1, YESTERDAY x1, COME x1 |
| 27 | TAKE | 3 | 1 | 2 | no | SICK x2, YESTERDAY x2, ME x2 |
| 28 | NEED | 3 | 2 | 1 | no | SICK x1, YESTERDAY x1, ME x1 |
| 29 | HAVE | 3 | 3 | 0 | no | - |
| 30 | KNOW | 3 | 2 | 1 | no | SICK x1, YESTERDAY x1, HOME x1 |
| 31 | LIKE | 3 | 2 | 1 | no | SICK x1, YESTERDAY x1, ME x1 |
| 32 | SEE | 3 | 3 | 0 | no | - |
| 33 | THINK | 3 | 3 | 0 | no | - |
| 34 | LEARN | 3 | 1 | 2 | no | SICK x3, YESTERDAY x2, ME x2 |
| 35 | STUDY | 3 | 3 | 0 | no | - |
| 36 | SCHOOL | 3 | 2 | 1 | no | SICK x1, YESTERDAY x1, ME x1 |
| 37 | WORK | 3 | 3 | 0 | no | - |
| 38 | HOME | 3 | 3 | 0 | no | - |
| 39 | CHURCH | 3 | 3 | 0 | no | - |
| 40 | BATHROOM | 3 | 3 | 0 | no | - |
| 41 | HERE | 3 | 3 | 0 | no | - |
| 42 | THERE | 3 | 3 | 0 | no | - |
| 43 | IN | 3 | 1 | 2 | no | SICK x2, YESTERDAY x2, ME x2 |
| 44 | OUT | 3 | 3 | 0 | no | - |
| 45 | TODAY | 3 | 3 | 0 | no | - |
| 46 | YESTERDAY | 3 | 3 | 0 | no | - |
| 47 | TOMORROW | 3 | 3 | 0 | no | - |
| 48 | MORNING | 3 | 2 | 1 | no | SICK x1, YESTERDAY x1, ME x1 |
| 49 | DAY | 3 | 3 | 0 | no | - |
| 50 | WHO | 3 | 1 | 2 | no | SICK x2, YESTERDAY x2, YOU x2 |
| 51 | WHERE | 3 | 3 | 0 | no | - |
| 52 | WHEN | 3 | 3 | 0 | no | - |
| 53 | WHY | 3 | 3 | 0 | no | - |
| 54 | WATER | 3 | 3 | 0 | no | - |
| 55 | HUNGRY | 3 | 0 | 3 | no | ME x5, SICK x3, YESTERDAY x3 |
| 56 | SLEEP | 3 | 3 | 0 | no | - |
| 57 | PAIN | 3 | 3 | 0 | no | - |
| 58 | SICK | 3 | 3 | 0 | no | - |
| 59 | DANGER | 3 | 2 | 1 | no | SICK x1, YESTERDAY x1, ME x1 |
| 60 | FIRE | 3 | 3 | 0 | no | - |
| 61 | COMPUTER | 3 | 3 | 0 | no | - |
| 62 | SIGN | 3 | 3 | 0 | no | - |
| 63 | LANGUAGE | 3 | 3 | 0 | no | - |
| 64 | HEARING | 3 | 1 | 2 | no | ME x4, SICK x2, YESTERDAY x2 |
| 65 | MEET | 3 | 2 | 1 | no | SICK x1, YESTERDAY x1, ME x1 |
| 66 | MORE | 3 | 3 | 0 | no | - |
| 67 | FINISH | 3 | 3 | 0 | no | - |
| 68 | LOVE | 3 | 3 | 0 | no | - |
| 69 | HAPPY | 3 | 0 | 3 | no | SICK x3, YESTERDAY x3, ME x3 |
| 70 | SAD | 3 | 3 | 0 | no | - |
| 71 | ANGRY | 3 | 3 | 0 | no | - |
| 72 | AFRAID | 3 | 3 | 0 | no | - |
| 73 | FEEL | 3 | 3 | 0 | no | - |
| 74 | NICE | 3 | 3 | 0 | no | - |
| 75 | BIG | 3 | 3 | 0 | no | - |
| 76 | SMALL | 3 | 3 | 0 | no | - |
| 77 | HOT | 3 | 3 | 0 | no | - |
| 78 | COLD | 3 | 2 | 1 | no | SICK x1, YESTERDAY x1, ME x1 |

Totals: 237 clips replayed, 205 correct commits, 32 wrong commits, 0 with no commit; 56/79 classes fully correct, 21/79 partial, 2/79 (HAPPY, HUNGRY) incorrect on every sampled clip.
3 of 79 classes (HELLO, YES, NO) have an avatar animation; the other 76 are text only.

State definitions used above:

| State | Meaning |
|---|---|
| Recognition tested | replay of the browser path over the held-out `val` split, with the correct normalization |
| Avatar clip | clip name present in `SignVox_Female_Competition_Prototype.glb` (`ASL_<LABEL>`) |
| Live signer verified | **not established for any class** — no camera/signer test was run in this environment |

## 6. Changes made

| File | Why |
|---|---|
| `web/src/lib/modelRegistry.ts` (new) | One spec per model (artifact URL, own vocab, expected class count, own stabilizer thresholds, avatar coverage). Module load fails if a vocab is not a dense 0..n-1 range with the declared size. Exports `DEFAULT_MODEL_ID = 'baseline'`: the shipped recognition scope is the 79-class SPOTER V2 model, so the scope shown in the UI and the running graph cannot disagree. |
| `web/src/lib/inference.ts` | `assertModelOutputSize` on every prediction — a 3-class map can never label a 79-class model or vice versa. `wasmPaths` is now only overridden in a browser, so the ORT Web loader is not hijacked under Node tests. Exposes `modelUrl`. |
| `web/src/lib/recognitionGate.ts` (new) | Pure input-validity gate: refuses a window whose landmark coverage is below the measured valid regime (hands ≥25%, pose ≥25% of buffered frames). |
| `web/src/lib/sequenceBuffer.ts` | Adds `anyHandPercent` (either hand present) to `SequenceQuality`, reusing the existing per-frame presence metadata. |
| `web/src/engine/useSignVoxEngine.ts` | Model lookup/URLs/vocab/thresholds now come from the registry; the gate runs before inference and clears pending stabilizer evidence when it rejects; commits record whether the loaded GLB can animate the sign; exposes `activeModelSpec`, `avatarClipLabels`, `avatarCanPlay`, `recognitionGate`. Active model now initialises from `DEFAULT_MODEL_ID` (79-class baseline) with the pilot selectable as the fallback. |
| `web/src/lib/signToText.ts` | `TranscriptItem.avatarClipAvailable` — recognition and animation stay separate. |
| `web/src/pages/LiveTranslationPage.tsx` | Replaces the three-sign chip with the active model's real scope ("Recognised signs: 79 ASL classes"), names the model, and states the recognition-vs-animation gap: "Recognises 79 signs; the avatar animates 3 of them (HELLO · YES · NO). Other recognised signs are shown as text only." Also states "Recognised as text only…" for uncovered signs, tags transcript entries `text only`, and explains a gated window ("Hands not visible — recognition is paused…"). |
| `web/src/components/DiagnosticDashboard.tsx` | Internal header reports active model, scope, the real avatar clip list and the model's known limitations; the model selector marks the 79-class baseline as the default and the pilot as the fallback. |
| `web/src/App.tsx`, `web/src/pages/WelcomePage.tsx`, `web/src/pages/AboutPage.tsx` | Same scope correction in the public copy: footer now reads "79 ASL-based signs recognised · avatar animates HELLO · YES · NO", and the "three-sign pilot" phrasing is replaced by the 79-sign scope with the 3-animated-signs caveat kept explicit. Routes, waiting-list behaviour and page structure unchanged. |
| `web/src/tests/modelRegistry.test.ts` (new) | Vocab ↔ training mapping equality for both models, model/class-map mismatch refusal, GLB clip inventory read from the shipped `.glb`. |
| `web/src/tests/recognitionGate.test.ts` (new) | Gate behaviour incl. the measured all-zero and no-shoulders regimes, wired through a real `SequenceBuffer`. |
| `web/src/tests/baseline_idle_diagnostic.test.ts` | The old file asserted that idle noise *should* commit and failed; it now asserts the measured correct behaviour (no idle commits) plus that a genuinely held sign still commits and a one-frame spike does not. |
| `web/src/tests/baseline_threshold_eval.test.ts` | Applies `applyV2Normalization` like the app does (the step the old harness omitted), uses a filesystem path instead of a `file://` URI for the Node ONNX loader, and asserts the logit count. |
| `web/src/tests/consistency_diagnosis.test.ts` | Fixture updated for the new `anyHandPercent` field. |
| `experiments/baseline-79-audit/*.py`, `*.json` | Reproducible measurement scripts and their raw results. |
| `docs/RECOGNITION_79_CLASS_RECOVERY_AUDIT.md` (this file) | Audit deliverable. |

Not changed: model weights, ONNX exports, `ASL_VOCAB`/`PILOT_VOCAB` contents, 366-D contract,
`V2_SCALARS`, `AvatarController`, production GLB, `App.tsx` routes, waiting-list form behaviour.

## 7. Commands and results

All commands run from `D:/Singvox/Singvox`.

| Command | Result |
|---|---|
| `cd web && npx tsc -b` | exit 0 |
| `cd web && npm run build` | exit 0, `dist/assets/index-DFEqu-w7.js` (1 477 kB) |
| `cd web && npx vitest run --reporter=json` | exit 0 — **27 files, 154 tests passed, 0 failed** (was 2 failed / 138 passed before this work) |
| `.venv_pilot/Scripts/python.exe experiments/baseline-79-audit/eval_baseline_79.py` | ONNX `[1,60,366]`→`[1,79]`; val 306: full-clip top-1 85.95%, 60-frame zero-pad 52.94%, argmax agreement 100%, max Δlogit 7.6e-06 |
| `... analyze_windowing.py` | val clip lengths 12–61 (median 23); masked 85.95%, unmasked 85.95%, zero-pad window 52.94%, resampled 82.68% |
| `... simulate_live.py --pilot --classes HELLO,YES,NO` | HELLO 4/4, YES 4/5, NO 2/3 correct commits |
| `... simulate_live.py --limit 3` | 237 clips: 205 correct / 32 wrong / 0 none |
| `... handedness_test.py` | identity 52.94%, hand swap 4.58%, full mirror 7.52% |
| Browser (dev server `127.0.0.1:5177`, `#diagnostics`) | pilot selected: "ONNX Runtime: PASS · Output: 3 logits"; **default (79-class baseline, no selection needed): "Output: 79 logits"**, no NaN/Inf, provider WASM |
| Browser, `#live` | chips read "Recognised signs: 79 ASL classes" + "79-Class Baseline (SPOTER V2)", with "Recognises 79 signs; the avatar animates 3 of them (HELLO · YES · NO). Other recognised signs are shown as text only." |

Pre-existing test failures: **both now pass**, and neither was silenced — the idle test's
expectation was inverted to match measurement, the trace test's input and path bugs were fixed.

## 8. Recommendation

1. **Keep the 3-class pilot as the production default and as the public claim.** Unchanged.
2. **The 79-class baseline is ready for controlled live testing** (internal `#diagnostics`
   screen, one signer, one sign at a time), not for a public demo: only 3 of its 79 classes
   have avatar animations, and its live accuracy on a *new* signer is unmeasured.
3. **Test in this order**: HELLO, YES, NO (all have clips and all committed correctly in
   replay), then the 56 classes that were fully correct in replay (text-only output),
   then NO/HAPPY/HUNGRY/WHO/IN/LEARN/TAKE as known weaknesses.
4. **Before any public multi-sign claim**, the model needs: an idle/rejection path
   (an `[IDLE]` class or a calibrated rejection head), retraining on augmented
   "hands absent / at rest" frames so zero-landmark windows stop producing SICK/YESTERDAY,
   and an animation library extension beyond 3 clips.
5. **Do not lower the baseline commit threshold further.** It is not the bottleneck;
   the measured bottlenecks are input validity and sign framing.

### 8.1 Shipped configuration (product decision, 2026-10-15)

The product owner asked for the UI to present the full 79-class SPOTER V2 scope rather
than the three-sign pilot. Implemented as **the 79-class baseline is now the default
model**, so the declared scope and the running graph agree, with these conditions kept
visible in the same screen:

- The Live page states the scope ("Recognised signs: 79 ASL classes"), names the model,
  and states the animation gap (3 of 79 signs animated).
- The 3-class pilot stays selectable as the fallback and keeps its own class map,
  output-size guard and thresholds.
- The public footer and the Vision/About pages no longer claim a three-sign scope, and
  still state that the model is experimental, not live-signer validated, not CSL.

This supersedes recommendation 1 above (which proposed keeping the pilot as the default).
Recommendation 4 is unchanged: a public multi-sign claim still needs the idle/rejection
path, the zero-landmark retraining and avatar animations beyond 3 clips.

## 9. Limitations and open items

- **No live signer or camera test was performed.** Every recognition number in this
  document is an offline replay of the browser pipeline over recorded `val` clips.
  Live recognition is *not* claimed as verified for any class.
- The gate thresholds (25% hands / 25% pose over the window) come from the measured
  degradation curve on recorded clips; they are permissive by design and should be
  re-tuned against a live session with the diagnostics screen.
- The window/vocabulary mismatch is not removable without retraining: the ONNX export has
  no attention-mask input, so the graph cannot express "attend only to these frames".
- `THREE.GLTFLoader: Couldn't load texture blob:` errors appear in the console from the
  existing avatar asset; they pre-date this work and do not affect clips or rig.
- The 79-class recognition replay used ≤3 clips per class; classes with a single wrong
  sample are marked partial, not "failing".
