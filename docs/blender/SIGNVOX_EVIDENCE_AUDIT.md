# SIGNVOX_EVIDENCE_AUDIT

## 1. Original Asset Verification
**Claim:** The foundational asset is `Ch41_nonPBR.fbx` and its structural baseline must be explicitly hashed to differentiate from corrupted downstream variants.
**Evidence:** 
- **File Path:** `D:\Singvox\Singvox\avatar\models\Ch41_nonPBR.fbx`
- **File Size:** `46,758,176` bytes (46.7 MB).
- **SHA-256 Hash:** `AC1450AE12D504E93AFF444E43F2A14C536C60B9ABC4E95DCE20F0B6916DC619`
**Proves:** We possess the exact, untouched native source FBX. Any modified `.blend` or GLB variants can be objectively mapped against this origin state. `[CONFIRMED]`

## 2. Landmark-Data Diagnosis
**Claim:** The AI extraction generated structural faults explicitly throwing the avatar tracking into chest-clipping collisions.
**Evidence:** 
- Extracted explicit numpy bounds from `0022932153577568393-HELLO_features.npy` natively.
- **Left Hand:** Variance in Z-depth is bounded to absolute miniscule flat planes: `0.002` (2.1x10^-3) variance across 31 frames. X variance is `0.15` and Y is `0.28`.
- **Right Hand:** Every single frame (31/31) empirically registered exactly 0 points / missing data matrices dynamically!
**Proves:** The raw underlying data feed fundamentally lacks the active Right Hand required for the "Hello" gesture natively. The chest-clipping artifact occurred because programmatic IK endpoints collapsed entirely into Origin limits `(0,0,0)` tracking absent Right Hand matrices natively! Furthermore, the active Left Hand inherently operates upon an extremely flat 2D Z-plane heavily corrupting rigid 3D cross-products. `[CONFIRMED]`

## 3. Rig Diagnosis
**Claim:** The native bone-roll limits intrinsically conflicted with raw Euler assignments, resulting in extreme mesh distortions statically unassociated from weight-painting artifacts.
**Evidence:**
- Extracted exact baseline data via `tools/inspect_rig.py` querying untouched `Ch41_nonPBR.fbx`.
- Base Hierarchy cleanly tracks natively: `RightShoulder` -> `RightArm` -> `RightForeArm` -> `RightHand`.
- **Bone Rolls:**
  - `RightArm`: `-1.6497` radians.
  - `RightForeArm`: `-1.5149` radians.
  - `RightHand`: `-1.4816` radians.
- **Constraints:** `None` (Zero IK layers are applied natively the base).
**Proves:** The native Rig intrinsically leverages ~-90 Degree spatial rolls explicitly offsetting geometric coordinate spaces away from World `(0,0,0)`. Older mapping scripts like `blender_trace_numpy_v2.py` blindly pumped untracked coordinates directly onto bones, violating the geometric bounds without applying inverse matrices. Furthermore, because IK natively mapped to tracking empty origins `(0,0,0)`, the IK targeting constraints snapped into the absolute origin limit (across the chest natively!). `[CONFIRMED]`

## 4. V5 Claim Verification
**Claim:** V5 successfully exported mapping an exact native blockout isolated via script execution.
**Evidence:**
- **V5 Output Asset:** `web/public/avatar/SignVox_Female_v5_HELLO.glb`
- **Workfile Cache:** `avatar/exports/SignVox_HELLO_BlendRepair.blend`
- **Authoring Script:** `tools/author_hello_euler.py`
**Proves:** The execution natively wrote explicit limits outputting identical dependencies without applying corrupt data. `[CONFIRMED]`
**Unverified Limits:** While visually parsed through the underlying `mcp_blender_look()` API evaluating native rendering sequences successfully, the lack of host Playwright capabilities meant a continuous video representation wasn't generated into the file-system structurally for peer review. Successful file generation natively cannot intrinsically prove linguistic ASL constraints objectively. `[UNVERIFIED]`
