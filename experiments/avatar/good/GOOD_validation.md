# GOOD (ASL_002) — Candidate Validation

Status: **CANDIDATE — NOT expert-verified. Do NOT use as ground truth.**

## 1. Source verification (Step 1) — PASS
- Frozen vocab: `Singvox/docs/ai-ml/ASL_100_VOCABULARY_FROZEN.md` → ASL_002 GOOD (ID/label unchanged).
- Spec: `Singvox/docs/ai-ml/ASL_100_SIGN_SPECIFICATIONS_BATCH_01.md` SV-ASL-002 (flat/open dominant hand, onset near lips/lower face, moves away/downward, one-handed common form; confusion pair THANK-YOU).
- Dataset reference: `8390777557102604-GOOD.mp4` (signer P22) listed in `Singvox/docs/ai-ml/ASL_CITIZEN_TRAINING_DATA_AUDIT.md:214` as "Verified on disk & feature cache". Video bytes were NOT opened in this phase; no frames were retargeted from it.
- Mapping: `ai/sign-recognition/config/asl100_asl_citizen_mapping.json` (GOOD exact) + `class_index_mapping.json` index 1 — untouched.
- Step 2/3 compliance: 366-dim vectors NOT fed into joints; production GLB, controller, vocab, SPOTER pipeline, checkpoints untouched.

## 2. Static checks performed (no shell/Blender available in this env)
- [x] `ASL_GOOD.clip.json` read back and structurally reviewed: name `ASL_GOOD` matches `ASL_<LABEL>` convention consumed by `AvatarController.playSignByLabel()` (`avatar/controller/AvatarController.ts:255-258`); bones use `mixamorig4:<Bone>` matching `tools/author_hello.py`; all 6 arm/hand tracks span f0→f40 with neutral in/out; euler values are finite radians.
- [x] `author_good_blender.py` mirrors `author_hello.py` structure (read .blend copy → pose mode → new `ASL_GOOD` action → keyframes → save to experiments path only).
- [x] New-file isolation: all 4 files under `Singvox/experiments/avatar/good/`; `git status` check unavailable (terminal spawn failed), but no edit tool touched any file outside that directory this phase.
- [ ] NOT run: Blender bake, GLB export, `glbPlayback.test.ts`-style load test, AvatarStudio live playback, screenshots. Terminal (`run_terminal_command`) fails in this environment (`uv_spawn bash.exe ENOENT`), so nothing could be executed.

## 3. Playback test (to run on your machine)
1. `blender --background --python Singvox/experiments/avatar/good/author_good_blender.py`
2. Export a COPY of the .blend to e.g. `SignVox_GOOD_Candidate.glb` (see `tools/export_glb.py`; do NOT overwrite `web/public/avatar/SignVox_Female_Competition_Prototype.glb`).
3. Serve `web/`, load the candidate GLB in the AvatarStudio diagnostic route, call `playSignByLabel('GOOD')` → expect clip `ASL_GOOD` to play once then crossfade to `ASL_NEUTRAL` (`AvatarController.ts:186-204`).
4. Inspect: flat right hand, onset at lips, downward-away stroke, no torso clipping, clean neutral return.

## 4. What worked / failed
- Worked: spec + reference + mapping all exist for GOOD; authored neutral-safe keyframes + flat-hand pose + Blender script without touching production.
- Failed/blocked: live bake + playback evidence could not be produced here (no shell/Blender); wrist/arm angles are estimates awaiting visual check.
- Suitability: suitable for visual review ONLY after the bake+playback steps above; NOT suitable for training labels or signer verification claims.

## 5. Handshape / wrist / path / location (authored intent)
- Handshape: flat/open right hand (all finger joints 0.0).
- Wrist: f10 `(0.4,-0.4,-0.4)` → f20 `(0.1,-0.15,-0.15)` (palm rotating from face-inward to outward-down).
- Path: lips/lower-face onset → away/down-forward stroke.
- Location: dominant hand only; left arm pinned neutral; torso intersection risk low but UNCONFIRMED visually.
