# SL2T Technical Analysis (SignVox Research)

## 1. Primary Sources & Capabilities
Google announced **Sign-Language-to-Text (SL2T)** in August 2026 for the Pixel 11 lineup. It operates through Gboard and Live Transcribe integrations. Unlike older systems mapping deterministic hand shapes, SL2T acts as a robust Machine Translation (MT) network interpreting holistic geometry into complete linguistic prose (ASL to English).

### Key Architectural Boundaries
1. **Landmark Extraction (On-Device Perception) [PUBLIC FACT]:**
   - The initial layer relies entirely on **MediaPipe Holistic**.
   - It computes 130 key nodes bounding the face, body, and hands locally on the edge device to prevent raw 1080p web-camera feeds from leaking outside the local mobile processor.
   - **Privacy Benefit:** Because geometry is processed instantly within the device hardware, identifying PII (face image data) is permanently discarded at the boundary before inference mapping occurs.

2. **Translation Core (Cloud Inference) [PUBLIC FACT]:**
   - The 130 geometric coordinates are streamed continuously to Google's backend cloud.
   - Heavy translation inference happens centrally across Google's massive tensor infrastructure rather than entirely on the mobile SOC. [INFERENCE: avoiding thermal constraints and permitting heavy parameter deployment.]
   - Output text is streamed iteratively back to the client interface.

### 2. Output & Interaction Behavior
- **Streaming MT Output:** Rather than classifying single distinct words, the model digests multi-frame phrases (likely employing internal transformer/RNN mechanisms) and emits ongoing textual streams.
- **Latency & Corrections:** Because it is an MT engine, it will inherently re-calculate tokens as the sentence expands. Words generated early in a query might be corrected or omitted as trailing descriptors alter the grammatical context of the ASL sequence natively.

### 3. Publicly Disclosed vs Undisclosed
| Property | Disclosed | Undisclosed / Proprietary |
| :--- | :--- | :--- |
| **Input Shape** | 130 MediaPipe Holistic Nodes (Edge extracted) | Normalization standards, velocity parameters, frame sampling rates. |
| **Deployment Layer** | Hybrid (Edge Perception + Cloud MT) | Size of the translation model, internal API transport protocols. |
| **Model Structure** | Machine Translation Engine across 50+ languages | Intermediate sequence representations (does it generate gloss first?), transformer depth. |
| **Dataset Scale** | Trained over 100,000+ hours of video | Data sourcing licenses, specific augmentation steps combating noise. |

### 4. Feasibility for SignVox Reconstruction
It is presently impossible to identically clone SL2T without equivalent Google-scale TPU arrays for training over 100K+ hours of specialized video. However, SignVox already naturally aligns with the geometric extraction methodology: SignVox currently leverages ONNX and MediaPipe bounds mapping coordinate systems. Transitioning SignVox to an MT engine (away from an isolated label classifier) is the necessary next step, requiring significant changes to the model output tensor and sequence compilation logic internally.
