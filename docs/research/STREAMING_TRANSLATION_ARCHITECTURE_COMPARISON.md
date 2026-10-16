# Streaming Implementation & Pipeline Architecture Comparisons

## Goal: Transition to Continuous ASL -> Text
Evaluating potential development tracks evolving SignVox away from static label triggers toward continuous stream ingestion.

### A. Direct Landmark-to-Text Streaming Translation (SL2T Inspired)
*   **Methodology:** Raw MediaPipe sequences feed continuously into an Encoder-Decoder transformer. The model directly outputs continuous English tokens based on continuous input.
*   **Time to First Useful Text:** Medium. The network must establish context boundaries across multiple trailing sequences before emitting stable tokens, causing natural translation lag.
*   **Correction Behavior:** Highly volatile. Like voice dictation, the sentence end often alters the noun structure of the sentence beginning in ASL. Previously confirmed text chunks frequently rewrite natively upon expanding sequence history.
*   **Network Dependence:** Extremely high. Dense ML translation topologies typically exceed real-time rendering caps on web browsers/phones, mandating cloud fallback mechanisms (much like Google's SL2T architecture).
*   **Practicality:** Immensely difficult due to hardware limits. Demands monumental multi-modal dataset scaling.

### B. Gloss-to-Text Bridging via Sliding Window (EMNLP 2024 Reference)
*   **Methodology:** A pipeline containing two independent operations. An online Continuous Sign Language Classifier (CSLR) leveraging sliding windows (e.g. `Towards Online Continuous Sign Language Recognition and Translation, EMNLP 2024`) first maps frames strictly into ASL "Glosses" (fundamental root words). A secondary lightweight Language Model translates the Gloss sequence into grammatically sound English.
*   **Time to First Useful Text:** Fast (for Gloss). The initial sign maps rapidly. Translation into sentence structure remains withheld until logical grammar blocks finalize.
*   **Training Demands:** Requires heavily aligned datasets featuring exact temporal timestamp bounding for valid Gloss alignment, which is structurally harder to annotate.
*   **Feasibility:** Moderate. Permits SignVox to naturally expand its current `Isolated` engine into a `Sliding Window` Continuous Engine easily before bolting on an LLM structure behind it natively.

### C. Hybrid Edge Perception + Cloud Translation
*   **Methodology:** MediaPipe processing happens strictly locally resolving 130+ coordinate geometry per-frame accurately without compromising face streaming data out to transit pipelines. A lightweight internal `Pilot` sequence limits noise and provides offline command triggers, while continuous full sentences stream the coordinates into Cloud inferences (Cloud GPUs).
*   **Hardware Demand:** Low for the edge device (browser), scaling entirely to the cloud budget efficiently.
*   **Hallucination Risks:** Mitigated partially by local thresholding protections deciding *if* translation data is sent vs *idle* states internally blocking cloud network span.
*   **Feasibility:** Most viable progression. Limits user data compromises while allowing SignVox to integrate LLM translation boundaries without exploding on-device `.onnx` WASM payloads past 50MB.

### Implementation Recommendation
SignVox should target **Architecture B (Gloss-to-Text Bridging)** integrated inside a **Hybrid Edge-Cloud Transport (Architecture C).**
1. Train a lightweight Continuous Sign Recognizer outputting ASL Gloss bounding streams natively.
2. Route identified Gloss segments natively through a linguistic translation engine generating structured strings securely.
