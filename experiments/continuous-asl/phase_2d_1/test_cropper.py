import sys
from pathlib import Path

exp_dir = Path(r"d:\Singvox\Singvox\experiments\continuous-asl\phase_2d_1")
sys.path.append(str(exp_dir))

from signer_cropper import SignerCropper
import json

with open(exp_dir / "matched_sample_clips.json", "r", encoding="utf-8") as f:
    clips = json.load(f)

test_clip = clips[1] # e.g. -d5dN54tH2E_1-1-rgb_front.mp4 (1.33s)
print(f"Testing SignerCropper on: {test_clip['filename']} ({test_clip['duration_sec']}s)")

cropper = SignerCropper(sample_every_n=4, padding_ratio=0.25, model_variant="lite")
bbox = cropper.compute_bbox(test_clip["path"])

print("\n--- Cropper Results ---")
print(f"Failed:          {bbox.failed}")
print(f"BBox (x1, y1, x2, y2): ({bbox.x1}, {bbox.y1}, {bbox.x2}, {bbox.y2})")
print(f"BBox Dimensions: {bbox.width}x{bbox.height} (Original: {bbox.frame_width}x{bbox.frame_height})")
print(f"Detection Rate:  {bbox.detection_rate * 100:.1f}% ({bbox.num_detected_frames}/{bbox.num_sampled_frames} frames)")
