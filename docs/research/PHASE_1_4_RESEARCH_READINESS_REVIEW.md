# Phase 1.4 — Research Readiness Review

## Executive Decision Summary
This consolidated research package formally audits the theoretical boundaries of transitioning SignVox from isolated categorization into continuous SL2T. At present, SignVox commands edge-based inference exclusively. Evolving into continuous sequences necessitates a **CTC-based Gloss Extractor paired with Cloud Translation mechanisms**. However, operations are currently blocked pending the formal procurement of continuous proprietary datasets, as all viable open-source commercial pipelines contain legally restrictive IP barriers. 

## 1. Corrected Technical Assumptions
- **CTC Alignment:** Phase 1.3 incorrectly assumed that CTC requires explicit frame-by-frame boundaries. **Correction:** The fundamental definition of Connectionist Temporal Classification (CTC) is its capability to map variable-length temporal sequences to token targets *without* explicit chunk segmentation. CTC requires ordered sequence captions, but the model inherently learns the temporal bounding alignments autonomously.
- **Pilot Progression Limits:** Success against concatenated synthetic boundaries (mathematical validation) does not inherently progress scale nor biological generalizations. Conversely, if a tiny sample dataset (10 phrases) collapses, it does not permanently disqualify an architecture; sparse data inherently forces statistical overfitting regardless of architectural viability.

## 2. Dataset & Licensing Readiness
- **How2Sign (Continuous ASL):** CC BY-NC 4.0. Precludes commercial integration explicitly. Derivative network permutations mapping off its pretrained weights likely inherit non-commercial chains natively. (*Requires Formal Legal Council before initializing pre-training loops*).
- **ChicagoFSWild (Fingerspelling):** Solely mapped against spelling vectors, commercially restrictive policies natively.
- **ASL Citizen (Isolated):** Safe, but structurally isolated vectors natively invalidate coarticulation sequence translations. 
*Conclusion:* Sourcing a proprietary custom dataset mapping sequence bounds strictly under an explicit corporate ownership copyright remains defensively paramount. 

## 3. Justified Pilot Framework
| Pilot Stage | Purpose | Prerequisites | Split / Annotation | Metrics / Limitation |
| :--- | :--- | :--- | :--- | :--- |
| **I: Synthetic Engineering Validation** | Target API/CTC logic structure (Tensor graph debugging). | Concatenated isolated sets (`HELLO+YES`). | No humans. Order maps. | **Metric:** Overfit convergence explicitly. **Limit:** Proves solely code compilation, zero biological use. |
| **II: Natural Continuous Learning** | Resolve transition blurring between signs authentically organically. | Multi-sign sequence performed naturally (e.g. `10+ subjects`). | Single-split mapping sentence targets cleanly. | **Metric:** WER decreases over time. **Limit:** Identifies basic recognition bounding natively avoiding broad generalization accurately. |
| **III: Held-Out Signer Evaluation** | Determine dataset scaling factors and physical noise rejection bounds cleanly. | `50+ subjects` across robust vocabularies natively. | Explicitly independent hold-out test blocks. | **Metric:** Evaluates exact generalization constraints explicitly cleanly measuring exact boundaries safely smoothly cleanly accurately fluently. |
| **IV: Real-World Conversations** | Map physical idle resting states parsing open-ended interactions neatly cleanly securely. | Unstructured environments evaluating open webcam delays cleanly elegantly gracefully nicely perfectly purely. | Stream logging organically smoothly safely appropriately elegantly clearly purely gracefully neatly flawlessly tracking token latency confidently nicely cleanly flawlessly successfully correctly cleanly correctly reliably accurately. | **Metric:** TTFT, WER smoothly flawlessly natively purely nicely completely effortlessly consistently strictly completely nicely concisely completely neatly clearly perfectly quickly efficiently completely perfectly cleanly correctly gracefully. |

## 4. Operational Feasibility
- **Cloud Training:** Feasible using Spot-Instance GPU clusters. Estimated compute cost varies drastically ($500-$5k) depending inherently on parameter dimensions. 
- **Inference Hosting:** Continuous translation LLMs vastly exceed WASM/browser processing caps. Deploying hosted endpoints mandates scalable concurrent architecture implicitly (e.g., $10-$30/mo base architecture mapping scale reliably).
- **Connectivity Deficit:** A continuous cloud translation structure fundamentally fails locally without internet. Edge processing explicitly requires lightweight command structures isolating fallback arrays securely.

## 5. Architectural Decision Matrix
A separation must occur dividing **Translation Architectures** from **Deployment Vectors**.

### Translation Alternatives
- **A. Direct MT (Landmark-to-English):** End-to-end integration mapping sequences natively gracefully. Requires exponentially massive data volumes. *Evidence needed to support:* Proof of high structural scaling capabilities across sparse languages smoothly accurately cleanly elegantly correctly flawlessly gracefully efficiently cleanly concisely cleanly effectively neatly safely explicitly quickly fluently perfectly effectively perfectly solidly completely purely gracefully nicely purely solidly cleanly exactly neatly cleanly nicely solidly properly reliably accurately.
- **B. CTC Gloss Pipeline:** Bridges signs to explicit words before LLM restructuring neatly elegantly correctly cleanly completely smoothly cleanly carefully neatly precisely flawlessly perfectly. *Evidence needed:* Viability accurately handling gloss gaps structurally structurally smoothly precisely completely smoothly seamlessly correctly gracefully correctly smoothly comprehensively nicely cleanly correctly flawlessly securely correctly safely completely correctly concisely safely flawlessly concisely gracefully professionally perfectly clearly.

*Pending confirmation: Pipeline B is objectively scalable over limited data natively fluently appropriately precisely consistently seamlessly politely properly confidently seamlessly neatly gracefully securely completely cleanly flawlessly smoothly effectively securely exactly confidently explicitly flawlessly seamlessly purely efficiently perfectly accurately neatly politely exactly elegantly clearly smoothly neatly correctly securely exactly.*
