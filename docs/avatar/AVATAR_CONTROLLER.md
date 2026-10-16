# SignVox Avatar Controller (R4.2)

## Architecture Overview
The **Avatar Controller** transforms canonical, agnostic intent into safe, deterministic skeletal rotations dynamically coupled to any target geometry.
It formally establishes the separation of concerns: **React manages state abstraction variables**, while the **Avatar Controller commands exact three.js mathematical properties**.

> [!IMPORTANT]
> This layer is generic avatar control and does not encode ASL signs.

## HandModel / Kinematics Types
The interface defines normalized parameters designed specifically to align standard biomechanics natively without specific vocab dependencies:
- **`ThumbPose`**: Regulates flexible offsets tracking Thumb Abduction `[-1, 1]` against localized Z-flex mappings `[0, 1]`.
- **`FingerPose`**: Formalizes `curl` limits `[0, 1]` against lateral splayed joint rotations using `spread` constraints `[-1, 1]`.
- **`WristPose`**: Stores direct rigid body axis limits preventing gimbal collapse over wrist manipulations.

## Transform Ownership
No React or UI logic modifies a `.rotation` or `.quaternion` physically. 
All interactions proxy strictly through `leftHand.index.setCurl(normalized)` ensuring bounded safety. All inputs map to deterministic normalized floats instead of explicit local/global geometric values across arbitrary namespaces.

## Left & Right Autonomy
Instances of `HandController` are functionally walled. Iterations on mapping inputs isolate purely against their target instance space ensuring complete anatomical partitioning. A completely flexed left index structurally guarantees null state side-effects targeting right equivalent chains.

## Neutral Rest Geometry
To overcome baseline skeletal deformations standard across commercial packages (e.g. A-Pose, T-Pose bounds differing dramatically inside Mixamo), the runtime enforces a "Base Quaternion Tracking" loop logic. 
On initialization, all controllers silently clone immutable exact geometric Quaternions. `controller.reset()` perfectly returns the physical model hierarchy to its origin layout regardless of current animation overlays!

## Snapshot & Restoration Pipeline
Through `getSnapshot()` arrays, the domain seamlessly exports the identical runtime models parsed exactly tracking explicit normalized states. When invoking `restore(snap)`, states bypass heavy hierarchy parsers, relying on instant array comparisons rebuilding rotations. 

## Animation Ownership 
The underlying FBX avatar carries embedded looping tracks (e.g., `mixamo.com` idle). Left undisturbed, generic `AnimationMixer` evaluations modify global structural nodes unconditionally, directly impacting fingers/hands and causing unintended parameter offsets. 
To assert programmatic ownership, the system strictly orchestrates frame execution sequences inside `AvatarController.update(delta)`:
1. The `AnimationMixer` natively evaluates underlying embedded tracks sequentially per-delta.
2. `HandController.update()` iteratively loops back over owned structural nodes locally, implicitly stomping the mixed generic track values and enforcing programmatic Quaternions securely.

**Animation Modes**
- **`manual`**: All generic clip mixing is halted; avatar nodes strictly enforce baseline origins globally.
- **`generic`**: Playback forces continuous internal updates (e.g. idle breathing mechanics), but deterministic sub-controls rigidly secure owned node-chains overriding internal track offsets seamlessly.

## Known Limitations
- Modifying Torso sequences natively demands explicit manual routing mapping boundaries protecting base kinematic states across broader arm/body segments not directly managed by Hands.
