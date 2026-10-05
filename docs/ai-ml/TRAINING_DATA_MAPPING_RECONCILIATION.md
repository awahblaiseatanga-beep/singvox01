# Vocabulary Mapping Reconciliation

## 1. Normalization Rules
To map stringently against raw CSV inputs without semantic hallucination, a standardized case and syntax normalization function evaluated classes securely:
- Case matching (`g.upper()`)
- Apostrophe removal (`'` -> ``)
- Hyphen conversion (`-` -> ` `)
- Space collapse (`  ` -> ` `)

## 2. 21-Class Reconciliation Table
| Canonical Class | Normalized Key | Source Matches | Status |
|---|---|---|---|
| THANK-YOU | THANK YOU | None | NO_SOURCE_MATCH |
| DON'T-UNDERSTAND | DONT UNDERSTAND | None | NO_SOURCE_MATCH |
| BABY | BABY | None | NO_SOURCE_MATCH |
| WANT | WANT | None | NO_SOURCE_MATCH |
| TEACH | TEACH | None | NO_SOURCE_MATCH |
| STORE | STORE | None | NO_SOURCE_MATCH |
| HOSPITAL | HOSPITAL | None | NO_SOURCE_MATCH |
| DOCTOR | DOCTOR | None | NO_SOURCE_MATCH |
| NIGHT | NIGHT | None | NO_SOURCE_MATCH |
| WHAT | WHAT | None | NO_SOURCE_MATCH |
| HOW | HOW | None | NO_SOURCE_MATCH |
| FOOD | FOOD | None | NO_SOURCE_MATCH |
| EAT | EAT | None | NO_SOURCE_MATCH |
| DRINK | DRINK | None | NO_SOURCE_MATCH |
| EMERGENCY | EMERGENCY | None | NO_SOURCE_MATCH |
| COMMUNICATE | COMMUNICATE | None | NO_SOURCE_MATCH |
| DEAF | DEAF | None | NO_SOURCE_MATCH |
| SPEAK | SPEAK | None | NO_SOURCE_MATCH |
| FINE | FINE | None | NO_SOURCE_MATCH |
| CALL | CALL | PHONE | REQUIRES_REVIEW |
| PHONE | PHONE | PHONE | REQUIRES_REVIEW |

## 3. CALL / PHONE Collision Analysis
Both canonical `CALL` and `PHONE` legally inherit the string `"PHONE"` as an active alias within the frozen `asl100_vocabulary.json`. Scanning the raw ASL Citizen dataset reveals that the sole available mapped string is precisely `"PHONE"` (which contains 90 videos). Because there is no deterministic secondary variable in the dataset schema to filter `"PHONE"` instances into semantic `CALL` vs `PHONE` intents organically, ANY algorithmic assignment would be entirely unscientific. Both classes have been structurally flagged as `REQUIRES_REVIEW` and safely stripped of all candidate videos to prevent hallucinated logic boundaries.

## 4. Deterministic Mapping Config
Generated JSON Dictionary saved natively to: 
`ai/sign-recognition/config/asl100_asl_citizen_mapping.json`

## 5. Remaining Ambiguous & Unavailable Classes
- **Unavailable (0 datasets):** 19 classes
- **Ambiguous (`review`):** 2 classes (`CALL`, `PHONE`)
- **Total Valid Classes:** 79 classes

## 6. Coverage Totals
- **Mapped Classes:** 79 classes
- **Total Candidate Videos Reconstructed:** 2,516 videos 

## 7. Split Totals
- **Train:** 1,199 videos
- **Validation:** 306 videos
- **Test:** 1,011 videos

## 8. Signer-Disjoint Verification
- **Total Unique Signers:** 46
- **Status:** **PASS** (100% mutual exclusion confirmed between Train, Val, and Test signers).

## 9. Delta from Phase 1
- **Class-Count Difference:** 0 (Remains 79 mapped natively)
- **Video-Count Difference:** 0 (Remains 2516 available).
*Analysis:* The aggressive syntax normalization confirmed what Phase 1 detected: there are no "hidden" source glosses available under simple grammatical errors. The 19 classes simply do not organically exist in the ASL Citizen arrays.

## 10. Historical Comparison
**Historical baseline:** 81 classes, 2,606 videos.
**Current exact mapping:** 79 classes, 2,516 videos.
**Reconciliation:** The explicit mathematical delta (2 classes, exactly 90 videos) maps undeniably precisely to the ambiguous `CALL` and `PHONE` collision. The historical subset arbitrarily/semantically assigned these 90 videos, masking the fundamental vocabulary ambiguity. Banning non-deterministic guessing mathematically locked the recovery specifically matching the historical baseline, with the exclusive scientific exclusion of the compromised `PHONE` subset.

## 11. Exact Mapping Configuration Path
`ai/sign-recognition/config/asl100_asl_citizen_mapping.json`

## 12. Recommendation for Manifest Generation
Using the established `asl100_asl_citizen_mapping.json` as the exclusive dataset constraint dictionary formally authorizes moving to dataset extraction. The 90 ambiguous videos functionally must remain excluded globally until manual annotation formally distinguishes `CALL`/`PHONE`.

---
**TRAINING DATA MAPPING — RECONCILED**
