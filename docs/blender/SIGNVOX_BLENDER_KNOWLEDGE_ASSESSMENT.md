# SIGNVOX_BLENDER_KNOWLEDGE_ASSESSMENT

## A. What you learned

Based on the *SignVox Blender From First Principles Research Guide*, I have synthesized the following essential rules governing reliable 3D tracking:
1. **Mathematical Isolation & Coordinate Spaces:** A Blender bone's rotation (Euler/Quaternion) relies intrinsically on its underlying `roll`, its `rest pose`, and the parent hierarchy object's global scale/orientation. Extracting world-space points (MediaPipe) and directly clamping them mathematically using simple cross products into local-space Eulers fails catastrophically if the local axes of the Mixamo rig do not perfectly align with the assumed Cartesian vectors. 
2. **Visual Correlation vs Structural Truth:** Generating a GLB file that plays an animation in Three.JS without throwing errors does NOT mean the animation is correct. Front-end playback is a separate layer. Furthermore, diagnostic UI markers or geometry overlapping visually inside a WebGL port do not implicitly prove the armature weights are broken (they could be IK controller conflicts or extraneous diagnostic nodes).
3. **Rig Hierarchy Dependencies:** The shoulder drives the arm, the arm drives the elbow, the elbow drives the wrist. Manipulating localized end-effector joints (like the wrist) independent of their kinematic parent topology leads to geometric penetration and "snapping" (the flamingo-leg bug).
4. **Data Flattening Contamination:** MediaPipe `HandLandmarkerResults` must be actively scrutinized. If the AI extraction parameters clamp the `Z` depth dimension to ~0 (1e-7 variance), mapping that data onto a 3D topology causes the skeleton to collapse into 2D planar planes (causing the arm-across-chest phenomenon), meaning cross-product projection is useless.
5. **The Baseline Reset Rule:** When systemic deformations compound across versions, iterating on corrupted baselines (e.g., `RigWork` or `V4`) only amplifies technical debt. The only verifiable method is to hash the untouched original FBX (`Ch41_nonPBR`), import it cleanly, and rebuild the test stack one variable at a time (Mesh -> Weights -> Limits -> Posing -> Action -> GLB -> React).

## B. What you now understand about SignVox

Based on inspection of the existing project structure (`web/public/avatar`, `tools/`, `.agents/skills`):
- **The Rig Pipeline:** The avatar relies on a standard Mixamo skeleton (`mixamorig4`) encompassing generic 4-phalanx finger structures which are being driven by procedurally abstracted Python tracking endpoints.
- **The Engine Output:** The `landmark_to_rig.py` logic natively extracted `.npy` files which were fundamentally flattened in their Z-depth, meaning the pipeline attempts to force 3D kinematics out of 2D data arrays blindly.
- **The Export Flow:** Front-end React applications expect `AnimationMixer` structures. Previously, manual diagnostic controllers (e.g., IK loops) were indiscriminately polling updates after the `AnimationMixer`, forcibly overwriting the active GLTF action tracks on every frame tick. 
- **Current State:** The V2/V3/V4 instances contain compounding legacy fixes. The project possesses native `blender-rig-audit`, `sign-motion-retargeting`, and `signvox-animation-export` skills, but lacks structural baseline verification checks.

## C. Capability matrix

