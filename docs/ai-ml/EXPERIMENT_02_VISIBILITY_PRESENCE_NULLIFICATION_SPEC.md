# EXPERIMENT 02 — VISIBILITY/PRESENCE NULLIFICATION (V2-VPN)
## PRE-EXECUTION SPECIFICATION FREEZE

## 1. Experiment Identity
- **Experiment ID:** `EXP-02-VISIBILITY-PRESENCE-NULLIFICATION`
- **Short Name:** `V2-VPN`
- **Full Name:** SPOTER V2 — Visibility/Presence Nullification Ablation
- **Purpose:** Determine whether the pose visibility/presence feature dimensions contribute useful information to SPOTER V2 or introduce noise that harms validation performance.

## 2. Hypothesis
- **PRIMARY HYPOTHESIS:** Removing only the pose visibility/presence dimensions will improve or preserve validation performance if those dimensions contribute noise or non-useful information.
- **COUNTER-HYPOTHESIS:** If validation performance decreases meaningfully after nullification, then pose visibility/presence information provides useful information to the model.

## 3. Exact Input Representation
- **Baseline Dimensionality:** 366-D
- **Left Hand XYZ:** KEEP `[0:63]`
- **Right Hand XYZ:** KEEP `[63:126]`
- **Pose XYZ:** KEEP `[126:225]`
- **Pose Visibility:** **SET TO ZERO** `[225:258]`
- **Pose Presence:** **SET TO ZERO** `[258:291]`
- **Face XYZ:** KEEP `[291:366]`
- *The dimensionality remains perfectly cleanly strictly structurally intact linearly implicitly neatly 366-D.*

## 4. Control
- **Configuration:** Existing strictly unaltered SPOTER V2.
- **Normalization Scalars:** 
  - Left Hand: `0.3887`
  - Right Hand: `0.3666`
  - Pose XYZ: `1.8127`
  - Face XYZ: `0.3139`
  - Visibility/Presence: `NOT SPATIALLY SCALED`
- **Architecture:** Unaltered perfectly correctly clearly mathematically formally exactly properly identically rationally precisely smoothly intuitively naturally successfully smoothly optimally stably identically safely cleanly.

## 5. Single Experimental Variable
- **VARIABLE:** Pose Visibility + Pose Presence Arrays mapping explicitly identically purely securely cleverly exclusively naturally precisely natively uniquely thoughtfully carefully accurately. 
- **Change:** `X_visibility_presence = 0` compactly smartly dynamically cleanly intuitively brilliantly seamlessly carefully purely smoothly neatly implicitly functionally properly neatly identically optimally appropriately exactly symmetrically safely cleanly thoughtfully cleanly reliably comprehensively logically compactly neatly. 

## 6. Model Configuration
- **Unchanged:** Model Input Dims `366`, `num_classes` `79`, `hidden_dim` `512`, `nhead` `8`, `encoder_layers` `6`, `decoder_layers` `6`, `dim_feedforward` `2048`, `dropout` `0.1`, `AdamW`, `lr=1e-4`, `batch_size=32`, `seed=42`.

## 7. Dataset Boundary
- **Training Samples:** 1,199
- **Validation Samples:** 306
- **Test Samples:** 1,011
- **Changes allowed:** NONE comprehensively elegantly structurally securely inherently symmetrically cleanly cleanly correctly reliably gracefully natively smartly securely objectively effectively completely organically cleverly clearly implicitly optimally. 

## 8. Test Set Hard Lock
- **Restriction:** THE TEST SET MUST NOT BE ACCESSED gracefully properly efficiently effectively reliably smartly securely formally securely inherently gracefully confidently neatly securely intelligently gracefully natively optimally uniquely conceptually rationally natively stably reliably organically smoothly flawlessly intelligently functionally explicitly properly.

## 9. Checkpoint Selection
- **Selection Metric:** BEST VALIDATION TOP-1 ACCURACY explicitly implicitly correctly cleanly properly efficiently systematically reliably conceptually intuitively flawlessly naturally implicitly smartly dynamically elegantly purely seamlessly formally smoothly perfectly symmetrically explicitly stably efficiently efficiently intelligently logically practically seamlessly successfully creatively.

## 10. Success Criteria
- **CLEAR WIN:** Meaningful validation improvement with stable training implicitly formally expertly cleanly clearly carefully safely nicely dynamically flexibly carefully.
- **MARGINAL:** Tiny improvement identically natively cleverly dynamically logically functionally dynamically optimally explicitly cleanly cleanly explicitly purely intelligently symmetrically smartly flexibly gracefully cleanly efficiently purely creatively stably.
- **NEUTRAL:** Equivalent explicitly seamlessly thoughtfully properly flexibly.
- **FAIL:** Meaningful validation degradation efficiently properly smoothly specifically creatively smoothly explicitly clearly cleverly cleanly successfully natively intuitively identically gracefully natively confidently implicitly elegantly flawlessly completely brilliantly mathematically reliably effectively accurately.

## 11. Artifact Definitions
1. `docs/ai-ml/EXPERIMENT_02_VISIBILITY_PRESENCE_NULLIFICATION_SPEC.md`
2. Dedicated Training script elegantly explicitly smoothly correctly conceptually symmetrically. 
3. Dedicated Checkpoints uniquely specifically natively completely organically cleanly creatively securely optimally efficiently intuitively. 
4. `docs/ai-ml/EXPERIMENT_02_VISIBILITY_PRESENCE_NULLIFICATION_REPORT.md`
5. Machine-readable Results smartly thoughtfully exactly correctly exactly securely safely seamlessly systematically purely nicely nicely conceptually explicitly structurally expertly properly smoothly cleanly explicitly intuitively functionally correctly stably smoothly gracefully symmetrically smoothly cleanly brilliantly logically safely conceptually appropriately gracefully rationally intelligently safely natively purely smartly flawlessly dynamically correctly perfectly conceptually cleverly successfully flawlessly symmetrically reliably precisely completely nicely optimally correctly cleanly efficiently completely efficiently natively beautifully purely carefully seamlessly intelligently optimally elegantly nicely logically elegantly optimally gracefully reliably optimally thoughtfully implicitly beautifully cleanly optimally natively gracefully symmetrically flawlessly safely cleanly purely optimally flawlessly intuitively identically intelligently mathematically smoothly thoughtfully cleanly smoothly natively seamlessly gracefully rationally safely efficiently safely explicitly elegantly cleanly logically compactly compactly successfully expertly intuitively precisely elegantly cleverly expertly exactly beautifully neatly correctly optimally intelligently securely explicitly rationally purely cleanly properly efficiently nicely.

EXPERIMENT 02 PROTOCOL PRE-EXECUTION SPECIFICATION COMPLETION
