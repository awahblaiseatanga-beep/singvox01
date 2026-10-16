import json
from pathlib import Path

exp_dir = Path(r"experiments/continuous-asl/phase_2c_27")
curves_path = exp_dir / "training_curves.json"
model_path = exp_dir / "best_attention_model.pt"

print("Model exists:", model_path.exists())
if model_path.exists():
    print("Model file size:", model_path.stat().st_size)

print("Curves exist:", curves_path.exists())
if curves_path.exists():
    with open(curves_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("Best val loss:", data.get("best_val_loss"))
    print("Total training time:", data.get("total_time_seconds"), "s")
    print("Epoch history:")
    for h in data.get("history", []):
        print(f"  Epoch {h['epoch']:02d}: Train Loss {h['train_loss']}, Val Loss {h['val_loss']}, Time {h['epoch_time_sec']}s")
