import os
import sys
import shutil
import urllib.request
import zipfile
import csv
import json
import time
from pathlib import Path
import cv2

BASE_DIR = Path(r"d:\Singvox\Singvox")
SANDBOX_DIR = BASE_DIR / "data" / "sandbox_continuous" / "how2sign_sample"
OUT_DATA_DIR = BASE_DIR / "data" / "continuous_how2sign_val"
VIDEO_OUT_DIR = OUT_DATA_DIR / "videos"
SHARDS_DIR = OUT_DATA_DIR / "shards"
EXP_DIR = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_26"
MANIFEST_PATH = OUT_DATA_DIR / "acquisition_manifest.json"

CSV_SOURCE = SANDBOX_DIR / "how2sign_val.csv"
CSV_DEST = OUT_DATA_DIR / "how2sign_val.csv"

BASE_URL = "https://huggingface.co/datasets/aipieces/How2Sign/resolve/main/val_rgb_front_clips/"

def setup_dirs():
    OUT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_OUT_DIR.mkdir(parents=True, exist_ok=True)
    SHARDS_DIR.mkdir(parents=True, exist_ok=True)
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    if CSV_SOURCE.exists() and not CSV_DEST.exists():
        shutil.copy2(CSV_SOURCE, CSV_DEST)

def reuse_existing_sandbox():
    print("Step 1: Checking for reusable clips from sandbox...")
    reused = 0
    if SANDBOX_DIR.exists():
        for mp4 in SANDBOX_DIR.glob("*.mp4"):
            dest_file = VIDEO_OUT_DIR / mp4.name
            if not dest_file.exists():
                shutil.copy2(mp4, dest_file)
                reused += 1
            else:
                reused += 1
    print(f"Reused/Identified {reused} clips from sandbox.")
    return reused

def download_and_extract_shards():
    print("Step 2: Processing 18 shards from Hugging Face...")
    
    # Load or initialize manifest
    manifest = {}
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
    total_shards = 18
    for shard_idx in range(1, total_shards + 1):
        shard_name = f"shard_{shard_idx:03d}_{total_shards:03d}.zip"
        shard_key = f"shard_{shard_idx:03d}"
        
        if manifest.get(shard_key, {}).get("status") == "extracted":
            print(f"[{shard_idx}/{total_shards}] {shard_name} already marked extracted. Skipping.")
            continue
            
        zip_path = SHARDS_DIR / shard_name
        url = BASE_URL + shard_name
        
        # Download if not present
        if not zip_path.exists():
            print(f"[{shard_idx}/{total_shards}] Downloading {shard_name} from {url}...")
            attempts = 0
            success = False
            while attempts < 3 and not success:
                attempts += 1
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "SingvoxResearch/1.0"})
                    with urllib.request.urlopen(req, timeout=30) as resp, open(zip_path, "wb") as out_file:
                        shutil.copyfileobj(resp, out_file)
                    success = True
                    print(f"Downloaded {shard_name} successfully ({zip_path.stat().st_size / (1024*1024):.1f} MB).")
                except Exception as e:
                    print(f"Attempt {attempts} failed for {shard_name}: {e}")
                    if zip_path.exists():
                        zip_path.unlink()
                    time.sleep(2)
            if not success:
                print(f"FAILED to download {shard_name} after 3 attempts.")
                manifest[shard_key] = {"status": "download_failed", "error": str(e)}
                with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2)
                continue
                
        # Extract
        print(f"[{shard_idx}/{total_shards}] Extracting {shard_name}...")
        extracted_files = []
        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                for member in z.namelist():
                    if member.endswith(".mp4"):
                        z.extract(member, VIDEO_OUT_DIR)
                        extracted_files.append(Path(member).name)
            print(f"Extracted {len(extracted_files)} videos from {shard_name}.")
            # Remove zip file to conserve disk space
            zip_path.unlink()
            manifest[shard_key] = {
                "status": "extracted",
                "extracted_count": len(extracted_files),
                "timestamp": time.time()
            }
        except Exception as e:
            print(f"Error extracting {shard_name}: {e}")
            manifest[shard_key] = {"status": "extract_failed", "error": str(e)}
            
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

def verify_all_acquired():
    print("Step 3: Verifying video decoding and metadata matching...")
    if not CSV_DEST.exists():
        print(f"ERROR: {CSV_DEST} does not exist!")
        return
        
    csv_rows = {}
    with open(CSV_DEST, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            csv_rows[row["SENTENCE_NAME"]] = row
            
    print(f"Total annotations in CSV: {len(csv_rows)}")
    
    videos = list(VIDEO_OUT_DIR.glob("*.mp4"))
    print(f"Total video files in directory: {len(videos)}")
    
    verified_samples = []
    failed_decode = []
    missing_csv = []
    
    for v in videos:
        stem = v.stem
        if stem not in csv_rows:
            missing_csv.append(v.name)
            continue
            
        cap = cv2.VideoCapture(str(v))
        if not cap.isOpened():
            failed_decode.append(v.name)
            cap.release()
            continue
            
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        
        if frame_count <= 0:
            failed_decode.append(v.name)
            continue
            
        row = csv_rows[stem]
        verified_samples.append({
            "SENTENCE_NAME": stem,
            "VIDEO_ID": row["VIDEO_ID"],
            "SENTENCE": row["SENTENCE"],
            "START": float(row["START"]),
            "END": float(row["END"]),
            "FRAME_COUNT": frame_count,
            "FPS": fps,
            "VIDEO_PATH": str(v.relative_to(BASE_DIR))
        })
        
    print(f"Verification Results:")
    print(f"  Successfully Verified: {len(verified_samples)}")
    print(f"  Failed Decode: {len(failed_decode)}")
    print(f"  Missing CSV Annotation: {len(missing_csv)}")
    
    verification_summary = {
        "total_csv_annotations": len(csv_rows),
        "total_video_files": len(videos),
        "verified_count": len(verified_samples),
        "failed_decode": failed_decode,
        "missing_csv": missing_csv,
        "verified_samples": verified_samples
    }
    
    with open(EXP_DIR / "acquisition_verification.json", "w", encoding="utf-8") as f:
        json.dump(verification_summary, f, indent=2)
    print(f"Saved acquisition verification to {EXP_DIR / 'acquisition_verification.json'}")

if __name__ == "__main__":
    setup_dirs()
    reuse_existing_sandbox()
    download_and_extract_shards()
    verify_all_acquired()
