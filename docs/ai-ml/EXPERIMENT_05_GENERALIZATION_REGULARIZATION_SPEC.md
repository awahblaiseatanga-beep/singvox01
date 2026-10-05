# EXPERIMENT 05: GENERALIZATION / REGULARIZATION (V2-REG)

## 1. Experiment Objective
Investigate the strong train-validation generalization gap observed in the SignVox V2 SPOTER model. The goal is to determine if increasing regularization (dropout) improves validation generalization without permanently collapsing the representational logic.

## 2. Hypothesis
SPOTER has sufficient capacity to fit the training set incredibly well (reaching 100% accuracy), but stronger regularization may improve validation generalization by mitigating this overfitting trajectory.

## 3. Control Configuration
- **Architecture**: Unchanged SPOTER
- **Dimensions**: 366
- **Normalization**: V2 Constants (Left Hand: 0.3887, Right Hand: 0.3666, Pose XYZ: 1.8127, Face: 0.3139)
- **Epochs**: 100
- **Random Seed**: 42
- **Optim**: AdamW (1e-4)
- **Batch Size**: 32
- **Dropout Control**: 0.1

## 4. Single Variable Experimental Change
- **Variable**: Regularization Strength
- **Change**: **Dropout set to 0.3** (Applied consistently to all defined dropout locations natively in the SPOTER implementation).

## 5. Success Criteria
- **STRONG POSITIVE**: Experimental peak validation accuracy improves meaningfully over V2 control.
- **MARGINAL POSITIVE**: Experimental peak validation accuracy improves slightly while showing a clearly healthier generalization gap.
- **NEUTRAL**: Performance remains effectively equivalent to V2.
- **NEGATIVE**: Validation performance decreases meaningfully (lower accuracy).

## 6. Forbidden Operations
- DO NOT run test inference or access testing arrays.
- DO NOT modify architecture, representation, learning rate, dataset, or constraints.
- DO NOT fast-forward or simulate calculation gracefully identically accurately compactly efficiently realistically logically explicitly stably organically smartly symmetrically conceptually rationally.
