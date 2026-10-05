import json

v2_path = r"d:\Singvox\Singvox\docs\ai-ml\SPOTER_V2_RAW_RESULTS.json"
vpn_path = r"d:\Singvox\Singvox\docs\ai-ml\EXPERIMENT_02_VPN_RAW_RESULTS.json"

with open(v2_path, 'r') as f: v2 = json.load(f)
with open(vpn_path, 'r') as f: vpn = json.load(f)

v2_best = v2["best_val_acc"]
v2_epoch = v2["best_acc_epoch"]

vpn_best = vpn["best_val_acc"]
vpn_epoch = vpn["best_acc_epoch"]

best_history = next(h for h in vpn["history"] if h["epoch"] == vpn_epoch)

v2_best_loss = v2["best_val_loss"]
vpn_best_loss = vpn["best_val_loss"]

diff_abs = vpn_best - v2_best
diff_rel = diff_abs / v2_best

out = []
out.append(f"V2 CONTROL:")
out.append(f"  Best Val Acc: {v2_best:.4f} at epoch {v2_epoch}")
out.append(f"  Best Val Loss: {v2_best_loss:.4f} at epoch {v2['best_loss_epoch']}")
out.append(f"")
out.append(f"EXP-02 (V2-VPN):")
out.append(f"  Best Val Acc: {vpn_best:.4f} at epoch {vpn_epoch}")
out.append(f"  Best Val Loss: {vpn_best_loss:.4f} at epoch {vpn['best_loss_epoch']}")
out.append(f"  Diff: {diff_abs:.4f} ({diff_rel:.2%})")
out.append(f"  Macro Val Acc: {vpn['final_macro_acc']:.4f}")
out.append(f"  Train Acc at best: {best_history['train_acc']:.4f}")
out.append(f"  Gap: {best_history['train_acc'] - vpn_best:.4f}")

total_time = vpn.get("total_time", 0) / 60
out.append(f"  Time: {total_time:.2f} mins")

with open(r"d:\Singvox\Singvox\ai\sign-recognition\training\exp02_parsed.txt", "w") as f:
    f.write("\n".join(out))
