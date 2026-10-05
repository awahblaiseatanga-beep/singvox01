# SPOTER BASELINE — LOCKED REFERENCE

## 1. Baseline Name
**SPOTER BASELINE**

## 2. Status
**LOCKED REFERENCE**

## 3. Checkpoint
`spoter_baseline_best_val_acc_checkpoint.pt`

## 4. Architecture
- SPOTER encoder-decoder
- input dimension: 366
- d_model: 512
- 8 attention heads
- 6 encoder layers
- 6 decoder layers
- FFN: 2048
- learned positional encoding
- single class query
- 79 output classes

## 5. Training
- AdamW
- learning rate: 1e-4
- batch size: 32
- CrossEntropyLoss
- seed: 42
- maximum epochs: 100

## 6. Final Held-Out Test Result
- 1,011 test sequences
- 713 correct
- 298 incorrect
- Top-1 accuracy: 70.52%
- Macro accuracy: 70.11%
- Test loss: 1.2497

## 7. Validation Reference
- best validation accuracy: 77.78%
- best validation accuracy checkpoint: epoch 75

## 8. Dataset
- 79 mapped classes
- 2,516 training sequences total across train/validation/test
- signer-disjoint evaluation
- test set untouched until final evaluation

## 9. Current Status
**ROOT-CAUSE INVESTIGATION CONTINUES**

## 10. Explicit Statement
The baseline is locked as a control/reference condition. Locking the baseline does not terminate research, diagnostics, or future experimentation. Any proposed improvement must be evaluated as a separate candidate against this locked baseline.
