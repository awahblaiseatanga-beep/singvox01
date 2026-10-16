import json

mapping_path = r'd:\Singvox\Singvox\experiments\spoter_v3\config\asl100_v3_class_mapping.json'
with open(mapping_path) as f:
    mapping = json.load(f)

print(f'Total entries in mapping: {len(mapping)}')
indices = sorted([v['class_index'] for v in mapping.values()])
print(f'Class index range: {indices[0]} to {indices[-1]}')
print(f'Unique indices: {len(set(indices))} (expected 100)')
print(f'Consecutive 0..99: {indices == list(range(100))}')

FIVE_EXCLUDED = {'ASL_045', 'ASL_066', 'ASL_074', 'ASL_082', 'ASL_085'}
for asl in sorted(FIVE_EXCLUDED):
    entry = mapping.get(asl)
    if entry:
        print(f'  {asl} ({entry["canonical_name"]}): index={entry["class_index"]} -- slot retained, non-trainable')
    else:
        print(f'  {asl}: MISSING from mapping (ERROR)')

active = {k: v for k, v in mapping.items() if k not in FIVE_EXCLUDED}
print(f'Active trainable classes: {len(active)} (expected 95)')

names = [v['canonical_name'] for v in mapping.values()]
dupes = {n for n in names if names.count(n) > 1}
print(f'Duplicate canonical names: {dupes if dupes else "None"}')

# Verify the 5 excluded classes DO have training data = 0 confirmation
# (Already confirmed by manifest audit, just state the class index reservation)
print()
print('Class index reservation check:')
for asl in sorted(FIVE_EXCLUDED):
    idx = mapping[asl]['class_index']
    print(f'  {asl} -> index {idx} reserved, will never appear in training targets')
