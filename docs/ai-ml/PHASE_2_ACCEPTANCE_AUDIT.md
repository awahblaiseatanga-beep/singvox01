# SignVox Phase 2 — Evidence-Based Acceptance Audit

*Date: October 9, 2026*  
*Scope: 3-Sign Pilot (`HELLO`, `YES`, `NO`) Prototype & Runtime Integration Audit*

---

## Executive Summary & Decision

### **DECISION: CONDITIONAL NO-GO FOR LIVE CAMERA DEMO / GO FOR TEST-SUITE DEMO**

- **Live Camera Web Demo:** **NO-GO**  
  *Reason:* The web browser application (`web/src/App.tsx`) currently loads the 79-class baseline ONNX model (`spoter_v2_model.onnx`) and routes recognized sign predictions to a text transcript and Web Speech API audio output. It is **not genuinely connected** to `spoter_pilot_checkpoint.pt`, nor does it trigger `AvatarController.playSignByLabel()`.
- **Automated Pipeline & Avatar Prototype:** **GO**  
  *Reason:* The 3-class SPOTER pilot PyTorch checkpoint (`spoter_pilot_checkpoint.pt`) is fully verified (94.29% held-out accuracy), and its prediction labels cleanly route through `AvatarController.playSignByLabel()` to play authentic ASL NLA animation tracks (`ASL_HELLO`, `ASL_YES`, `ASL_NO`) and return to `ASL_NEUTRAL` without redundant restarts.

---

## Check 1 — Live Recognition Pipeline Audit

### Traced Pipeline Path
1. **Camera Frame Acquisition:** `web/src/App.tsx` captures live video frames via `navigator.mediaDevices.getUserMedia()`.
2. **Landmark Extraction:** `BrowserLandmarkerPipeline` (`web/src/lib/mediapipe.ts`) runs MediaPipe Pose, Hands, and Face landmarkers.
3. **Feature Assembly & Normalization:** `assembleCanonicalFrame()` (`web/src/lib/featureVector.ts`) constructs 366-D vectors, normalized via `applyV2Normalization()` (`web/src/lib/normalize.ts`).
4. **Buffer & Inference Session:** `App.tsx` accumulates 60 normalized frames and executes `SpoterInferenceSession.predict()`.
5. **Loaded Model Asset:** `App.tsx` initializes `SpoterInferenceSession.create('/spoter_v2_model.onnx')` — loading the **79-class baseline ONNX model** (`spoter_v2_model.onnx`).
6. **Output Routing:** `TemporalStabilizer` (`web/src/lib/temporalStabilizer.ts`) processes top-1 predictions. Committed signs update `transcript` state and trigger Web Speech API `speakText()`.

### Crucial Findings
- **Disconnected Model Checkpoint:** `spoter_pilot_checkpoint.pt` (the PyTorch 3-class pilot model) has **not been exported to ONNX format** (`spoter_pilot.onnx`) and is **not loaded by `App.tsx`**.
- **Disconnected Avatar Routing:** `App.tsx` does **not instantiate `AvatarController`** and does **not call `playSignByLabel()`**. Live camera input drives text and speech, while the avatar component lives in an isolated diagnostic harness (`AvatarDiagnostic.tsx` at `#avatar-diagnostic`).

---

## Check 2 — Animation Track & Visual Evidence Audit

### Audit of NLA Animation Tracks
File: `web/public/avatar/SignVox_Female_Competition_Prototype.glb` (**47.34 MB**)

| Sign | GLB NLA Track | Linguistic Visual Analysis | Status |
|------|---------------|----------------------------|--------|
| `HELLO` | `ASL_HELLO` | Right hand raised to temple/forehead, moving outward in salute. | ✅ Visually Plausible |
| `YES` | `ASL_YES` | **S-handshape** (fist with thumb crossed across fingers), right arm raised in front of chest, wrist nodding flexed down/up 2× (frames 14 & 26), synced with head nod. | ✅ Visually Plausible Manual Component |
| `NO` | `ASL_NO` | **U/H-handshape** (index & middle extended straight, ring/pinky curled, thumb extended), index & middle snapping down to thumb tip 2× (frames 14 & 26), synced with head shake. | ✅ Visually Plausible Manual Component |

