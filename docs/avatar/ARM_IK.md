# SignVox Avatar Arm Inverse Kinematics (R4.3)

## Purpose
R4.3 provides the foundational biomechanical targeting infrastructure handling abstract hand reaching and placement across internal runtime spaces. 
The IK solver explicitly translates Cartesian goal destinations into rotational transformations driving avatar elbows and shoulders autonomously without breaking decoupled manual hand/finger orientations defined in R4.2.

> [!CAUTION] 
> This sub-system does not directly sequence or map ASL animations natively. All vocabulary abstractions lie layers above. 

## Coordinate Systems
- **World Space (`THREE.Vector3`)**: Represents globally transformed node arrays exactly matching the parent `AvatarController` root instance. Internal functions rely explicitly on mathematical matrices over structural rotations safely tracking nested avatar translations in space dynamically.
- **Body-Relative Equivalents (`AnatomicalAnchorName`)**: Static offset representations translated implicitly across real-time base poses (e.g. `'nose'`, `'forehead'`).

## Anatomical Anchor Definitions
Anchors strictly isolate deterministic offsets mapped securely over canonical baseline models:
- **`forehead` / `eyes` / `nose` / `mouth` / `chin`**: Local offsets projected upwards and forwards upon the base `Head` hierarchy array.
- **`sternum` / `chest`**: Outward Y/Z transformations originating securely across the structural `Spine2`.
- **`belly`**: Derived explicitly across lower `Spine` constraints globally.
- **`leftShoulder` / `rightShoulder` / `leftHip` / `rightHip`**: X/Y lateral projections mapping natively outward.

*See `AnatomicalAnchors.ts` for native vector parameters determining exact 1.7m standard rig estimates.*

## Two-Bone Analytic Algorithm
The core solver relies on trigonometric Law of Cosines bounding evaluation loops bypassing computational limits typical inside standard CCD iterations natively. 
Given a distance target bound strictly shorter than `$L1 + L2$`, we evaluate static `alpha` and `beta` hinge constraints explicitly resolving absolute spatial pivot vectors perfectly over single evaluation ticks cleanly averting infinity regressions seamlessly.

## Reach Clamping
Internal tracking functions parse `clamp(goalDistance, minConstraint, armTotalReach)`.
This strictly limits mathematical `Math.acos()` failures if coordinates target physically unreachable spatial vectors natively ensuring stable `NaN` defenses implicitly natively across boundaries.

## Elbow Pole Orientations
Controls establish secondary global tracking `Vector3` properties determining rigid outer limits representing standard elbow projections intuitively over lateral and forward arm extensions accurately averting unexpected inward joint inversion structures.

## Left / Right Isolation
Architectural bounds establish separated instances mapping explicit structural indices across completely discrete namespaces (`LeftArm` vs `RightArm`). Solutions process internal cache caches completely unaware of mutual cross-arm limits avoiding shared geometric overwrites linearly natively.

## Wrist Ownership
The IK instance evaluates structural rotations targeting standard `Shoulder` and `ForeArm` pivots. The terminal `Hand`/`Wrist` quaternion inherently retains geometric independence directly driven through established `HandController` layers safely persisting logical orientations alongside explicit arm-reaching routines.

## Animation Precedence & Reset Bounds
As defined in R4.2.1, tracking loops sequence background clips evaluating before explicit IK calculations.
- `mixer.update(delta)` -> Native clip tracks
- `armIK.update()` -> Stomps base frames with math IK bounds
- `hands.update()` -> Stomps hand/finger orientations rigidly.
All IK resets target rigid cached arrays securely preventing dynamic drift natively completely natively preserving origins securely over infinite test intervals.

## Diagnostics
Within `#avatar-diagnostic`, controls explicitly drive localized parameters determining raw Arm IK anchor tracking and manual structural pole adjustments cleanly visualizing raw targeting logic independent of manual joint mapping vectors.

## Identified Frame Metrics
Targeting executes inside pure JS analytical limits successfully delivering exact vectors effortlessly fitting standard 60-hz loop evaluations with near-zero millisecond impacts naturally avoiding geometric parsing costs.

## Future Context Extensions
Future architectural layers explicitly map parameterized ASL motions translating specific timeline goals directly into raw coordinate/target requests spanning sequential targets seamlessly.
