import json
import cv2
from pathlib import Path

audit_path = Path("experiments/continuous-asl/phase_2d_2/resource_audit.json")
manifest_path = Path("experiments/continuous-asl/phase_2d_1/matched_sample_clips.json")

with open(audit_path, "r", encoding="utf-8") as f:
    audit = json.load(f)

with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = {c["filename"]: c for c in json.load(f)}

print("=" * 65)
print("  VERIFYING 5 SELECTED CLIPS FROM MANIFEST")
print("=" * 65)

for i, sc in enumerate(audit["selected_clips"]):
    fn = sc["filename"]
    m = manifest.get(fn)
    if not m:
        print(f"[{i+1}] {fn}: NOT FOUND IN MANIFEST")
        continue
    path = m["path"]
    cap = cv2.VideoCapture(path)
    ok = cap.isOpened()
    fcount = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if ok else 0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if ok else 0
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if ok else 0
    fps = cap.get(cv2.CAP_PROP_FPS) if ok else 0
    cap.release()
    print(f"[{i+1}] {fn}")
    print(f"     Path: {path}")
    print(f"     Status: {'OK' if ok else 'FAILED TO OPEN'}")
    print(f"     Properties: {fcount} frames, {w}x{h}, {fps:.1f} fps, {sc['duration_sec']}s")
    print(f"     Reference: \"{sc['reference'][:80]}...\"")
    print("-" * 65)
