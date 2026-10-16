import os
import json
import csv

VOCAB = r"d:\Singvox\Singvox\docs\ai-ml\asl100_vocabulary.json"
MAPPING = r"d:\Singvox\Singvox\ai\sign-recognition\config\asl100_asl_citizen_mapping.json"
MANIFEST = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
ANIMATIONS_DIR = r"d:\Singvox\Singvox\web\public\avatar\animations"

def load_json(p):
    try:
        with open(p, 'r') as f: return json.load(f)
    except: return {}

vocab_raw = load_json(VOCAB)
mapping_raw = load_json(MAPPING)

keys = []
if 'classes' in vocab_raw:
    for cls in vocab_raw.get('classes', []):
        keys.append(cls.get('name'))

if not keys:
    for item in mapping_raw:
        if item.get('mapping_type') != 'unavailable':
            keys.append(item.get('canonical_name'))

manifest_counts = {}
try:
    with open(MANIFEST, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lbl = row.get('canonical_name')
            if lbl:
                manifest_counts[lbl] = manifest_counts.get(lbl, 0) + 1
except: pass

mapping_count = len(mapping_raw) if isinstance(mapping_raw, list) else len(mapping_raw.keys())
anim_files = []
if os.path.exists(ANIMATIONS_DIR):
    anim_files = [f for f in os.listdir(ANIMATIONS_DIR) if f.endswith('.fbx') or f.endswith('.glb')]

out = []
out.append(f"Total Vocab Words parsed: {len(keys)}")
out.append(f"Total Mapped Classes with Config Rules: {mapping_count}")
out.append(f"Total Classes with Videos in Manifest: {len(manifest_counts.keys())}")
out.append("\n=== COVERAGE MATRIX ===")
ready_signs = []
for k in keys:
    count = manifest_counts.get(k, 0)
    has_anim = any(k.lower() in f.lower() for f in anim_files)
    status = "READY" if count > 0 and has_anim else "Needs Animation" if count > 0 else "Needs Data"
    if status == "READY": ready_signs.append(k)
    out.append(f"[{k}] Videos: {count} | Animation: {has_anim} | Status: {status}")

out.append(f"\nFinal Ready Signs: {len(ready_signs)} targetting 26-30 threshold.")

with open(r"d:\Singvox\Singvox\.tmp\coverage.txt", "w") as f:
    f.write("\n".join(out))
