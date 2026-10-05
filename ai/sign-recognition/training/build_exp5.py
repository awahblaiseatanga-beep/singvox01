import os
with open(r'd:\Singvox\Singvox\ai\sign-recognition\training\train_spoter_v2.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace model init
code = code.replace("model = Spoter(num_classes=79, hidden_dim=512)", 
                    "model = Spoter(num_classes=79, hidden_dim=512, dropout=0.3)")

# Replace checkpoints
code = code.replace("spoter_v2_groupnorm_best_val_acc.pt", 
                    "spoter_experiment_05_reg_best_val_acc.pt")
code = code.replace("spoter_v2_groupnorm_best_val_loss.pt", 
                    "spoter_experiment_05_reg_best_val_loss.pt")

# Replace outputs
code = code.replace("SPOTER_V2_RAW_RESULTS.json", 
                    "EXPERIMENT_05_REG_RAW_RESULTS.json")
code = code.replace("SPOTER V2 CANDIDATE TRAINING", 
                    "SPOTER EXPERIMENT 05 (V2-REG) TRAINING")

# Write
with open(r'd:\Singvox\Singvox\ai\sign-recognition\training\train_experiment_05_reg.py', 'w', encoding='utf-8') as f:
    f.write(code)