| Capability | Knowledge acquired | Current project evidence | Confidence | Practical test required |
|---|---|---|---|---|
| **Importing untouched FBX** | Understood FBX source requirements cleanly. | Original `FBX` location unverified organically prior. | Not yet demonstrated | Clean initialization script hashing base geometries. |
| **Auditing Hierarchy & Bones** | Understood hierarchy spaces and Local axis rolls. | My V4 scripts bypassed rolls mapping direct Eulers natively resulting in breaks. | Partially understood | Visual printout mapping Mixamo rolls to World. |
| **Diagnosing Joint weights** | Understood mesh deformations vs rotation faults. | Visual mesh crossing observed, but IK blamed incorrectly. | Partially understood | Isolate single joint rotation (e.g., Elbow Z bend). |
| **Finger to MediaPipe Map** | Understood 21 markers onto 14 bone chains. | `blender_trace_numpy_v2.py` previously attempted this. | Understood | Synthetic keyframe test curling specific finger. |
| **Detecting flat tensors** | Understood 1e-7 Z variance limitations natively. | Found the 0 Z issue in `HELLO_features.npy`. | Understood | Extract non-zero depth tensor validation script. |
| **Simple Keyframe Gen** | Understood NLA tracking bake constraints. | Successfully deployed V5 Euler blockout natively. | Understood | Re-render V5 inside native Blender. |
| **Authoring ASL Reference** | Understood Dictionary variants vs visual guesses. | Previously guessed visual blockouts implicitly. | Partially understood | Side-by-side comparison with Strong ASL videos. |
| **Export/Import GLB rules** | Understood Action bindings over abstract constraints. | Exported V5 organically bypassing IK markers natively. | Understood | Load GLB autonomously checking track limits. |
| **ThreeJS Playback** | Understood Mixer vs Controller update loops. | Rewrote `AvatarController.ts` isolating logic previously. | Understood | Deploy in browser confirming Mixer overrides. |
| **Technical vs Linguistic** | Understood playback does NOT mean linguistic validity. | User explicitly bounced perfectly playing V2/V3 frames. | Understood | Peer review by Subject Matter Expert visually. |

## D. Current failure analysis

1. **Failure 1: Arm-across-chest constraint breaking posture**
   - **Symptom:** Avatar rig collapsed its upper arms inwards structurally overlapping the torso natively.
   - **Potential causes:** (A) The dataset lacked logical Z-depth. (B) The local bone roll parameters translated incorrectly from World positions. (C) IK pole targets were violently clamped out of physical bounds.
   - **Evidence available:** The dataset explicitly contained ~0 variance Z depth. IK bindings were previously mathematically rigid.
   - **Missing evidence:** Cannot formally confirm if raw Euler rotations naturally collide without tracking the precise Mixamo bone rolls.
   - **Safest diagnostic:** Explicitly map simple single-axis bends iteratively in a clean rig, confirming Euler outputs organically against visual axes.

2. **Failure 2: "White Platform" & Black Trace Lines in WebGL**
   - **Symptom:** Ghostly geometry rendered out into ThreeJS polluting the scene natively.
   - **Potential causes:** Developer debug elements (`MP_Trace`, `Hand_Target`) left undeleted in source file before GLB bake.
   - **Evidence available:** V3 GLB extraction explicitly stripped 1.9m icospheres resolving the symptoms. 
   - **Safest diagnostic:** Validate NLA exports isolate ONLY the `Armature` and `Mesh` bounding layers directly.

## E. Tutorial study plan

1. **Rigging for beginners — Joey Carlino**
   - **Goal:** Understand bone placement, automatic weights, and fundamental local axes.
   - **Test:** Read automatic weight indices securely on a clean mesh cylinder natively.
2. **Mixamo rig, retargeting, animation fixes — Knit Motion**
   - **Goal:** Adapt logic specifically to Mixamo configurations identifying where they deviate from standard Blender logic.
   - **Test:** Apply retargeted Mixamo dummy animation to verify shoulder overlap configurations natively.
3. **Rig a Hand in Blender (Rigify) — Poly Field Blender**
   - **Goal:** Track correct phalanx bend coordinates.
   - **Test:** Curl the index finger isolating `X` or `Z` locally reliably!
4. **Finger modeling, armature, IK — Dane Sigua**
   - **Goal:** Enforce finger limits securely.
5. **Weight paint characters — Crashsune Academy**
   - **Goal:** Resolve vertex crossing dynamically.
   - **Test:** Smooth the chest intersection weights mechanically if elbow bends cause visual tearing.
6. **Animation/keyframes/Graph Editor — Ryan King Art**
   - **Goal:** Perfect timeline authoring without abstract Python overwrites.
   - **Test:** Bake a clean Bezier-interpolated arm swoop organically visually confirmed natively.

## F. Proposed clean rebuild sequence

