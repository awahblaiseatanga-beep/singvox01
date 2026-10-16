# Android MediaPipe Tasks frame processor

## Decision

Use the React Native VisionCamera 4 frame-processor API to call an Android native plugin. The plugin reads the native `ImageProxy` image and runs MediaPipe Pose, Hand, and Face Landmarker Tasks on the same frame. JavaScript receives per-frame status/metrics only; it receives landmark arrays only for a requested one-frame diagnostic.

The app explicitly selects the **back camera** with VisionCamera `useCameraDevice('back')`. It does not set `isMirrored`; VisionCamera V4's back-camera preview default is unmirrored. On Android, the plugin wraps `frame.image` with `MediaImageBuilder`; it does not create a bitmap or physically rotate/mirror the pixels. It reads `ImageProxy.imageInfo.rotationDegrees` and passes that metadata to MediaPipe `ImageProcessingOptions`. MediaPipe therefore performs inference in the rotation-corrected image coordinate space; no coordinate mirroring is applied. The numeric rotation depends on the device orientation and is included in each status record and diagnostic. The frame buffer itself remains in the camera's buffer orientation; the preview is rendered by VisionCamera's preview surface. Device-level alignment with the preview and the canonical decoded-video orientation still requires the physical-device comparison.

MediaPipe handedness labels assume mirrored/selfie input. Since this app currently processes the unmirrored back camera, Android swaps the *labels only*: task `Left` goes into canonical RH; task `Right` goes into canonical LH. Landmark coordinates and their 21-point order are unchanged. This matches the explicit label inversion in the canonical crop-fallback code for unmirrored frames. It does not reproduce the canonical Holistic primary detector or its wrist-crop fallback.

## Raw group contract

- `leftHand`: 21 points × XYZ
- `rightHand`: 21 points × XYZ
- `pose`: 33 points × XYZ, visibility, presence
- `face`: first 25 points × XYZ, matching the existing compact face selection
- Missing or invalid groups are zero-filled with their fixed shape.
- `groupStatus` reports `detected` or `missing`; `invalidGroups` identifies groups zero-filled because of invalid shape/non-finite values.
- The one-frame diagnostic includes these four arrays, group statuses, frame dimensions, rotation metadata, camera facing/mirroring, coordinate-space label, and timestamp. No camera pixels are sent to JavaScript.

## Model files

The three `.task` bundles are local ignored artifacts. Run `python app/scripts/copy_mediapipe_models.py` after downloading them to copy them to Android assets. Gradle keeps `.task` files uncompressed. The copies remain ignored and must not be committed.

## Verification limits

The current machine has no Java/JDK, Android SDK, `adb`, or installed app dependencies. No Android build or device run has been performed. A physical Android device with USB debugging is the intended test target; an emulator is not required. Raw camera orientation and coordinate equivalence remain unverified until the diagnostic is compared on-device with the canonical extractor.
