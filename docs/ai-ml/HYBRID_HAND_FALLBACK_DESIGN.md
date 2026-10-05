# SignVox Hybrid Hand Landmark Fallback Architecture

## Architecture & Integration Point
The foundational Hybrid Extraction module has been formulated securely from scratch in this repository at `ai/sign-recognition/preprocessing/hybrid_landmark_extractor.py`.

## Fallback Trigger Configuration (Opportunistic Crop Fallback)
The fallback rule utilizes strict architectural absence rather than non-viable per-node threshold scoring algorithms:
**Rule: Holistic hand absent -> attempt Dedicated Hands opportunistic crop fallback.**
Because MediaPipe Holistic's hand tracking nodes do not natively provide robust per-waypoint visibility arrays natively (it strictly projects the fully modeled 21-node map or simply returns `None`), checking purely mathematical coordinates generates fake quality representations internally against static frames. Fallback rigorously checks for pure object absence, proposing an opportunistic regional crop (anchored to pose wrists) and safely running exactly once if missing.

**Note on Recovery Expectations:** The crop fallback is strictly an *opportunistic fallback*. While the current 20-video diagnostic validation formally produced 0 structural recoveries, this was unequivocally because every targeted fallback case was evaluated strictly as `NO_ANCHOR` (the corresponding pose wrists were entirely absent from the spatial frame). The 0% recovery natively models out-of-frame physical reality, and explicitly should *not* be interpreted as proving Dedicated Hands cannot recover geometries out of valid algorithmic anchor bounds.

## Handedness Handling
Frames extracted directly from ASL Citizen manifest structures strictly evaluate as unmirrored real-world interactions. MediaPipe Hands natively constructs its categorical metadata labels under the strict assumption of a mirrored/selfie-camera format natively.
**Explicit Handedness Correction Schema:**
- `mp_label` == `"Left"` maps explicitly backward to analytical `"Right"` (`right_hand_xyz`).
- `mp_label` == `"Right"` maps explicitly backward to analytical `"Left"` (`left_hand_xyz`).
This precise reversal inverts the API's selfie bias, keeping geometric coordinates tied accurately to their canonical physical space slots mathematically.

## Normalization Ordering
Data constraints execute dynamically mapped coordinate projections seamlessly relative strictly to static shoulder variables (shoulder-origin offset/shoulder scaling constants). The normalization functions fire linearly after all fallbacks merge seamlessly, explicitly bypassing potential mirror interference variables structurally.

## Provenance Tracker
Each tracking frame bounds unique string metrics capturing origins dynamically across:
- `holistic`
- `hands_fallback`
- `missing`

## Safety Constraints & Output Geometry Format
Target 366-D vectors strictly flatten natively inside exactly the same 4 slots mapping: `0:63` Left Hand, `63:126` Right Hand, `126:291` 33-Node Holistic Pose, and `291:366` 25-Node Face bounds. Remaining frames strictly retain mathematically complete zero-fills.

## Validation CLI Configuration
Integration supports a detailed output summary natively enumerating exact holistic anchors retained mapping exactly alongside explicit fallback deployment constraints, successfully documenting structural output characteristics seamlessly into the deployment payload.
