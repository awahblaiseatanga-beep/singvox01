"""
Check whether the missing feature files correspond to videos that actually exist
in the ASL Citizen source directory, and attempt to understand why they weren't extracted.
"""
import csv
from pathlib import Path

manifest = r'd:\Singvox\Singvox\experiments\spoter_v3\manifests\spoter_v3_matched_manifest.csv'
features_dir = Path(r'd:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted')
videos_dir = Path(r'D:\ASL_Citizen\ASL_Citizen\videos')

npy_files = {p.name for p in features_dir.glob('*_features.npy')}

rows = []
with open(manifest, 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

missing_info = []
for r in rows:
    video = r['video_file']
    base = Path(video).stem
    npy = f'{base}_features.npy'
    if npy not in npy_files:
        # Check if source video exists
        video_path = videos_dir / video
        exists = video_path.exists()
        missing_info.append({
            'asl_id': r['asl_id'],
            'canonical_name': r['canonical_name'],
            'video': video,
            'source_split': r['source_split'],
            'source_video_exists': exists
        })

print(f'Total missing feature files: {len(missing_info)}')
video_exists = sum(1 for m in missing_info if m['source_video_exists'])
video_missing = sum(1 for m in missing_info if not m['source_video_exists'])
print(f'  Source video EXISTS (can re-extract): {video_exists}')
print(f'  Source video also MISSING (unrecoverable): {video_missing}')

# Group by class: which classes are entirely unextractable
from collections import defaultdict
class_video_status = defaultdict(lambda: {'exists': 0, 'missing': 0})
for m in missing_info:
    if m['source_video_exists']:
        class_video_status[m['asl_id']]['exists'] += 1
    else:
        class_video_status[m['asl_id']]['missing'] += 1

# The 16 zero-feature classes
ZERO_CLASSES = ['ASL_005', 'ASL_015', 'ASL_026', 'ASL_032', 'ASL_040',
                'ASL_047', 'ASL_048', 'ASL_058', 'ASL_060', 'ASL_065',
                'ASL_067', 'ASL_068', 'ASL_077', 'ASL_078', 'ASL_083', 'ASL_087']

print()
print('=== Zero-Feature Classes: Source Video Status ===')
for asl in ZERO_CLASSES:
    e = class_video_status[asl]['exists']
    m_count = class_video_status[asl]['missing']
    total = e + m_count
    # Also get canonical name
    name = next((r['canonical_name'] for r in rows if r['asl_id'] == asl), '?')
    print(f'  {asl} ({name}): {e}/{total} source videos found, {m_count} also missing')
