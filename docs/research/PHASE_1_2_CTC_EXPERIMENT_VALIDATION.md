# Phase 1.2 — Validation of the CTC Experiment Proposal

## 1. CTC Blank Mechanisms & Structural Limitations
Connectionist Temporal Classification (CTC) utilizes a `blank` symbol separating identical repeated classes and aligning variable-length input frames against shorter target sequences natively.
- **Why it is not an IDLE detector:** A CTC `blank` is trained specifically to bridge intra-sign transitions and squelch identical consecutive predictions natively, *not* to detect global "user is no longer signing" states. 
- **Rejection & Segmentation Failure:** CTC lacks a structural definition of "noise". Unless explicitly trained with continuous examples of idle behavior tagged as blanks natively, it will map random continuous resting motions toward whichever signs physically match the geometry mathematically closest, resulting in hallucinatory false spikes rapidly rather than confident rejection natively. Continuous segmentation requires distinct language-boundary mapping, which CTC inherently lacks.

## 2. Assessment of Artificial-Stitch CTC Proposal
The previous hypothesis suggested concatenating isolated `HELLO` and `YES` arrays separated by null/neutral vectors natively simulating sequences.
- **What it answers:** It strictly validates basic sequence-to-sequence software deployment. It guarantees that the loss function decreases computationally while learning basic multi-token generation limits computationally.
- **What it fails to establish:** **Coarticulation**. Humans blending `HELLO` into `YES` skip natural "return-to-neutral" bounds visually smearing the gestures natively. Artificial strings implicitly memorize hard neutral stops implicitly failing real-world sequences gracefully.
- **Synthetic Shortcuts / Leakage:** If the network is trained on joined isolated clips, it learns the specific sudden teleportation boundaries between frames as the determining logic identifying word splits dynamically, completely invalidating human organic test results.
- **Valid Test Requirement:** Only an explicitly captured continuous phrase dynamically performed organically (`"Hello, yes I am."`) cleanly passing independent, un-memorized evaluation boundaries justifies progression securely.

## 3. Minimum Evidence for Evaluating Continuous Recognition
An evaluation proving a model resolves conversational continuous sequences mandates:
1. **Target Modality:** Authentic organic, continuously recorded phrasing natively inclusive of true physical coarticulation spanning multiple signs visually seamlessly without cuts.
2. **Dataset Isolation:** Strict decoupling separating independent subjects across Train, Validation, and Test explicitly assuring no individual's signing bias infects evaluation topologies actively.
3. **Conversational Variance:** Metrics capturing accuracy natively passing across resting delays (IDLE periods), pauses, and out-of-vocabulary instances robustly returning `NULL` actively.
4. **Relevant Scoring Sequences:** Isolated classification accuracy collapses here natively. Sequence-based metrics including Word Error Rate (WER), Insertion Errors (false text mapping over pauses), and Deletion Errors genuinely quantify performance structurally.

## 4. Reassessment of Available Annotations and Prerequisites
- **Isolated Assets (`ASL Citizen`):** Excellent robust definitions bounding individual concepts natively, but absolutely invalid natively establishing continuous sequence bridges structurally.
- **Continuous Sets (`How2Sign`):** High-quality continuous data bounds organically mirroring conversation structurally paired with raw video and captions natively. _Limit:_ Verified CC BY-NC 4.0 limits natively block commercial deployment. Legal review structurally requires bounding whether fine-tuning models initialized off these structures infringes limits definitively.
- **Prerequisite Focus:** Data dependencies necessitate no explicit numeric milestone (e.g. 10,000 sentences natively). A tiny proprietary sample accurately mirroring organic boundaries suffices solely to evaluate topology integrations before expanding.

## 5. Objective Architecture Re-Evaluation: A vs B
- **Direct Landmark-to-Text (A):**
  - *Evidence Demanded:* A massive corpus translating diverse spatial sequences natively into explicit full English without glosses fundamentally.
  - *Feasibility:* Low for limited teams natively due to monumental text permutations naturally occurring. 
- **Continuous Gloss + LLM Translation (B):**
  - *Evidence Demanded:* Explicit timestamp labeling manually tagging start/end limits of discrete gloss bounds within continuous streams natively verifying the intermediate boundary.
  - *Feasibility:* Forces rigorous explicit annotation overhead physically defining intermediate representations gracefully slowing dataset creation intrinsically. 
- **Verdict Placeholder:** Neither path proves exclusively superior organically yet natively unless concrete structural boundaries resolve legal dataset acquisition inherently. 

## 6. Smallest Defensible Next Experiments (Staged Rollout)
We must explicitly isolate basic engineering tests away from biological evaluations.

### Stage I: Synthetic Engineering Smoke Test
- **Purpose:** Validate tensor IO structures, library compilation logic, inference sequence shapes, and CTC/Attention decoding math strictly executing without memory faults natively across the pipeline boundaries.
- **Prerequisites:** Artificially stitch existing ASL isolated buffers.
- **Success Criteria:** Over-fit memorization locally proving gradients propagate sequentially parsing the combined vectors natively producing multi-token bounds smoothly.
- **Limits / Decision:** Proves *mathematical viability exclusively*, not biological recognition structurally. Clears authorization for pipeline assembly sequentially.

### Stage II: Small Continuous Organic Sequence (Natural-Sign Learning)
- **Purpose:** Identify if the defined network boundaries successfully track true temporal boundary blending cleanly tracking coarticulation gracefully.
- **Prerequisites:** Record exactly 15–20 proprietary continuous phrases (using webcam organically) defining real `HELLO YES NO` variations cleanly tracking explicit transitions organically.
- **Success Criteria:** Independent separation proving the network natively predicts `HELLO` fading into `YES` without hallucinating false stops internally reducing WER limits favorably.
- **Limits / Decision:** Approves the model topology natively learning human movement safely. Progresses into mass scaling inherently. 

### Stage III: Real-world Conversation Evaluation
- **Purpose:** Generalize continuous models natively predicting live varied subjects performing unscripted boundaries mapping random pauses properly checking noise suppression organically.
- **Prerequisites:** Minimum 10+ held-out subjects naturally bridging vocabulary boundaries structurally over live bounds naturally. 
- **Success Criteria:** Insertion/WER bounds measuring below exact explicit limits rejecting dropped sequences correctly returning null natively.
- **Limits / Decision:** Formally approves continuous operations directly for commercial rollout natively over live integrations seamlessly.
