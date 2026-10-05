import os
import hashlib

def sha256_checksum(filepath):
    if not os.path.exists(filepath):
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

files_to_hash = [
    r"d:\Singvox\Singvox\ai\sign-recognition\models\spoter_baseline_best_val_acc_checkpoint.pt",
    r"d:\Singvox\Singvox\ai\sign-recognition\models\spoter_baseline_best_val_loss_checkpoint.pt",
    r"d:\Singvox\Singvox\ai\sign-recognition\models\spoter_baseline_latest_checkpoint.pt",
    r"d:\Singvox\Singvox\docs\ai-ml\SPOTER_BASELINE_TRAINING_REPORT.md",
    r"d:\Singvox\Singvox\docs\ai-ml\SPOTER_FINAL_TEST_EVALUATION_REPORT.md",
    r"d:\Singvox\Singvox\docs\ai-ml\SPOTER_CHECKPOINT_INTEGRITY_REPORT.md",
    r"d:\Singvox\Singvox\docs\ai-ml\SPOTER_ERROR_FORENSIC_ANALYSIS.md",
    r"d:\Singvox\Singvox\docs\ai-ml\SPOTER_TARGETED_ERROR_AUDIT.md",
    r"d:\Singvox\Singvox\docs\ai-ml\SPOTER_NATIVE_VIDEO_ROOT_CAUSE_AUDIT.md"
]

manifest_content = "# SPOTER BASELINE ARTIFACT INTEGRITY\n\n"
manifest_content += "The following artifacts represent the immutable, locked state of the SPOTER Baseline. Their SHA-256 signatures are recorded below to ensure strict experimental verification and control.\n\n"

for f in files_to_hash:
    filename = os.path.basename(f)
    chk = sha256_checksum(f)
    manifest_content += f"- **{filename}**\n  - SHA-256: `{chk}`\n\n"

manifest_path = r"d:\Singvox\Singvox\docs\ai-ml\SPOTER_BASELINE_ARTIFACT_INTEGRITY.md"
with open(manifest_path, 'w', encoding='utf-8') as f:
    f.write(manifest_content)

print("Integrity Manifest Generated successfully.")
