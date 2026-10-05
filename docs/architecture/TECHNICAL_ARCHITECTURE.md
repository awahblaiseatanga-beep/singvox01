# SignVox Technical Architecture

## 1. Product Architecture
SignVox operates as a mobile-first intelligent communication bridge. The core loop consists of a continuous visual and audio input stream, localized spatial feature extraction, machine-learning-based temporal translation, and synthesized output (verbal or visual 3D avatar).

## 2. Mobile Architecture
**Recommendation:** React Native.
**Reasoning:** Provides a robust unified codebase for iOS/Android while possessing mature native bridging capabilities (e.g., VisionCamera, JSI native modules). We can execute C++ level frame processors for raw camera manipulation without crossing the React Native bridge for every frame, attaining native-tier performance for the AI constraints.

## 3. Computer-Vision Architecture
**Recommendation:** MediaPipe Holistic (or specialized Pose + Hand tracking).
**Reasoning:** Highly optimized for on-device mobile execution. Extracts high-fidelity spatial landmarks (X, Y, Z coordinates for body posture, hands, and facial geometry) directly from the camera feed.

## 4. ASL Recognition Architecture
**Recommendation:** Landmark-Based Temporal Neural Network.
**Pipeline:**
`Camera -> MediaPipe Landmarks -> Sliding Window Buffer -> Lightweight Temporal Network (ST-GCN / Transformer) -> Sign Gloss Output`
By vectorizing the landmarks instead of performing CNNs on raw video frames, the computational cost plummets, enabling 30+ FPS real-time inferences on average edge devices.

## 5. AI/ML Architecture
**Recommendation:** 
- **Training:** PyTorch.
- **Inference Format:** ONNX / TensorFlow Lite.
- **Execution:** Mobile CPU/NPU via platform-native ML delegates (CoreML/NNAPI) driven by ONNX Runtime Mobile or TFLite.

## 6. Speech Architecture
**Recommendation:** On-Device Speech-to-Text (Platform Native APIs or whisper.cpp).
**Reasoning:** Processing speech locally honors privacy, prevents lag over cellular connections, and fulfills the offline constraint. 

## 7. Translation Architecture
**Recommendation:** 
- **Phase 1 (MVP/CITX Demo):** Strict phrase mapping / Rule-based dictionary (Direct speech-to-gloss mappings) for ultra-high determinism.
- **Phase 2+ (Production):** Cloud Edge Function running a specialized Seq2Seq translation model or bounded LLM taking conversational English and generating accurate ASL Gloss sequence including NMS (Non-Manual Signals) definitions.

## 8. Avatar Architecture
**Recommendation:** Real-time rigged 3D character context (WebView/Three.js or embedded Unity player).
**Reasoning:** Video clips fail to scale and cannot blend transitions between dynamic sentences. A rigged 3D avatar parameterized to handle hand kinematic limits and facial blend-shapes allows dynamic programmatic execution of signs.

## 9. Supabase Architecture
Supabase will handle all persistence outside the real-time processing loop.
- **Auth:** Device-based anonymous sessions, scaling to verified profiles.
- **PostgreSQL:** Sign language vocabulary dictionary mappings, system configuration.
- **Edge Functions:** Execute speech-to-gloss LLM requests if heavy translation logic is required.
- **Storage:** Perform OTA (Over-the-Air) distribution of updated TFLite models or Avatar assets.

## 10. On-Device vs Cloud Architecture
**Hybrid Architecture Chosen.** 
- **On-Device (Hotpath):** Raw Camera -> Landmark Extraction -> Sign Inferencing -> Output Synthesis. Absolute minimum latency and maximum privacy. Video frames NEVER stream anywhere.
- **Cloud (Coldpath):** Model updating, Heavy algorithmic English -> ASL Syntax translations, Telemetry, and Syncing. 

## 11. Offline Strategy
- SignVox must ship with an embedded baseline TFLite model, ensuring core capability survives offline.
- Speech-to-Text uses OS-level offline recognition APIs.
- Cloud NLP translation will degrade to literal word-to-sign dictionary lookup offline.

## 12. Data Architecture
- **In-Memory:** Rolling buffer of the last N frames of spatial landmarks (e.g., 60 frames = 2 seconds of signing).
- **Persistent Local:** Cached ML models.
- **Cloud:** Anonymized metrics, model metadata. 

## 13. Security Architecture
- **Inference Limits:** Once landmarks are extracted, camera pixel arrays are immediately discarded.
- **Supabase RLS:** All network payloads isolated strictly by User UUID. 

## 14. Testing Architecture
- Unit Testing: Model inference layer and UI.
- Deterministic E2E: Injecting pre-recorded landmark JSON files into the AI pipeline to guarantee reproducible test sequences automatically.

## 15. CITX Demonstration Architecture
- Strict bounded conversational domain (e.g., ~15-20 crucial signs/phrases).
- Hardcoded fallback mechanics if edge conditions arise. 
- Wholly deterministic local model to guarantee zero internet reliance under stage networking environments.

## 16. Performance Targets
- **Camera Capture:** 30 FPS minimum
- **CV Landmark Extraction Latency:** < 15ms
- **Sign Inference Latency:** < 50ms per window evaluation
- **Speech STT Latency:** < 1000ms
- **Total Local Loop Latency:** ~200-250ms (conversational fluidity threshold)

## 17. Technology Recommendations
- UI: React Native
- Vision Pipeline: MediaPipe
- Inference Binding: TensorFlow Lite
- Persistence: Supabase

## 18. Major Risks
- Precision of the avatar hand rigging (improperly blended fingers make signs unintelligible).
- Scarcity of publicly available continuous ASL datasets with proper facial landmarks included.
- Extreme edge-lighting lowering camera shutter speed, causing motion blur on rapid hand movements.

## 19. Open Questions
- What exact narrow domain vocabulary will form the CITX 2026 demo? *(Note: Refer to `docs/ai-ml/ASL_100_VOCABULARY_SPEC.md` for the current RESEARCH DRAFT vocabulary candidates).*
- Is the avatar presentation intended to be hyper-realistic (heavy rendering penalty) or stylized (easier on battery)?

## 20. Implementation Roadmap
1. Validate MediaPipe React Native integration (FPS constrained testing).
2. Train a dummy temporal model acting on 5 arbitrary signs and deploy to the mobile wrapper.
3. Construct the core React Native UI shell and camera overlays.
4. Integrate the 3D Avatar viewing portal and rig tests.
5. Setup the Cloud Supabase environments for telemetry and OTA models.
