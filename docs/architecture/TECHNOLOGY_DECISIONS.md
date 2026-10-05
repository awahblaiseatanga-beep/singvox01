# SignVox Technology Decisions

The following table summarizes the primary architectural choices made during the feasibility analysis, mapping component needs against viable candidates.

| Area             | Options Considered      | Recommended | Reason | Confidence |
| ---------------- | ----------------------- | ----------- | ------ | ---------- |
| **Mobile**       | React Native, Flutter, Native (Swift/Kotlin) | React Native (w/ Native modules/JSI) | Rapid iteration, unified cross-platform UX. Can establish zero-copy bridging to native camera pipelines (e.g. VisionCamera). | High |
| **Vision**       | MediaPipe, OpenCV, YOLO | MediaPipe Holistic | Best-in-class mobile efficiency for tracking hand joints, body pose, and face topography. | High |
| **Sign Recognition**| Landmark Sequences vs Raw Video | Landmark Temporal Network | Tracking X/Y/Z vectors is magnitudes lighter computationally than processing raw RGB grid tensors. Required to hit real-time parity constraints. | High |
| **Speech**       | Whisper, Native OS APIs, Cloud Services | Whisper.cpp or Target OS Native STT | Local STT processing ensures high availability in disconnected states and preserves raw microphone data privacy. | Medium |
| **Translation**  | Cloud LLM, Rule-based maps, Seq2Seq | Rule-based MVP → Cloud LLM | Strict phrasebook is perfect for a rapid, deterministic V1 prototype. A tailored LLM can decode ASL gloss mechanics in V2. | Medium |
| **Avatar**       | 3D Rigged Engine, Pre-recorded clips, 2D | 3D Rigged WebGL/Native View | Smooth kinematic interpolation is required to link signs organically. Pre-recorded video cannot scale. | Medium |
| **Backend**      | Supabase, Firebase, Custom | Supabase | Postgres relational capabilities, edge functions for NLP translation, and OTA model management scale effectively. | High |
| **Inference**    | Local API, Cloud Stream, Hybrid | Hybrid (Local Vision + Sign Rec) | Real-time requirement forces hotpath CV off the cloud. Latency limits prevent video streaming constraints. | High |

