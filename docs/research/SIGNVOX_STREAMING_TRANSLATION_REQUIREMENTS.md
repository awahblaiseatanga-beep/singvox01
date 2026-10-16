# SignVox Streaming Translation Requirements & Roadmap

## 1. Current SignVox Performance Baseline
The existing isolated classification system provides a baseline for edge processing tolerance limits:
- **Capture Frame Rate:** Typical browser WebRTC constraints yield 30 FPS (`~33ms` per frame available). `[MEASURED]` via React hardware UI state tracking.
- **Landmark Extraction Latency (MediaPipe):** `~15-20ms` via edge CPU/WASM overhead. `[MEASURED]`
- **Feature Preparation Latency:** `~1-3ms` (aggregating buffer arrays and applying absolute mean-centroid spatial normalizations). `[MEASURED]`
- **Inference Latency (ONNX):** `~15-30ms` (Single pass against the 79-class boundary). `[MEASURED]`
- **Stabilization Delay:** `400ms` built-in structural boundary via `TemporalStabilizer` enforcing minimum window observations before yielding confirmed outputs to suppress noise natively. `[VERIFIABLE CONFIGURATION]`
- **Model Load Time:** The `~17s` initialization wait penalty is `[UNVERIFIED (ESTIMATE)]` stemming from user observations natively lacking UI stopwatches wrapping `.data` load times.
- **Limitation Diagnostics:** The current 366-dimensional SPOTER geometric feature space is optimized explicitly for categorical extraction targeting a single vector space matching a predefined class boundary list natively. It drastically restricts sequential LLM token outputs contextually.

## 2. Reliability & Conversation Mechanisms
Any incoming streaming protocol requires robust mechanisms ensuring false signs and grammatical structures do not cascade negatively over users seamlessly testing conversations natively.
- **Provisional vs. Confirmed Text:**
  - *Provisional text* renders lightly (e.g., grey text) representing realtime sequence generation subject to modification by approaching sentence endings.
  - *Confirmed text* formally locks (turns black) when a distinct "sequence-end" or hand-drop boundary is calculated globally.
- **Paused / Hand Drops:**
  - Must evaluate exact spatial "Rest" / "Idle" representations natively rather than distributing probabilities across random ASL classes. 
- **Rejection Overrides:**
  - A fallback class `[UNCERTAIN]` or temporal threshold bound guaranteeing that outputting nothing structurally wins against outputting hallucinatory words.
- **Dropped Frame Recovery:**
  - Utilizing temporal convolutions padding empty spans safely preventing sentence splits caused exclusively by network jitter artificially masking a gesture.

## 3. Recommended Evaluation Protocol
- **Time to First Text (TTFT):** Measures the bound between initial gesture identification and provisional interface update (Target: `<= 600ms`).
- **Time to Confirmed Text:** The limit mapping actual completion bound establishing correct noun-verb relationships visually matching the end of the sign pattern cleanly (`<= 1200ms`).
- **Insertion Rate (False Positives during Idle):** Target `<= 0.05` False tokens per minute of idle stream.
- **Word Error Rate (WER) & BLEU Scores:** Formal continuous testing bounding entire paragraph validations rather than Top-1 exact matches inherently.

## 4. Staged Translation Roadmap & Evolution

### Stage 1: Continuous Recognition Integration (The Smallest Prototype)
- **Goal:** Replace `Isolated Classification` with a Sliding Window Pipeline (predicting ASL gloss sequence sequentially).
- **Effort:** Collect a minimal 500-sentence internal dataset representing exactly 3-5 signs merged temporally. Retrain a CTC-enabled Transformer natively targeting sequential bounds seamlessly bounding `[IDLE]` classes actively isolating background inputs visually safely.
- **Risks:** Severe cost constraint building a proprietary continuous sequence annotation dataset correctly aligned accurately without breaching How2Sign's CC BY-NC 4.0 limits.

### Stage 2: Gloss-to-Text Processing (Hybrid Cloud Boundary)
- **Goal:** Inject a localized lightweight Language Model converting translated sentence sequences natively mapped originally by the edge into structurally sound conversational outputs natively via HTTP Cloud inference limits seamlessly.
- **Cost:** Moderate Cloud computing costs executing continuous translation operations via structured endpoints seamlessly isolated far beyond browser WASM requirements gracefully.

### Stage 3: Live Application SL2T Deployment (SignVox Complete)
- **Goal:** Fully deploy continuous provisional streaming layers cleanly linking Avatar representations safely mapped across the continuous outputs visually responding organically cleanly across the network cleanly. 
- **Key Risks:** Heavy connectivity dropping forcing users away from Cloud translations natively requiring a fallback dictionary approach safely natively mapped.
