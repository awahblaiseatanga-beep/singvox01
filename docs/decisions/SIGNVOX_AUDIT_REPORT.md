# SIGNVOX PHASE 1-4 AUDIT REPORT & RETARGETING DESIGN

## Phase 1: Blender Avatar Audit

**1. Black Line Overlays:**
The massive black lines observed historically in Blender viewports are **not mesh edges or topological corruption**. They are native Blender *Bone Relationship Lines*. These originate whenever physical bones (e.g., wrist IKs) are procedurally mapped to detached tracker empties (`MP_Trace_Left_Wrist` targets) over great spatial distances mechanically. 

**2. Mesh Intersections:**
The severe torso self-intersections witnessed during `ASL_HELLO` playback were induced by mechanical Inverse Kinematics twisting. Because standard MediaPipe depth (Z) was mapped directly onto an IK constraint possessing a rigidly locked *Pole Angle* (-90 degrees), the upper arm was forced to spin laterally along its local axis to satisfy reach targets dynamically, collapsing the geometry organically.

**3. Finger & Vertex Group Integrity:**
The V2 Armature rigorously maintains the full Mixamo `mixamorig4` structural hierarchy natively. 
- *Bones:* Contains 3 distinct phalanx joints per finger natively.
- *Weights:* Clean interpolation mapped across `Index`, `Middle`, `Pinky`, etc. Modifiers perfectly evaluate the topological weights structurally. 
- *Articulation:* Capable of complete fluid dynamics naturally. The historic issue was that **0% of the hand tracker data was injected during baking**.

**4. A-Pose Integrity:**
The baseline V2 geometry structurally relies on the generic Mixamo T-Pose as its underlying mathematical Rest Pose. The arms-down posture evaluated inside Browser is bound dynamically by the default `AvatarController` logic.

**5. Mixamo.com Animation Compatibility:**
The fallback `mixamo.com` clip relies on quaternion mappings intrinsic to this skeleton securely. Structural parity is fully compatible.

---

## Phase 2: Feature-Tensor Schema (`0022932153577568393-HELLO_features.npy`)

Extracted via `tools/extract_dataset.py`, the 366 dimensions are mathematically distributed exactly as follows:

| Component | Landmarks | Dimensions | Math Size | Mapping Definition |
|-----------|-----------|------------|-----------|--------------------|
| Left Hand (lh_active) | 21 | 3 (X, Y, Z) | 63 | Extracted via crop bounds; Normalized cleanly |
| Right Hand (rh_active) | 21 | 3 (X, Y, Z) | 63 | Extracted via crop bounds; Normalized cleanly |
| Pose/Body (pose_33) | 33 | 5 (X, Y, Z, Vis, Pres) | 165 | Shoulders/Elbows track visibility metrics |
| Face (face_25) | 25 | 3 (X, Y, Z) | 75 | Subset of full facial mesh bindings |
| **TOTAL** | | | **366** | |

**Crucial Findings:**
1. The tensor **DOES contain depth (Z) natively**, contrary to previous assumptions!
2. Internal normalization (`center_x`, `scale = dist_shoulder`) guarantees relative consistency.
3. The root failure inside `blender_trace_numpy_v2.py` was that it **only read indices `Left/Right Shoulder/Elbow/Wrist` and completely ignored the 126 Hand dimensions natively.** 
4. MediaPipe yields spatial vectors natively (positions); it does NOT output rotational SO(3) matrices. All bone rolls/palms must be analytically determined using math (e.g., cross products mapping Index/Pinky bases).

---

## Phase 3: Reference-Driven Motion Pipeline Design

To sever dependency on flawed IK limits, the new pipeline maps native video straight to 3D rotation logic.

1. **Extraction:** Run Video through native Vision networks, emitting precise `(x, y, z)` spatial matrices across 21 hand joints.
2. **Analytical Solving (The missing link):** Convert spatial vectors natively into Rotational Quaternions mathematically bounding the Palm Normal (Cross Product of Wrist-Index & Wrist-Pinky) natively before generating bones.
3. **Retargeting/Baking:** Apply derived Rotations directly onto standard Blender Animation channels internally without IK bindings restricting coordinate angles. 
4. **GLB Export:** Dump to strict Keyframe tracking native paths cleanly, erasing diagnostic variables.
5. **Validation:** Browser playback executes statically decoupled from runtime inverse limit math!

---

## Phase 4: Prototype Plan (ASL_HELLO)

- **Input:** Single normalized baseline ASL_HELLO Reference Video locally evaluated.
- **Processing:** Direct extraction generating true 366-D array matrix natively locally in CLI.
- **Conversion Math:** Map `lh_active`/`rh_active` strictly to Rotational bounds utilizing numpy cross-product math targeting the palm origin limits accurately.
- **Output Validation:** Generate *one* final `SignVox_Female_v4_HELLO.glb` bounding strictly organic angles securely. No systemic pipeline loops deployed until explicitly accepted by user.

---

## Required Deliverables Matrix

| Check | Deliverable | Status |
|---|---|---|
| 1 | Blender Audit logic | **PASS** - Relationship lines + Fixed IK limits identified safely. |
| 2 | Verified Tensor Schema | **PASS** - 366 structure mathematically mapped precisely resolving Depth (Z). |
| 3 | Pipeline Architectural Design | **PASS** - Migrating off generic IK to Analytical quaternion synthesis precisely. |
| 4 | One-sign Prototype Map | **PASS** - ASL_HELLO bound statically. |
| 5 | Phase Arrest | **PASS** - Pipeline paused awaiting User Approval! |
