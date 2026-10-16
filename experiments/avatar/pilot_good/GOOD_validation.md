# GOOD (ASL_002) — Candidate Validation

Status: **CANDIDATE — NOT expert-verified. Do NOT use as ground truth.**

## 1. Source verification — PASS
- Frozen vocab: `Singvox/docs/ai-ml/ASL_100_VOCABULARY_FROZEN.md:29` → ASL_002 GOOD (ID/label unchanged).
- Spec: `docs/ai-ml/ASL_100_SIGN_SPECIFICATIONS_BATCH_01.md` SV-ASL-002 (flat/open dominant hand,
  onset near lips/lower face, moves away/downward, one-handed common form; confusion pair THANK-YOU).
- Reference video: `8390777557102604-GOOD.mp4` (signer P22) per
  `docs/ai-ml/ASL_CITIZEN_TRAINING_DATA_AUDIT.md:214` — "Verified on disk & feature cache".
  Bytes not opened here; listed reference only.
- Mappings (`asl100_asl_citizen_mapping.json` GOOD exact, `class_index_mapping.json` index 1) untouched.
- 366-dim recognition vectors NOT fed into joints.

## 2. Files (all isolated under `Singvox/experiments/avatar/pilot_good/`)
- `GOOD_manifest.json` — sources, settings, file index
- `ASL_GOOD.clip.json` — `ASL_GOOD` keyframes, 30 fps, f0–f40, neutral in/out,
  `mixamorig4:<Bone>` XYZ-euler (matches `tools/author_hello.py`; strip `:` for `boneMap.ts`;
  `playSignByLabel('GOOD')` resolves it per `AvatarController.ts`)
- `author_good_blender.py` — bake script mirroring `author_hello.py`; saves only to the pilot dir
- `pilot_good_preview.html` — self-contained motion-check harness (FK + animation + checks table)

## 3. Motion checks (computed in-harness from the authored keyframes)
- hand→lips distance, torso clearance, neutral-return exactness, finite-angle sanity —
  computed live by the checks table in `pilot_good_preview.html` (open it to run them;
  no harness screenshot was captured — see §4).
- Segment lengths / shoulder / lips / torso box are ESTIMATES, not GLB measurements:
  numbers support the design but do not replace visual confirmation on the real avatar.

## 4. Playback evidence (baked 2026-10-15 — supercedes the earlier "no GLB yet" state)
- Candidate GLB: `SignVox_GOOD_Candidate.glb` (~49.8 MB, Khronos glTF Blender I/O v4.2.57),
  baked from the v2 HELLO-retarget (`author_good_blender.py`) via `export_good_glb.py`.
  Animations: `ASL_GOOD` (195 rotation channels/samplers, 1.33 s) + untouched
  `ASL_HELLO` / `ASL_NO` / `ASL_YES` / `mixamo.com`. Production GLB untouched.
- Numeric track check (parsed GLB BIN, 2026-10-15): `ASL_GOOD` sampler inputs sorted
  0.0–1.333 s, 41 keys (f0–f40 @ 30 fps); RightArm/RightForeArm/RightHand quaternions at
  f10 and f20 differ from f0 (real onset + stroke motion, not a static clip); f0==f40
  EXACTLY (maxdiff 0.0) → neutral return exact, clean crossfade to `ASL_NEUTRAL`.
- On-avatar harness `on_avatar_good_harness.html` (plain three.js, loads ONLY the candidate
  GLB, plays `ASL_GOOD` once then rests — same pattern as
  `AvatarController.playSignByLabel('GOOD')`), screenshotted 2026-10-15:
  onset hold (25%) shows the avatar's right hand raised toward the face; log confirms
  `GLB loaded OK — bones: 65`, `ASL_GOOD tracks: 195`, and a clean
  `playing ASL_GOOD (dur 1.33s) → finished → rest` cycle with no errors.
- Caveat: the mid-stroke hold (50%) rendered in bind/T-pose — the harness `rest()` falls
  back to the `mixamo.com` clip (production crossfades to `ASL_NEUTRAL` instead, so this
  is a harness artifact, not a clip defect), and the numeric data above confirms real
  stroke motion at f20. Mid-stroke VISUAL on the avatar is therefore not yet confirmed —
  flagged for the next review pass, not a blocker for candidate status.
- Earlier live diagnostic (2026-10-15, `http://127.0.0.1:5188/#avatar`, screenshotted):
  Avatar Studio loads, "Avatar ready"; "Available signs in this build: HELLO, NO, YES."
  — GOOD correctly ABSENT from the production build (sidecar not baked into any shipped
  GLB; `playSignByLabel('GOOD')` would fall back to `ASL_NEUTRAL`). Production untouched.
- Tests (2026-10-15, green): `web/src/tests/goodCandidate.test.ts` (candidate GLB carries
  `ASL_GOOD` rotation tracks on RightArm/RightForeArm/RightHand; `playSignByLabel('GOOD')`
  resolves to `clip:ASL_GOOD`) + `web/src/tests/glbPlayback.test.ts` — 4/4 pass.

## 5. What worked / failed
- Worked: v2 bake (HELLO-derived retarget, no guessed eulers) → candidate GLB with exact
  neutral return; on-avatar onset screenshot + clean play-through log; 4/4 tests green;
  production and HELLO/YES/NO untouched.
- Open: mid-stroke VISUAL confirmation on the avatar (numeric motion verified, screenshot
  pending — harness `pose=mid` hold needs a fix so autoplay/rest doesn't stomp the pose).
- Suitability: visual-review candidate ONLY; NOT expert-verified, NOT for training labels
  or verification claims.

## 6. Production preservation
No production asset modified: `web/public/avatar/*.glb`, `avatar/controller/*`, vocab,
and mappings untouched; HELLO/YES/NO intact. Outside the pilot dir, ONE file was added:
`Singvox/web/src/tests/goodCandidate.test.ts` (read-only assertions against the candidate
GLB + controller resolution — no production code changed). STOPPED — awaiting approval
before BAD, PLEASE, HELP, STOP.