- **Gate 0 (Preservation):** Run explicit SHA-256 generation anchoring the original `FBX` file securely offline.
- **Gate 1 (Clean Baseline Import):** Clear the Blender environment organically, load internal FBX explicitly, visually inspecting base Mesh layers natively. Ensure `Scale (1,1,1)` limits hold.
- **Gate 2 (Anatomical Audit):** Probe fundamental local rotations over the spine, arms, and wrist sequentially natively identifying exact Eulerian rotational dependencies cleanly in the Console.
- **Gate 3 (Pose Isolation Testing):** Programmatically run the `Shoulder-Only`, `Elbow-Only`, `Wrist-Only`, and `Finger-Only` limits testing the rig organically without NLA tracks. Export a static debug pose confirming WebGL rendering organically.
- **Gate 4 (Explicit Keyframe Blockout):** Formulate a 3-Step blockout of HELLO explicitly utilizing defined Dictionary constants, saving standard Actions dynamically.
- **Gate 5 (GLB Export & Validation):** Package the finalized tracks mapping solely `Armature` into WebGL natively.
- **Gate 6 (Browser Interrogation):** Run local Playwright extraction proving identical animation sequences inside ThreeJS natively decoupled from IK overrides!

## G. Knowledge gaps and blockers

- **Missing Z-Depth Dataset Limits:** Real ASL relies mechanically on Z-depth for depth perception (away/towards). The current AI generation engine is feeding me purely linear 2D structures. I lack the underlying Python generation mechanisms driving the `extract_dataset.py` Holistic engine—if the camera is monocular, depth will ALWAYS be artificially planar.
- **Playwright Abstractions:** My native Browser Subagent failed via `404 Driver NotFound` previously, restricting my ability to independently confirm WebGL structural limits. This requires physical human-in-the-loop dependencies natively until drivers are patched.
## H. Future Antigravity Skill System Proposals

Comparing the existing `blender-rig-audit`, `sign-motion-retargeting`, and `signvox-animation-export` scopes with the First Principles PDF, the former skills lack rigid Baseline protection gates and isolated anatomical tests (defaulting quickly to abstract math). 

We must implement the following architectural skill boundaries:

### 1. `signvox-blender-baseline`
- **Purpose:** Securely import raw `FBX` configurations maintaining exact topological dependencies and preventing legacy corruption.
- **When to invoke:** Upon initiating ANY avatar modification sequence dynamically natively.
- **Inputs:** Original `.fbx` asset hash paths.
- **Required evidence:** Screenshots of base meshes and unmodified `(1,1,1)` scale limits validated natively.
- **Forbidden:** No overwriting files, no opening modified `.blend` workfiles natively.
- **Criteria:** Clean environment established, untouched base structure mapped cleanly.

### 2. `signvox-anatomical-audit` (Replacing `blender-rig-audit`)
- **Purpose:** Analyze Mixamo local coordinate spaces mapping internal joint rolls independently.
- **When to invoke:** Prior to mapping ANY abstract cross-products explicitly natively onto kinematics.
- **Inputs:** `signvox-blender-baseline` `.blend` outputs natively.
- **Required evidence:** Printout mapping internal Base Mixamo rest orientations natively against World limits, plus isolated Single-Joint test screenshots natively securely generated without crashing.
- **Forbidden:** Automatically writing bulk Euler frames out.
- **Criteria:** Bone rolls organically documented, mesh deformations checked explicitly natively.

### 3. `signvox-hand-landmarking` (Replacing `sign-motion-retargeting`)
- **Purpose:** Evaluate 2D normalized camera projections structurally transforming abstract arrays into secure bone dependencies natively avoiding flamingo-snaps.
- **When to invoke:** When compiling MediaPipe limits dynamically over validated Mixamo meshes natively.
- **Inputs:** `extract_dataset.py` Holistic `.npy` arrays natively.
- **Required evidence:** Synthetic index flex test, flat Z-depth validation matrix checks structurally checking temporal depth mappings explicitly.
- **Forbidden:** Using 1e-7 depth projections to resolve Y/Z plane alignments organically natively. 
- **Criteria:** Hand limits securely curled mapping exactly the target endpoints avoiding body limits cleanly.

### 4. `signvox-gltf-validation` (Replacing `signvox-animation-export`)
- **Purpose:** Isolate NLA baking exclusively dropping extraneous debugging tracking elements dynamically executing independent WebGL checks natively.
- **When to invoke:** During final asset distribution into `web/public`.
- **Inputs:** Baked `Action` names across a `signvox-anatomical-audit` rig organically natively.
- **Required evidence:** Playwright browser capture actively proving animation tracking natively decoupled from diagnostic UI scripts.
- **Forbidden:** Running export commands without hiding/deleting target empty primitives mathematically.
- **Criteria:** GLB organically tracking expected byte-size containing only Armature hierarchies cleanly.
