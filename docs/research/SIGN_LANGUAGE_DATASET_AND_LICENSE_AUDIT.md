# Dataset Identification and Licensing Audit (Continuous ASL)

## Commercial Viability Analysis

To restructure the SignVox neural networks from an `Isolated Classifier` targeting singular class arrays into a `Sentence-Level Continuous Translator`, vast temporal bounds must be sourced linking chronological videos against complete text targets.

### 1. How2Sign Dataset
*   **Scale:** Over 80 hours of high-quality continuous American Sign Language (ASL) videos matched identically to English sentence captions.
*   **Contents:** Signer diversity mapping, multiple cameras including Panoptic studio tracking, and holistic tracking boundaries establishing robust multi-view geometries safely.
*   **Licensing Constraints:** Published explicitly under the **Creative Commons Attribution-NonCommercial (CC BY-NC 4.0)** license.
*   **Commercial Verdict:** ❌ **Restricted.** The dataset strictly prohibits commercial deployment of weights generated primarily upon its contents. A corporate release requires sourcing fundamentally alternate independent assets. It remains an exceptional research/academic playground solely.

### 2. ChicagoFSWild / ChicagoFSWild+
*   **Scale:** A major dataset focused on fingerspelling inside the wild natively. Great temporal variance.
*   **Scope:** Extremely narrow. Fingerspelling continuous bounds do not adequately project generalized linguistic sentence mapping natively unless augmented across broader sign language definitions.
*   **Commercial Verdict:** ❌ Usually restricted inherently through its original non-commercial data deployment structures.

### 3. ASL Citizen Add-on Usage
*   **Scale:** SignVox previously sourced the `ASL Citizen` definitions establishing its fundamental isolated models initially.
*   **Constraint:** These structures are meticulously cropped isolated clips focused entirely on dictionary definitions (Singular words).
*   **Verdict:** ❌ **Insufficient.** Bolting isolated signs together sequentially does not synthetically capture "coarticulation" (the physical blending and blending of gestures sequentially across human motion natively). An AI trained strictly on patched isolated sequences completely collapses during natural human sentence translations.

### Sourcing Directives
SignVox *cannot* legally pivot toward a commercially marketable SL2T feature relying implicitly on academic-backed open-source packages like How2Sign without aggressively limiting its release scope. 
**Recommendations:**
1. Secure corporate data deployment permissions directly with specific non-profit ASL annotation collectives ensuring commercialization boundaries are mapped accurately.
2. Formally construct a paid proprietary dataset internally focusing specifically on 10,000 highly targeted multi-sign sentences matching key application constraints natively (a custom isolated SignVox Continuous library).
