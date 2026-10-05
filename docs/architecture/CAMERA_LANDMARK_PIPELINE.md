# Camera & Landmark Pipeline (Technical Spike)

## 1. Camera Technology Selected
**React Native VisionCamera (v4)**
*Why it was selected:* It is arguably the most performant cross-platform React Native camera module available. It explicitly exposes C++ Frame Processors via JSI (Worklets) to allow instantaneous thread-safe read access to raw Camera preview frames (YUV) without ever crossing the JS bridge layer.

## 2. MediaPipe Technology Selected
**MediaPipe Tasks Vision C++ API (Holistic Models)**
*Why it was selected:* The most powerful edge-based tracking solution for complex skeletal modeling (body, hands, and face limits combined). It will be piped directly into a single custom C++ VisionCamera plugin.

## 3. Native / JSI Integration Approach
Raw camera frames arrive inside a VisionCamera Worklet. C++ methods injected into the JS global context via JSI are used to hand over the pixel buffer pointer to the MediaPipe engine running asynchronously on the native edge. The extracted landmark JSON maps are returned down the JSI buffer for JS visualization and buffer queuing for the future AI model.

## 4. Landmark Schema
```json
{
  "timestamp": 1729019918201,
  "leftHand": [{ "x": 0.45, "y": 0.6, "z": -0.1 }, ... ],
  "rightHand": [{ "x": -0.45, "y": 0.6, "z": -0.1 }, ... ],
  "pose": [...],
  "face": [ /* Minimum bounded set for Non-Manual Signals: Eyebrows, Jaw, Lips */ ]
}
```
*Note: Using a strict epoch timestamp resolves out-of-order temporal boundaries in sliding windows. `z` translates depth via normalized local scale.*

## 5. Normalization Approach
**Shoulder-Relative Bounding Normalization**
Absolute frame pixels represent failure if the user is further away from the lens. By pinning the origin `[0,0,0]` strictly to the geometric center between the left/right shoulder pose landmarks, and using the shoulder width as scalar `1.0`, all hand interactions become relative kinematic variables (perfectly consistent regardless of screen distance).

## 6. Processing Pipeline
`Physical Camera -> OS Buffer -> Frame Processor Plugin (C++) -> MediaPipe Holistic execution -> Output landmarks to JSON Array -> Normalization Translation -> Send to JS Thread for overlay / FPS visualization`

## [PENDING PHYSICAL TEST EXECUTION]
Sections 7-13 require physical Android hardware to conduct metrics recording.
* Performance measurements
* Device used for testing
* Lighting conditions
* Known limitations
* Problems encountered
* Recommended next step
