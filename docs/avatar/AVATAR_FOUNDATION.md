# SignVox Avatar Foundation (R4.1)

## Architecture
The foundation enables dynamic loading of GLB characters linked to our canonical Mixamo-based `boneMap`. This ensures that ASL sequences can be applied abstractly on any compliant skeleton irrespective of original character dimensions or visual meshes.

## Main Selected Avatar
- **Character:** Ch41_nonPBR.fbx
- **GLB Output Expectation:** `avatar/exports/SignVox_Female.glb` (49,576,404 bytes)
- **Source/License Status:** LICENSE STATUS: REQUIRES VERIFICATION (Obtained from an external source resembling Mixamo but confirmation is required before any commercial distribution).

## Structural Details
- **Armature Name:** Armature (Node 0)
- **Bone Count:** 73 (66 mapped canonical + 7 extra mixamo root/leaf bones)
- **Fingers:** Fully supported. All 5 digits per hand each have canonical bindings logically validated.
- **Mixamo Prefix used:** `mixamorig4:`
- **Face Capabilities:** NOT AVAILABLE (0 Morph Targets / Shape Keys found in physical GLB).
- **Available Animations:** 1 (`mixamo.com`) - Generic locomotion/idle track.

## Performance Baseline
- The pure React-Three approach retains a nominal load performance overhead.
- No new libraries were introduced other than runtime `three.js`. Vite development proxy avoids unnecessary framework-layer wrapping.

## Developer Diagnostic
The diagnostic screen (`#avatar-diagnostic`) contains physical testing of all isolated skeleton fingers, capabilities reporting, and manual error recovery flows to preserve the functional `MediaPipe` integration.

## Verification & Validation Status
The R4.1 foundation has achieved a unified **PASS** following manual UI validation against the raw browser DOM:
- **HTTP Transport**: PASS (GLB `49.5MB` delivered over `:5174` proxy flawlessly).
- **Physical Finger Binding**: PASS (Left Hand 1→3, Right Hand 1→3 complete chain verifications confirm empirical 3D visualization rotations trigger cleanly over normalized canonical indices).
- **Canonical Capability Loader**: PASS (Capabilities explicitly decouple 'Structural' from 'Signing' dependencies successfully capturing `hasLeftFingers`, `hasRightFingers`, and `hasHead`).
- **Regression Pipeline**: PASS (All 59/59 non-avatar systems maintained parity).

## Implemented Files
- `tools/export_glb.py` (Script to safely extract `glb`)
- `avatar/controller/boneMap.ts`
- `avatar/controller/avatarCapabilities.ts`
- `avatar/controller/AvatarController.ts`
- `web/src/components/AvatarDiagnostic.tsx`
- `web/tests/avatar.test.ts`
- `docs/avatar/AVATAR_FOUNDATION.md`

## Next Steps
Complete R4.2 — Avatar Controller + Hand/Finger System scaling towards mapping SPOTER embeddings directly into localized skeletal transforms.
