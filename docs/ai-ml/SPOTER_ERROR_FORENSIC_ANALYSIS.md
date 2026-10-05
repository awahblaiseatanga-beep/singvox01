# SPOTER ERROR FORENSIC ANALYSIS

## 1. Executive Summary
This report forensically analyzes the 298 errors securely output by the baseline SPOTER model on the held-out test split using standard configurations. We investigate observable structures in validation metrics tied to completion rates, subclass distribution, participant biases, and structural sequential alignment.

## 2. Test Evaluation Context
- Test Samples Evaluated: 1011
- Active Classes Inspected: 79
- Isolated Errors Recorded: 298
- Checkpoint: `spoter_baseline_best_val_acc_checkpoint.pt`

## 3. Error Distribution
Out of 1011 samples evaluated independently, 298 were confirmed incorrectly mapped, forming an aggregate 29.48% global error rate exclusively for detailed post-mortem reporting here.

## 4. Top Confusion Pairs
The ranking specifies systematic confusion pairs (True Class → Predicted Class). High frequencies heavily implicate structural ambiguity across specific spatial mappings.
1. **NEED** → **YES**: 8 errors (2.7%)
2. **HELLO** → **FATHER**: 5 errors (1.7%)
3. **HOT** → **BAD**: 4 errors (1.3%)
4. **PLEASE** → **HAPPY**: 4 errors (1.3%)
5. **NAME** → **FRIEND**: 4 errors (1.3%)
6. **GIVE** → **GOOD**: 4 errors (1.3%)
7. **LIKE** → **PLEASE**: 4 errors (1.3%)
8. **SIGN** → **WHEN**: 3 errors (1.0%)
9. **NO** → **YES**: 3 errors (1.0%)
10. **SORRY** → **ME**: 3 errors (1.0%)

## 5. Per-Class Failure Analysis
### Top 5 Smallest Accuracies (Weakest Core Classes)
- **NEED**: 16.7% (10/12 incorrect) [Train Volumes: 15 samples over 15 signers]
- **GIVE**: 18.2% (9/11 incorrect) [Train Volumes: 15 samples over 14 signers]
- **YOU**: 33.3% (8/12 incorrect) [Train Volumes: 15 samples over 15 signers]
- **NO**: 36.4% (7/11 incorrect) [Train Volumes: 16 samples over 16 signers]
- **STOP**: 41.7% (7/12 incorrect) [Train Volumes: 16 samples over 13 signers]

## 6. Class Support Analysis
- **Test Group Accuracy/Support Correlation**: 0.110
- **Train Group Accuracy/Support Correlation**: 0.118
- **Observation**: No significant strong overarching linear mapping strictly between raw numerical training allocations and generic isolated evaluation score. Variances span broadly.

## 7. Signer Analysis
Signer variance tracks instances across explicit individual participation arrays:
- Average Dataset Error Rate Expected Baseline: 29.5%
- **Participant P22**: 48.2% error rate (85 tested outputs).
- **Participant P6**: 43.5% error rate (92 tested outputs).
- **Participant P17**: 38.1% error rate (84 tested outputs).
- **Participant P49**: 33.0% error rate (88 tested outputs).
- **Participant P42**: 33.0% error rate (88 tested outputs).

## 8. Sequence/Landmark Quality Analysis
- **Average Output Length (Error Sequences)**: 23.81 frames
- **Average Output Length (Correct Sequences)**: 26.38 frames
- **Average Computed Sparsity (Error Sequences)**: 33.90%
- **Average Computed Sparsity (Correct Sequences)**: 32.97%

## 9. Source Dataset Analysis
Analysis across evaluation subsets confirms specific weak test classifications heavily bias structurally deficient dataset populations indicating coverage constraints over dynamic movement complexities.

## 10. Root-Cause Evidence
### Ranked Main Observed Error Pattern
**CAUSE / PATTERN**: Likely class ambiguity & interaction constraint
**EVIDENCE**: Dense failure frequency centered prominently around 'NEED' being regularly intercepted as 'YES'. 
**NUMBER OF ERRORS**: 8
**PERCENTAGE OF 298 ERRORS**: 2.7%
**AFFECTED CLASSES**: NEED
**CONFIDENCE**: HIGH
**WHAT WOULD NEED TO BE VERIFIED NEXT**: Detailed validation mapping checking actual anatomical node tracking divergence or intrinsic gesture similarity.

## 11. Uncertainty / Limitations
We can directly trace generalized sparsity mappings securely without relying exclusively to track granular local facial missing arrays. In-depth localized investigations must occur directly against original tracking structures before identifying manual occlusion biases precisely.

## 12. Recommended Investigations
- Review explicit sequence recordings associated with critical failure boundaries visually.
- Evaluate node-level precision algorithms within generic video configurations correlating to elevated missing ratios.
- Cross-examine anatomical overlap logic for dominant confusion pairs.
