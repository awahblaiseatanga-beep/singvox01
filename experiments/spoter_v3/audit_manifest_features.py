import csv
from pathlib import Path
from collections import defaultdict

manifest = r'd:\Singvox\Singvox\experiments\spoter_v3\manifests\spoter_v3_matched_manifest.csv'
features_dir = Path(r'd:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted')
npy_files = {p.name for p in features_dir.glob('*_features.npy')}

rows = []
with open(manifest, 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

split_total = defaultdict(int)
split_found = defaultdict(int)
split_missing = defaultdict(int)
class_split_counts = defaultdict(lambda: defaultdict(int))
class_split_found = defaultdict(lambda: defaultdict(int))
split_signers = defaultdict(set)

for r in rows:
    split = r['source_split']
    asl_id = r['asl_id']
    participant = r['participant_id']
    video = r['video_file']
    base = Path(video).stem
    npy = f'{base}_features.npy'

    split_total[split] += 1
    class_split_counts[asl_id][split] += 1
    split_signers[split].add(participant)

    if npy in npy_files:
        split_found[split] += 1
        class_split_found[asl_id][split] += 1
    else:
        split_missing[split] += 1

print('=== Per-Split: Total / Found / Missing ===')
for s in ['train', 'val', 'test']:
    print(f'  {s}: total={split_total[s]}, found={split_found[s]}, missing={split_missing[s]}')

print()
print('=== Signer Counts per Split ===')
for s in ['train', 'val', 'test']:
    print(f'  {s}: {len(split_signers[s])} signers')

train_s = split_signers['train']
val_s = split_signers['val']
test_s = split_signers['test']
print(f'  Train/Val overlap: {len(train_s & val_s)} signers')
print(f'  Train/Test overlap: {len(train_s & test_s)} signers')
print(f'  Val/Test overlap: {len(val_s & test_s)} signers')

print()
FIVE_EXCLUDED = {'ASL_045', 'ASL_066', 'ASL_074', 'ASL_082', 'ASL_085'}
zero_train, zero_val, zero_test = [], [], []
all_asl_ids = sorted({r['asl_id'] for r in rows} - FIVE_EXCLUDED)

for asl_id in all_asl_ids:
    if class_split_found[asl_id]['train'] == 0:
        zero_train.append(asl_id)
    if class_split_found[asl_id]['val'] == 0:
        zero_val.append(asl_id)
    if class_split_found[asl_id]['test'] == 0:
        zero_test.append(asl_id)

print(f'95 active classes with 0 usable TRAIN features: {zero_train}')
print(f'95 active classes with 0 usable VAL features: {zero_val}')
print(f'95 active classes with 0 usable TEST features: {zero_test}')
print(f'Total active classes covered in manifest: {len(all_asl_ids)}')

print()
print('=== Five Excluded Classes (must have 0 rows in manifest) ===')
for asl in sorted(FIVE_EXCLUDED):
    t = class_split_counts[asl]
    has_rows = any(t.values())
    print(f'  {asl}: train={t.get("train",0)}, val={t.get("val",0)}, test={t.get("test",0)} | {"LEAKS INTO MANIFEST!" if has_rows else "CORRECTLY EXCLUDED"}')

print()
print('=== Summary ===')
print(f'  Manifest rows: {len(rows)}')
print(f'  Feature files on disk: {len(npy_files)}')
print(f'  Matched (usable): {sum(split_found.values())}')
print(f'  Unmatched (need extraction): {sum(split_missing.values())}')
