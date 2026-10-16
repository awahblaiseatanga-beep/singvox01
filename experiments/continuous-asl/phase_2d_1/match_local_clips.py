import csv
from pathlib import Path
import cv2

video_dir = Path(r"d:\Singvox\Singvox\data\sandbox_continuous\how2sign_sample")
manifest_path = Path(r"d:\Singvox\Singvox\experiments\continuous-asl\phase_2c_26\dataset_manifest.csv")

# Load manifest
manifest_records = {}
with open(manifest_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        sname = row.get("SENTENCE_NAME") or row.get("NAME") or ""
        manifest_records[sname] = {
            "sentence": row.get("SENTENCE", ""),
            "video_id": row.get("VIDEO_ID", ""),
            "duration": row.get("DURATION", ""),
            "split": row.get("SPLIT", "")
        }

print(f"Loaded {len(manifest_records)} manifest rows.")

# Scan video files
matched_clips = []
video_files = sorted(list(video_dir.glob("*.mp4")))
print(f"Found {len(video_files)} video files in {video_dir}")

for vf in video_files:
    stem = vf.stem
    # How2Sign filenames often have suffixes like -rgb_front
    clean_name = stem.replace("-rgb_front", "")
    
    match = None
    if stem in manifest_records:
        match = manifest_records[stem]
        key = stem
    elif clean_name in manifest_records:
        match = manifest_records[clean_name]
        key = clean_name
    else:
        # Check partial prefix
        for sname, rec in manifest_records.items():
            if sname in stem or stem in sname:
                match = rec
                key = sname
                break
                
    if match and match["sentence"]:
        # inspect video properties
        cap = cv2.VideoCapture(str(vf))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_s = frame_count / fps if fps > 0 else 0
        cap.release()
        
        matched_clips.append({
            "filename": vf.name,
            "path": str(vf),
            "sentence_name": key,
            "video_id": match["video_id"],
            "split": match["split"],
            "reference": match["sentence"],
            "fps": fps,
            "frame_count": frame_count,
            "width": w,
            "height": h,
            "duration_sec": round(duration_s, 2)
        })

print(f"Successfully matched {len(matched_clips)} clips with ground-truth English captions!")
print("\n--- First 8 Matched Clips ---")
for i, c in enumerate(matched_clips[:8]):
    print(f"[{i+1}] {c['filename']}")
    print(f"    Duration: {c['duration_sec']}s ({c['frame_count']} frames @ {c['fps']} fps, {c['width']}x{c['height']})")
    print(f"    Split: {c['split']}, Video ID: {c['video_id']}")
    print(f"    Reference: \"{c['reference']}\"")

# Save matched clips to JSON
import json
out_path = Path(r"d:\Singvox\Singvox\experiments\continuous-asl\phase_2d_1\matched_sample_clips.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(matched_clips, f, indent=2)
print(f"\nSaved matched clips metadata to {out_path}")
