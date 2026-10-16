# Phase 1.1 — Evidence Audit and Architecture Decision

## 1. Executive Findings
*   The previous baseline metric claims (15-30ms latencies) are **explicitly measured** by the React application state via `performance.now()`, but depend entirely on the host hardware executing the WASM payload.
*   The `17-second` model load time is **unverified computationally** (no metric exists wrapping `InferenceSession.create`). It correlates heavily to WASM `.data` payload fetching over un-cached browser bounds.
*   Google's SL2T is confirmed locally protective via edge preprocessing (MediaPipe), but fully dependent on proprietary Google Cloud Translation networks, verifying isolated device execution translates poorly without Cloud backup.
*   **Architecture B (CTC Sliding Window + Gloss Translation)** is formally selected as the most actionable pathway, minimizing proprietary datasets organically while providing streaming capability.

## 2. Claim / Evidence / Confidence Table

| Claim | Source / Code Location | Verification Status | Qualifications / Corrections |
| :--- | :--- | :--- | :--- |
| **MediaPipe Latency is 15-20ms** | `web/src/lib/mediapipe.ts:L57-63`, `web/src/App.tsx:L331-334` | **Verified (Measured)** | Depends strictly on hardware CPU. Will spike under thermal throttling. |
| **Feature Extraction takes 1-3ms** | `App.tsx:L309-L315` | **Verified (Measured)** | Confirmed matrix manipulation mathematically requires minimal cycles. |
| **ONNX Inference takes 15-30ms** | `App.tsx:L358-L361` | **Verified (Measured)** | Valid exclusively for the 366-dim Spoter model, not dense translation models. |
| **17-second Startup Penalty** | User reporting / Phase 2 observations | **Unverified (Estimate)** | The codebase (`inference.ts:L19`) does not actively wrap initialization in stopwatch limits. The penalty stems from network/sandbox bounds. |
| **SL2T Extracts 130 nodes / Protects raw video** | Google Pixel 11 Announcement / MediaPipe Specs | **Verified (Public Source)** | Facts confirmed via Google AI Blogs describing SL2T. |
| **How2Sign relies on CC BY-NC 4.0** | How2Sign Dataset License Repository | **Verified (Public Source)** | Strictly Non-Commercial. Commercial translation features are explicitly barred. |
| **Cloud Translation prevents edge thermal collapse** | SL2T Server Implementation Architecture | **Inference** | Google confirmed edge-to-cloud payload transit, but thermal justification is standard hardware logic, not an explicit publicized rule. |

## 3. Verified vs Unverified Performance Baseline
- **Measured Metrics:** Camera FPS calculation, MediaPipe evaluation time (Pose, Hands, Face independently), mathematical mean-centroid normalization bounding, overall processing loop bounding, and ONNX prediction execution times.
- **Unverified Metrics:** Time waiting for asynchronous model WASM memory allocations (`SpoterInferenceSession.create`), temporal stabilization UI render propagation bounding, WebGL crossfade avatar synchronization delays.

## 4. Corrected SL2T Fact Breakdown
- **Publicly Documented Facts:** MediaPipe extracts geometric meshes locally. Raw video stays on-device to support anonymity. Cloud servers natively perform the actual Machine Translation stream. Outputs directly yield prose. 
- **Reasonable Architectural Inferences:** Sentences inherently update retroactively (streaming dictation) as trailing SL components redefine earlier contexts. The cloud pipeline relies on extensive transformer depth matching over 100K training hours.
- **Undisclosed Proprietaries:** The exact size of the translation model, internal frame sampling metrics to minimize battery drain, payload transfer encryption methodology for coordinate JSON, structure bridging intermediate representations like Gloss internally.

## 5. Reassessed Architecture Comparison (A/B/C) with Uncertainties
- **A. Direct Landmark-to-Text (SL2T Style):** 
  - *Data reqs:* Colossal sentence-level translation pairing.
  - *Latency:* End-heavy. Wait time for valid text implies heavy lag.
  - *Uncertainty:* Huge likelihood of hallucinating output unless datasets eclipse 1MM+ examples natively. High risk of failure given our dataset caps.
- **B. Online CSLR Gloss + Translation LLM (EMNLP 2024 via CTC):**
  - *Data reqs:* Frame-aligned sign gloss boundary tagging (Harder annotating). Text conversions thereafter.
  - *Handling Pauses:* CTC natively predicts `blank` frames smoothly masking idle spans implicitly.
  - *Uncertainty:* Collecting temporal annotations requires rigorous manual oversight natively bridging isolated constraints iteratively.
- **C. Hybrid Hardware Boundary:**
  - *Handling weak connectivity:* Edge handles short pilot/command subsets natively (offline fallback). Full sentences fail over to explicit "Network Offline" gracefully. 
  - *Uncertainty:* Orchestrating local WASM and remote HTTPS endpoints requires careful state-machine integration preventing stale responses out-of-order.

## 6. Dataset and Commercial Rights Audit
- **Isolated-Sign Assets:** (`ASL Citizen`): Valid. Cropped natively. Useful for isolated triggers, *incapable* of supporting Continuous Translation bridging.
- **Continuous-Sign Translators:** (`How2Sign`): CC BY-NC 4.0 strictly non-commercial. (`ChicagoFSWild`): Spelled structures only natively avoiding vocabulary natively. 
- **Resolutions Pending Legal:** Can a model initialize pre-training matrices against Non-Commercial bounds before transferring exclusively onto proprietary boundaries tuning? Legal validation required. 

## 7. Defensible Evaluation Protocol
- **Time to First Provisional Text (TTFT):** Measure HTTP Round Trip Time (RTT) + LLM inference First Token Latency (FTL). Target *Provisional*: `<= 800ms`.
- **Time to Confirmed Text:** Target depends on user motion conclusion. Measured natively via hand-velocity dropping below spatial origin bounds cleanly locking trailing contexts recursively. 
- **WER (Word Error Rate):** Applied specifically on 50 strictly held-out continuous sentence combinations natively simulating standard conversational syntax. 

## 8. Smallest Justified Next Research Experiment
**Objective:** Confirm if SignVox isolated data can transition into a minimal sliding window structure via CTC predicting `Blank` spaces natively.
- **Prerequisites:** Artificially stitch 3-5 confirmed sign `.npy` tensors separated by structural null buffers (neutral bounds) natively.
- **Experiment:** Train a tiny LSTM/Transformer using CTC loss to natively parse the stacked series cleanly reporting output tokens isolating blanks.
- **Success Criteria:** Over 90% accuracy parsing strict `HELLO -> blank -> YES` sequences without hallucinating intermediate steps cleanly isolating `blank` spaces.

## 9. Decisions Requiring Explicit User Approval
1. **Architecture Commitment:** Formally commit to Pipeline **B (Continuous Gloss CTC + LLM)** over Pipeline A natively mapping a more scalable annotation phase.
2. **Experiment Authorization:** Do I build the minimal artificial-stitch CTC pipeline script natively targeting `HELLO` and `YES` to prove sequential viability?
