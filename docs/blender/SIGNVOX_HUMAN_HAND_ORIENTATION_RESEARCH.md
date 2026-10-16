# SignVox R4.4 — Human Hand Orientation and Anatomical IK Research

## 1. Relevant Anatomy and Biomechanics

Human upper-limb motion operates through a complex chain of distinct joints, each with specific Degrees of Freedom (DOF). In robotic and computational kinematics, merging these DOFs often yields unnatural "spaghetti" bending if physiological restraints aren't implemented.

*   **Shoulder Complex (Sternoclavicular & Glenohumeral):** The true shoulder joint (glenohumeral) acts as a ball-and-socket, allowing flexion/extension (raising arm forward/back), abduction/adduction (raising arm sideways), and internal/external rotation. The clavicle/scapula assist heavily during reaching (e.g., shrugging or reaching across the chest).
*   **Elbow (Humeroulnar & Humeroradial):** The elbow operates strictly as a hinge joint. It handles **flexion and extension exclusively (1 DOF)**. It cannot intrinsically twist.
*   **Forearm (Radioulnar joint):** The forearm comprises the radius and ulna bones, which overlap each other to create **pronation (palm down) and supination (palm up)**. This axial rotation happens across the length of the forearm, *not* at the wrist joint itself.
*   **Wrist (Radiocarpal joint):** Operates primarily in 2 DOF: flexion/extension (bending palm up/down) and radial/ulnar deviation (tilting hand side-to-side). **The wrist does not axially roll;** all axial roll inherently comes from forearm pronation/supination.
*   **Hand Orientation Distinction:** A hand's orientation must be defined by two distinct vectors:
    1.  **Finger Direction** (distal vector extending from the wrist through the metacarpals).
    2.  **Palm Normal** (perpendicular facing vector coming off the palm skin).

*Sources: Academic Kinesiology References (e.g., Neumann, D. A. (2010). Kinesiology of the Musculoskeletal System; Stokoe's ASL parameters).*

---

## 2. ASL-Specific Orientation Requirements

In American Sign Language (ASL), touching a location is insufficient to convey semantic meaning (phonology requires correct Location, Handshape, Movement, and Orientation).

*   **Semantic Differentiation:** Placing a flat hand on the chest with the palm facing inward means "MINE". Placing the same hand on the chest with the thumb edge inward and palm facing sideways means "FINE".
*   **Wrist Limits:** Many signs mandate natural wrist deviation. A solver that merely positions the hand at a target and blindly twists the shortest path often fractures the wrist mathematically or bends it backward outside human limits.
*   **Movement Trajectory:** Hand orientation must be correctly aligned *before* or *during* the trajectory to the target, rather than violently snapping into orientation once contact is made.

---

## 3. SignVox Rig Audit (`SignVox_Female_v3.glb`)

A Python mathematical audit was executed directly against the exact Blender/ThreeJS arrays for `SignVox_Female_v3.glb`.

**Rig Structure & Bone Capabilities:**
*   **Bones:** `LeftShoulder` (Clavicle), `LeftArm` (Glenohumeral), `LeftForeArm` (Elbow + Twist), `LeftHand` (Wrist).
*   **Twist Bones:** `Twist Bones Found: []`. The rig operates purely on standard Mixamo weights. There are no helper twist bones. Therefore, the `ForeArm` bone is mathematically responsible for both elbow flexion angles *and* forearm pronation/supination twists simultaneously. 
*   **Local Axes:**
    *   `LeftArm`: Y bounds pointing fundamentally downward/outward from the Clavicle.
    *   `LeftForeArm`: Local Y-axis accurately tracks the bone length (`[0.11, 0.97, 0.19]`). Twisting the `LeftForeArm` bone natively across its local Y-axis accurately yields human pronation/supination bounds.
    *   `LeftHand`: Local Y-axis extends distally through the palm.
*   **Solver Constraints:** The current `ArmIKController.ts` limits solver scopes. In `indexFingertip` mode, it uses Phase C (`orientHandTowardsTargetPhaseC`) to evaluate the Delta Quaternion aligning the wrist towards the target via shortest-path `crossVectors`.
*   **The Defect:** Phase C currently controls **only Finger Direction (distal pointing)**. The code establishes Pitch to point the bone, but **lacks explicit Palm Normal (Roll) control**. It arbitrarily inherits whatever twist remains from the upper arm pole solver.

---

## 4. Separating Position IK from Orientation Control

To natively resolve unnatural twists without destroying the stable origin-tracking of R4.3.1, the hierarchy must mathematically split the solver:

1.  **Position Objective (The Cartesian Target):** Handled exclusively by `LeftArm` and `LeftForeArm`. Uses the analytic 2-bone solver to bend the hinge elbow towards a pole target.
2.  **Orientation Objective (The Kinematic Roll):**
    *   *Step A (Pointing):* The Wrist (`LeftHand`) is flexed/deviated to point the Index/Fingertip at the Cartesian Target.
    *   *Step B (Palm Facing / Pronation):* The `LeftForeArm` is twisted across its local Y-axis to satisfy the requested Palm Normal (e.g., "palm facing left", "palm facing torso"). 
    *   *Constraint:* Twisting the `LeftForeArm` rotates the hand attached to it. Mathematical isolation requires subtracting the `LeftForeArm`'s twist from the `LeftHand`'s absolute deviation matrix to avoid compounding errors.

---

## 5. Measurable Test Plan

Before implementing ASL Orientation features, rigorous regression tests within the Diagnostic UI must be drafted observing independent limits:

1.  **Forehead Target (SALUTE):**
    *   *Constraint:* Palm Normal evaluating DOWN and LEFT. Finger Direction evaluating UP and BACK.
    *   *Expected Elbow:* Flared laterally to clear the chest. 
2.  **Chest Target (MINE):**
    *   *Constraint:* Palm Normal evaluating IN (towards Spine). Finger Direction evaluating RIGHT.
    *   *Expected Elbow:* Tucked naturally downward.
3.  **Shoulder Target (TAP):**
    *   *Constraint:* Palm Normal evaluating DOWN. Finger Direction evaluating BACK.
4.  **Mouth Target (EAT):**
    *   *Constraint:* Palm Normal evaluating IN. Finger Direction evaluating IN (curled handshape).

**Visual Evidence Required:**
*   Screenshots demonstrating successful Palm Normals at each target without breaking the Cartesian fingertip tracking.
*   Verification that Y-axis twists applied to `LeftForeArm` do not collapse the mesh natively.

---

## 6. Proposed Implementation Staging (Post-Approval)

1.  **Introduce Explicit Target Transforms:** Expand the diagnostic UI and `ArmIKController` signature from accepting pure positional vectors (`Vector3`) to evaluating explicit transform limits (`Position`, `LookAt Direction`, `Palm Normal`).
2.  **Roll Extraction:** Implement a Local Y-Axis Roll solver applied strictly to `LeftForeArm.quaternion` *after* the primary IK distance constraint loop, replacing shortest-path noise with locked orientations.