### Playback Behavior Verification
- **Deduplication:** `AvatarController.playSignByLabel()` checks `if (this.animationMode === targetMode && currentAction.isRunning()) return;` — preventing redundant animation restarts on consecutive identical predictions.
- **Neutral Recovery:** Upon animation clip completion, `THREE.AnimationMixer` `finished` listener fires and crossfades avatar mode back to `ASL_NEUTRAL`.

---

## Check 3 — Fingertip and IK Regression Audit

### Browser Diagnostic Behavior (`#avatar-diagnostic`)
1. **Master IK Disabled (`ikEnabled = false`):**
   - Finger curl sliders (`indexCurl`, `middleCurl`, etc.) manipulate local Euler rotations on finger bones directly.
   - Hand pose updates immediately with zero IK interference or joint fighting.
2. **Master IK Enabled (`ikEnabled = true`):**
   - Target selections (`forehead`, `belly`, `chest`) execute 2-bone analytical IK solver (`ArmIKController.ts`).
   - Forehead anchor reach: Target world position `[0.08, 1.43, 0.03]`. As traced in `reproduce_trace.test.ts`, elbow pole vector projection reaches joint limits causing minor wrist contact offset (~0.05m), but stays stable without infinite quaternion spinning or frame-to-frame accumulation.
   - Target switching between anchors: Hand smoothly transitions between targets; visual debug spheres (`S`, `E`, `W`, `Tip`) accurately track arm joints.

---

## Check 4 — Model Evaluation Integrity

### Discrepancy Reconciliation
- **3-Sample Smoke Test (`tools/smoke_test_pilot.py`):** **100.0% (3/3)**  
  *Scope:* Tested 1 representative `.npy` sequence file per class (`HELLO`, `YES`, `NO`).
- **Full Held-Out Test Evaluation (`train_pilot_spoter.py`):** **94.29% (33/35)**  
  *Scope:* Evaluated all 35 samples in the held-out test split (`HELLO`: 14/14, `YES`: 10/10, `NO`: 9/11).

### Integrity Confirmations
- **Zero Data Leakage:** Signer IDs across train (45), val (12), and test (35) splits are completely mutually exclusive.
- **Zero Test Tuning:** Checkpoint `spoter_pilot_checkpoint.pt` was selected at Epoch 7 based strictly on 100% validation set accuracy. The held-out test set was evaluated once post-training without hyperparameter or threshold tuning.

---

## Audit Matrix

| Category | Claim | Audit Status | Evidence |
|----------|-------|--------------|----------|
| Model | 3-class SPOTER accuracy 94.29% | **CONFIRMED** | `spoter_pilot_config.json`, test split eval |
| Model | Baseline 79-class model untouched | **CONFIRMED** | Baseline checkpoint hash/size (187.78 MB) |
| Animations | Authentic YES/NO manual hand components | **CONFIRMED** | GLB tracks `ASL_YES`, `ASL_NO`, Blender keyframes |
| Animations | Deduplicated restart & neutral recovery | **CONFIRMED** | `AvatarController.ts` & `test_end_to_end_pilot.py` |
| Web Runtime | Live camera connected to pilot PyTorch model | **UNVERIFIED / FALSE** | `App.tsx` loads baseline `/spoter_v2_model.onnx` |
| Web Runtime | Live camera connected to Avatar playback | **UNVERIFIED / FALSE** | `App.tsx` has no `AvatarController` reference |

---

## Required Action Items Before Full Live Camera Acceptance

1. **Export Pilot Model to ONNX:** Convert `spoter_pilot_checkpoint.pt` to `spoter_pilot.onnx` and `pilot_class_mapping.json`.
2. **Wire Avatar Controller in App.tsx:** Instantiate `AvatarController` inside main application view and connect `TemporalStabilizer` committed signs to `avatarController.playSignByLabel()`.
