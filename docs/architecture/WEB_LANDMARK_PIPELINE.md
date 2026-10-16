# SignVox browser landmark pipeline

## Active path

The active competition product path is the browser application in `web/`:

`getUserMedia → MediaPipe Tasks Web → canonical 366-D frame → V2 normalization → diagnostic UI`

SPOTER/ONNX inference is intentionally outside Phase 1.

## Camera and orientation

The browser requests the user-facing camera. The `<video>` preview is CSS
mirrored only for the signer. CSS transforms do not alter the `HTMLVideoElement`
given to MediaPipe, so landmark extraction receives the original camera frame.
The pipeline uses `performance.now()` timestamps and a 125 ms target interval.
It does not queue work: a new eligible frame is dropped if processing is busy.

## Landmark assembly

The web app uses PoseLandmarker, HandLandmarker, and FaceLandmarker in `VIDEO`
mode. It produces a fixed 366-D `Float32Array`:

| Slot | Range | Shape |
|---|---:|---|
| Left hand | 0–62 | 21 × XYZ |
| Right hand | 63–125 | 21 × XYZ |
| Pose | 126–290 | 33 × `[X,Y,Z,visibility,presence]` |
| Face | 291–365 | face indices 0–24 × XYZ |

The pose layout is interleaved. For pose landmark `i`, XYZ/visibility/presence
occupy `126 + i * 5` through `126 + i * 5 + 4`.

Missing groups are zero-filled. Wrong-sized or non-finite groups are zero-filled
and reported separately in `invalidGroups`; the emitted vector is always finite.

## Handedness diagnostic

MediaPipe labels are displayed alongside their canonical slots. The active
pipeline supplies the unmirrored frame, so task `Right` maps to canonical LH and
task `Left` maps to canonical RH. Coordinates are never mirrored. This remains
a human-verifiable device diagnostic: show only the anatomical left hand, then
only the right hand, and capture each frame before accepting browser parity.

## V2 normalization

First, coordinate-bearing groups are shoulder-centered using pose shoulders 11
and 12 and their 3-D distance, matching the Python function. Then V2 scalars
are applied to LH XYZ, RH XYZ, pose XYZ, and face XYZ. Pose visibility and
presence are left unchanged. The current Python live tester scales the entire
pose block and is not the V2 deployment reference for this detail.

## Artifact hosting

MediaPipe WASM and task bundles are external deployment artifacts. The source
repository does not commit `.task` model binaries. Production must use immutable
approved asset URLs with recorded SHA-256 values.
