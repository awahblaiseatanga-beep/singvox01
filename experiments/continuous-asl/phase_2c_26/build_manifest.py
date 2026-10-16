import os
import csv
import json
import random
import re
from pathlib import Path
from collections import Counter
import numpy as np

BASE_DIR = Path(r"d:\Singvox\Singvox")
DATA_DIR = BASE_DIR / "data" / "continuous_how2sign_val"
VIDEO_DIR = DATA_DIR / "videos"
CSV_PATH = DATA_DIR / "how2sign_val.csv"
EXP_DIR = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_26"
FEAT_DIR = EXP_DIR / "features"
MANIFEST_OUT = EXP_DIR / "dataset_manifest.csv"
METRICS_OUT = EXP_DIR / "dataset_metrics.json"

def clean_sentence(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s']", " ", text)
    tokens = text.split()
    return tokens

def build_dataset_manifest():
    print("Step 1: Reading annotations and verifying file paths...")
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)

    print(f"Total annotations in CSV: {len(rows)}")
    
    # Check video files
    available_videos = {v.stem: v for v in VIDEO_DIR.glob("*.mp4")}
    print(f"Total downloaded and verified videos: {len(available_videos)}")
    
    # Filter valid rows
    matched_rows = []
    unmatched_rows = []
    for r in rows:
        stem = r["SENTENCE_NAME"]
        if stem in available_videos:
            matched_rows.append(r)
        else:
            unmatched_rows.append(r)
            
    print(f"Matched rows with downloaded videos: {len(matched_rows)}")
    print(f"Unmatched rows: {len(unmatched_rows)}")
    
    # Group by VIDEO_ID
    video_to_clips = {}
    for r in matched_rows:
        vid = r["VIDEO_ID"]
        video_to_clips.setdefault(vid, []).append(r)
        
    unique_video_ids = sorted(list(video_to_clips.keys()))
    print(f"Total unique source VIDEO_IDs: {len(unique_video_ids)}")
    
    # Deterministic split: 70% Train, 15% Val, 15% Test
    rng = random.Random(42)
    shuffled_vids = unique_video_ids.copy()
    rng.shuffle(shuffled_vids)
    
    # Assign by video count aiming for ~70/15/15 clip balance
    total_clips = len(matched_rows)
    target_train = int(0.70 * total_clips)
    target_val = int(0.15 * total_clips)
    
    train_vids, val_vids, test_vids = [], [], []
    train_count, val_count, test_count = 0, 0, 0
    
    for vid in shuffled_vids:
        n = len(video_to_clips[vid])
        if train_count + n <= target_train or (val_count >= target_val and test_count >= target_val):
            train_vids.append(vid)
            train_count += n
        elif val_count + n <= target_val or test_count >= target_val:
            val_vids.append(vid)
            val_count += n
        else:
            test_vids.append(vid)
            test_count += n
            
    print(f"Split Assignment by Source VIDEO_ID:")
    print(f"  Train: {len(train_vids)} videos -> {train_count} clips ({train_count/total_clips*100:.1f}%)")
    print(f"  Val:   {len(val_vids)} videos -> {val_count} clips ({val_count/total_clips*100:.1f}%)")
    print(f"  Test:  {len(test_vids)} videos -> {test_count} clips ({test_count/total_clips*100:.1f}%)")
    
    # Verify zero overlap in VIDEO_ID
    assert set(train_vids).isdisjoint(set(val_vids)), "Train and Val share source videos!"
    assert set(train_vids).isdisjoint(set(test_vids)), "Train and Test share source videos!"
    assert set(val_vids).isdisjoint(set(test_vids)), "Val and Test share source videos!"
    print("Assertion passed: Strict zero-leakage group split by VIDEO_ID verified.")
    
    # Prepare manifest entries
    manifest_rows = []
    
    def process_split_rows(vids, split_name):
        entries = []
        for vid in vids:
            for r in video_to_clips[vid]:
                stem = r["SENTENCE_NAME"]
                start = float(r["START"])
                end = float(r["END"])
                duration = round(end - start, 3)
                vpath = VIDEO_DIR / f"{stem}.mp4"
                fpath = FEAT_DIR / f"{stem}.npy"
                feat_exists = fpath.exists()
                
                num_frames = 0
                lh_miss = False
                rh_miss = False
                if feat_exists:
                    try:
                        arr = np.load(fpath)
                        num_frames = arr.shape[0]
                        lh_miss = bool(np.all(arr[:, :63] == 0))
                        rh_miss = bool(np.all(arr[:, 63:126] == 0))
                    except Exception:
                        pass
                        
                entries.append({
                    "SENTENCE_NAME": stem,
                    "VIDEO_ID": vid,
                    "SPLIT": split_name,
                    "START": start,
                    "END": end,
                    "DURATION": duration,
                    "SENTENCE": r["SENTENCE"].strip(),
                    "VIDEO_PATH": str(vpath.relative_to(BASE_DIR)),
                    "FEATURE_PATH": str(fpath.relative_to(BASE_DIR)),
                    "FEATURE_EXISTS": int(feat_exists),
                    "NUM_FRAMES": num_frames,
                    "LH_MISSING": int(lh_miss),
                    "RH_MISSING": int(rh_miss)
                })
        return entries
        
    train_entries = process_split_rows(train_vids, "train")
    val_entries = process_split_rows(val_vids, "val")
    test_entries = process_split_rows(test_vids, "test")
    all_entries = train_entries + val_entries + test_entries
    
    # Write CSV manifest
    fieldnames = [
        "SENTENCE_NAME", "VIDEO_ID", "SPLIT", "START", "END", "DURATION",
        "SENTENCE", "VIDEO_PATH", "FEATURE_PATH", "FEATURE_EXISTS",
        "NUM_FRAMES", "LH_MISSING", "RH_MISSING"
    ]
    with open(MANIFEST_OUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_entries)
    print(f"Saved dataset manifest to {MANIFEST_OUT} ({len(all_entries)} rows).")
    
    # Compute vocabulary and length statistics
    def analyze_tokens(entries):
        words = []
        lengths = []
        durations = []
        for e in entries:
            toks = clean_sentence(e["SENTENCE"])
            words.extend(toks)
            lengths.append(len(toks))
            durations.append(e["DURATION"])
        return words, lengths, durations
        
    train_words, train_lens, train_durs = analyze_tokens(train_entries)
    val_words, val_lens, val_durs = analyze_tokens(val_entries)
    test_words, test_lens, test_durs = analyze_tokens(test_entries)
    all_words, all_lens, all_durs = analyze_tokens(all_entries)
    
    train_vocab = set(train_words)
    val_vocab = set(val_words)
    test_vocab = set(test_words)
    total_vocab = set(all_words)
    
    # OOV computation
    val_oov_tokens = [w for w in val_words if w not in train_vocab]
    val_oov_rate = len(val_oov_tokens) / max(1, len(val_words)) * 100.0
    val_oov_types = [w for w in val_vocab if w not in train_vocab]
    
    test_oov_tokens = [w for w in test_words if w not in train_vocab]
    test_oov_rate = len(test_oov_tokens) / max(1, len(test_words)) * 100.0
    test_oov_types = [w for w in test_vocab if w not in train_vocab]
    
    # Existing 100-video pilot stats for comparison
    pilot_metrics = {
        "train_clips": 61,
        "val_clips": 19,
        "test_clips": 20,
        "total_clips": 100,
        "train_vocab": 249,
        "total_vocab": 319,
        "val_oov_token_rate": 31.8,
        "test_oov_token_rate": 28.5,
        "mean_sentence_length": 8.1,
        "median_sentence_length": 7.0
    }
    
    metrics = {
        "dataset_name": "How2Sign Validation Expanded (Phase 2C.26)",
        "total_annotated_in_csv": len(rows),
        "total_downloaded_videos": len(available_videos),
        "total_matched_samples": len(all_entries),
        "split_counts": {
            "train": {"videos": len(train_vids), "clips": len(train_entries), "pct": round(len(train_entries)/len(all_entries)*100, 1)},
            "val":   {"videos": len(val_vids),   "clips": len(val_entries),   "pct": round(len(val_entries)/len(all_entries)*100, 1)},
            "test":  {"videos": len(test_vids),  "clips": len(test_entries),  "pct": round(len(test_entries)/len(all_entries)*100, 1)}
        },
        "target_sentence_lengths": {
            "all":   {"mean": round(float(np.mean(all_lens)), 2), "median": int(np.median(all_lens)), "min": int(np.min(all_lens)), "max": int(np.max(all_lens))},
            "train": {"mean": round(float(np.mean(train_lens)), 2), "median": int(np.median(train_lens)), "min": int(np.min(train_lens)), "max": int(np.max(train_lens))},
            "val":   {"mean": round(float(np.mean(val_lens)), 2), "median": int(np.median(val_lens)), "min": int(np.min(val_lens)), "max": int(np.max(val_lens))},
            "test":  {"mean": round(float(np.mean(test_lens)), 2), "median": int(np.median(test_lens)), "min": int(np.min(test_lens)), "max": int(np.max(test_lens))}
        },
        "clip_durations_sec": {
            "total_hours": round(sum(all_durs) / 3600.0, 2),
            "mean": round(float(np.mean(all_durs)), 2),
            "median": round(float(np.median(all_durs)), 2),
            "min": round(float(np.min(all_durs)), 2),
            "max": round(float(np.max(all_durs)), 2)
        },
        "vocabulary_analysis": {
            "train_vocab_size": len(train_vocab),
            "val_vocab_size": len(val_vocab),
            "test_vocab_size": len(test_vocab),
            "total_vocab_size": len(total_vocab),
            "val_oov_token_rate_pct": round(val_oov_rate, 2),
            "val_oov_type_count": len(val_oov_types),
            "test_oov_token_rate_pct": round(test_oov_rate, 2),
            "test_oov_type_count": len(test_oov_types)
        },
        "comparison_with_100_pilot": {
            "pilot_train_clips": pilot_metrics["train_clips"],
            "expanded_train_clips": len(train_entries),
            "clip_expansion_factor": round(len(train_entries) / pilot_metrics["train_clips"], 1),
            "pilot_train_vocab": pilot_metrics["train_vocab"],
            "expanded_train_vocab": len(train_vocab),
            "vocab_expansion_factor": round(len(train_vocab) / pilot_metrics["train_vocab"], 1),
            "pilot_val_oov_rate": pilot_metrics["val_oov_token_rate"],
            "expanded_val_oov_rate": round(val_oov_rate, 2),
            "val_oov_rate_reduction": round(pilot_metrics["val_oov_token_rate"] - val_oov_rate, 2)
        }
    }
    
    with open(METRICS_OUT, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved dataset metrics to {METRICS_OUT}")
    
    print("\nDataset Quality and Split Summary:")
    print(f"  Total Clips: {len(all_entries)} across {len(unique_video_ids)} source videos ({metrics['clip_durations_sec']['total_hours']} hours)")
    print(f"  Train: {len(train_entries)} clips | Val: {len(val_entries)} clips | Test: {len(test_entries)} clips")
    print(f"  Train Vocab: {len(train_vocab)} words | Total Vocab: {len(total_vocab)} words")
    print(f"  Val OOV Token Rate: {val_oov_rate:.2f}% (vs {pilot_metrics['val_oov_token_rate']}% in 100-clip pilot)")
    print(f"  Test OOV Token Rate: {test_oov_rate:.2f}% (vs {pilot_metrics['test_oov_token_rate']}% in 100-clip pilot)")
    print(f"  Sentence Length: Mean={metrics['target_sentence_lengths']['all']['mean']} words, Median={metrics['target_sentence_lengths']['all']['median']} words")

if __name__ == "__main__":
    build_dataset_manifest()
