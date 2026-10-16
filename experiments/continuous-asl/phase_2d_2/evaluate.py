"""
Phase 2D.2 — Cloud Inference Evaluate Script
mamounyosef/sign-language-bridge on Qwen/Qwen3-VL-2B-Instruct

This script is designed to run on a GPU server (A100/RTX 4090 with >= 8GB VRAM).
It must NOT be executed locally (see Phase 2D.1 for hardware audit evidence).

Usage (on cloud GPU after installing requirements):
    python evaluate.py --clips_json matched_sample_clips.json --output_dir ./results

Environment Variables:
    HF_TOKEN  — Optional Hugging Face token (for gated models; not required here)
                 Export from shell: export HF_TOKEN="hf_..."
                 NEVER hardcode credentials in this file.
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import random
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import torch

# Suppress MediaPipe / TF log noise
os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

PHASE_DIR = Path(__file__).resolve().parent

# ─────────────────────────────────────────────────────────────────────────────
# GENERATION CONFIG — mirrors author's published test settings (step 4,610)
# ─────────────────────────────────────────────────────────────────────────────
GEN_CONFIG = {
    "beam_size": 5,
    "length_penalty": 0.6,
    "no_repeat_ngram_size": 4,
    "repetition_penalty": 1.1,
    "max_new_tokens": 32,
}

MODEL_ID = "mamounyosef/sign-language-bridge"
BASE_MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"
ADAPTER_SUBDIR = "adapter"   # within the HF repo

SYSTEM_PROMPT = "You are a sign language translator."
USER_PROMPT = "Translate this American Sign Language video into English."

# FPS used at training time (from author's README / CONFIG)
VIDEO_FPS = 2   # author trained at 2 fps to limit token count
VIDEO_MIN_PIXELS = 4 * 32 * 32
VIDEO_MAX_PIXELS = 256 * 256   # ~256px cap matches author's 256px config
VIDEO_TOTAL_PIXELS = 20480 * 32 * 32


# ─────────────────────────────────────────────────────────────────────────────
# ENV + HARDWARE CHECK
# ─────────────────────────────────────────────────────────────────────────────
def check_gpu():
    if not torch.cuda.is_available():
        raise RuntimeError(
            "No CUDA GPU detected. This script requires a GPU with >= 8 GB VRAM. "
            "See docs/research/PHASE_2D_1_PRETRAINED_MODEL_FEASIBILITY_REPORT.md."
        )
    name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    print(f"  GPU: {name}")
    print(f"  VRAM: {vram_gb:.2f} GB")
    if vram_gb < 8.0:
        raise RuntimeError(
            f"GPU has only {vram_gb:.1f} GB VRAM. Minimum 8 GB required. "
            "Use an A100, RTX 4090, or similar."
        )
    return name, vram_gb


def check_packages():
    missing = []
    for pkg in ["transformers", "peft", "qwen_vl_utils"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        raise RuntimeError(
            f"Missing packages: {missing}. Run:\n"
            f"  pip install transformers peft accelerate qwen-vl-utils"
        )


# ─────────────────────────────────────────────────────────────────────────────
# MODEL LOADING
# ─────────────────────────────────────────────────────────────────────────────
def load_model(dtype=torch.bfloat16):
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from peft import PeftModel

    print(f"\n  Loading base model: {BASE_MODEL_ID}")
    model_kwargs = {
        "dtype": dtype,
        "device_map": "cuda",
    }

    try:
        import flash_attn  # noqa: F401
        model_kwargs["attn_implementation"] = "flash_attention_2"
        print("  Using Flash Attention 2")
    except ImportError:
        model_kwargs["attn_implementation"] = "sdpa"
        print("  Using SDPA (Flash Attention 2 not available)")

    t0 = time.perf_counter()
    model = AutoModelForImageTextToText.from_pretrained(BASE_MODEL_ID, **model_kwargs)
    base_load_time = time.perf_counter() - t0
    base_vram = torch.cuda.memory_allocated() / (1024 ** 3)
    print(f"  Base model loaded in {base_load_time:.1f}s, VRAM: {base_vram:.2f} GB")

    processor = AutoProcessor.from_pretrained(BASE_MODEL_ID)
    processor.tokenizer.padding_side = "left"

    print(f"\n  Loading RSLoRA adapter from HF: {MODEL_ID}/{ADAPTER_SUBDIR}")
    t1 = time.perf_counter()
    model = PeftModel.from_pretrained(
        model,
        MODEL_ID,
        subfolder=ADAPTER_SUBDIR,
        is_trainable=False
    )
    adapter_load_time = time.perf_counter() - t1

    print(f"  Merging LoRA adapter into base weights...")
    model = model.merge_and_unload()
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    if hasattr(model, "config"):
        model.config.use_cache = True

    merged_vram = torch.cuda.memory_allocated() / (1024 ** 3)
    print(f"  Adapter loaded + merged in {adapter_load_time:.1f}s")
    print(f"  Peak VRAM after merge: {merged_vram:.2f} GB")

    return model, processor, {
        "base_load_time_s": round(base_load_time, 2),
        "adapter_load_time_s": round(adapter_load_time, 2),
        "vram_after_merge_gb": round(merged_vram, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# VIDEO PREPROCESSING (author's signer_cropper.py)
# ─────────────────────────────────────────────────────────────────────────────
def preprocess_video(video_path: str, cropper=None) -> str:
    """
    Apply pose-guided signer crop and return a path.
    If cropper is None or cropping fails, returns the original path.
    """
    if cropper is None:
        return video_path
    try:
        sys.path.insert(0, str(PHASE_DIR))
        bbox = cropper.compute_bbox(video_path)
        if bbox.failed:
            print(f"    [crop] Pose detection failed, using original.")
            return video_path

        cap = cv2.VideoCapture(video_path)
        fps_in = cap.get(cv2.CAP_PROP_FPS) or 24.0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frames = []
        while True:
            ok, frm = cap.read()
            if not ok:
                break
            frames.append(frm)
        cap.release()

        cropped = np.stack(frames)[:, bbox.y1:bbox.y2, bbox.x1:bbox.x2, :]
        out_path = str(PHASE_DIR / "tmp_cropped.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        bh, bw = cropped.shape[1], cropped.shape[2]
        writer = cv2.VideoWriter(out_path, fourcc, fps_in, (bw, bh))
        for frm in cropped:
            writer.write(frm)
        writer.release()
        return out_path
    except Exception as e:
        print(f"    [crop] Error: {e}, using original.")
        return video_path


def build_messages(video_path: str) -> list:
    """Build Qwen3-VL multi-modal chat message list for a single video."""
    return [
        {
            "role": "system",
            "content": [{"type": "text", "text": SYSTEM_PROMPT}],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "video",
                    "video": video_path,
                    "fps": VIDEO_FPS,
                    "min_pixels": VIDEO_MIN_PIXELS,
                    "max_pixels": VIDEO_MAX_PIXELS,
                    "total_pixels": VIDEO_TOTAL_PIXELS,
                },
                {"type": "text", "text": USER_PROMPT},
            ],
        },
    ]


# ─────────────────────────────────────────────────────────────────────────────
# SINGLE INFERENCE
# ─────────────────────────────────────────────────────────────────────────────
def run_inference(model, processor, video_path: str) -> tuple[str, float, dict]:
    """
    Run inference on one video clip.
    Returns: (hypothesis_str, latency_ms, debug_info)
    """
    from qwen_vl_utils import process_vision_info

    messages = build_messages(video_path)
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    images, videos, video_kwargs = process_vision_info(
        messages,
        image_patch_size=16,
        return_video_kwargs=True,
        return_video_metadata=True,
    )

    video_metadatas = None
    if videos is not None:
        try:
            videos, video_metadatas = zip(*videos)
            videos, video_metadatas = list(videos), list(video_metadatas)
        except (TypeError, ValueError):
            pass  # older qwen_vl_utils version — pass without metadata

    proc_kwargs = dict(
        text=[text],
        images=images if images else None,
        videos=videos if videos else None,
        return_tensors="pt",
        padding=True,
        do_resize=False,
        **video_kwargs,
    )
    if video_metadatas:
        proc_kwargs["video_metadata"] = video_metadatas

    inputs = processor(**proc_kwargs)
    input_ids = inputs["input_ids"]
    total_tokens = input_ids.shape[1]
    video_token_id = 151656  # <|video_pad|>
    video_tokens = int((input_ids == video_token_id).sum())

    inputs = {k: v.to("cuda") if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
    peak_before = torch.cuda.max_memory_allocated() / (1024 ** 3)

    torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            num_beams=GEN_CONFIG["beam_size"],
            length_penalty=GEN_CONFIG["length_penalty"],
            no_repeat_ngram_size=GEN_CONFIG["no_repeat_ngram_size"],
            repetition_penalty=GEN_CONFIG["repetition_penalty"],
            max_new_tokens=GEN_CONFIG["max_new_tokens"],
        )
    latency_ms = (time.perf_counter() - t0) * 1000.0
    peak_vram = torch.cuda.max_memory_allocated() / (1024 ** 3)

    # Decode only the generated tokens (strip input prefix)
    gen_tokens = output_ids[0, input_ids.shape[1]:]
    hypothesis = processor.tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

    return hypothesis, round(latency_ms, 1), {
        "total_input_tokens": total_tokens,
        "video_tokens": video_tokens,
        "text_tokens": total_tokens - video_tokens,
        "peak_vram_gb": round(peak_vram, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────────────────────────────────────
def ngrams(tokens, n):
    return Counter(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))


def bleu(refs, hyps, max_n=4):
    c, r = 0, 0
    precisions = [[] for _ in range(max_n)]
    for ref, hyp in zip(refs, hyps):
        rt = ref.lower().split()
        ht = hyp.lower().split()
        c += len(ht)
        r += len(rt)
        for n in range(1, max_n + 1):
            hn = ngrams(ht, n)
            rn = ngrams(rt, n)
            num = sum(min(cnt, rn[ng]) for ng, cnt in hn.items())
            den = max(1, len(ht) - n + 1)
            precisions[n - 1].append(num / den if num else 1e-9)
    bp = 1.0 if c > r else math.exp(1.0 - r / max(1, c))
    avg = [float(np.mean(precisions[i])) for i in range(max_n)]
    return {
        "bleu1": round(bp * avg[0] * 100, 2),
        "bleu4": round(bp * math.exp(sum(0.25 * math.log(max(1e-9, avg[i])) for i in range(4))) * 100, 2),
        "bp": round(bp, 4),
    }


def word_error_rate(refs, hyps):
    total_ref, total_edits = 0, 0
    for ref, hyp in zip(refs, hyps):
        rt, ht = ref.lower().split(), hyp.lower().split()
        total_ref += len(rt)
        # Levenshtein on tokens
        dp = list(range(len(ht) + 1))
        for i, rc in enumerate(rt):
            prev = dp[:]
            dp[0] = i + 1
            for j, hc in enumerate(ht):
                dp[j + 1] = min(prev[j] + (0 if rc == hc else 1), dp[j] + 1, prev[j + 1] + 1)
        total_edits += dp[-1]
    return round(total_edits / max(1, total_ref) * 100, 2)


def shuffled_frames(video_path: str, seed: int = 42) -> str:
    """Save a frame-shuffled version of the video and return its path."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames = []
    while True:
        ok, frm = cap.read()
        if not ok:
            break
        frames.append(frm)
    cap.release()

    rng = random.Random(seed)
    rng.shuffle(frames)

    out_path = str(PHASE_DIR / "tmp_shuffled.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    for frm in frames:
        writer.write(frm)
    writer.release()
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Phase 2D.2 Cloud Inference")
    parser.add_argument("--clips_json", type=str, required=True, help="Path to matched_sample_clips.json")
    parser.add_argument("--max_clips", type=int, default=8, help="Number of pilot clips (default 8)")
    parser.add_argument("--expand", action="store_true", help="Expand to 20 clips if pilot is promising")
    parser.add_argument("--output_dir", type=str, default=str(PHASE_DIR), help="Where to write results.json")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 75)
    print("  PHASE 2D.2 — CLOUD INFERENCE PILOT")
    print("=" * 75)

    # ── Hardware check ──
    print("\n[0] Hardware Check")
    gpu_name, vram_gb = check_gpu()
    check_packages()

    # ── Import heavy deps ──
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from peft import PeftModel

    sys.path.insert(0, str(PHASE_DIR.parent / "phase_2d_1"))
    try:
        from signer_cropper import SignerCropper
        cropper = SignerCropper(sample_every_n=4, padding_ratio=0.25, model_variant="lite")
        print("  SignerCropper loaded.")
    except ImportError:
        cropper = None
        print("  SignerCropper unavailable — using raw video paths.")

    # ── Load model ──
    print("\n[1] Loading Model")
    torch.cuda.reset_peak_memory_stats()
    model, processor, load_stats = load_model()
    peak_load_vram = torch.cuda.max_memory_allocated() / (1024 ** 3)
    print(f"  Peak load VRAM: {peak_load_vram:.2f} GB")

    # ── Load clips ──
    with open(args.clips_json, "r", encoding="utf-8") as f:
        all_clips = json.load(f)

    n_pilot = min(args.max_clips, len(all_clips))
    pilot_clips = all_clips[:n_pilot]
    print(f"\n[2] Running Pilot on {n_pilot} Clips")

    pilot_results = []
    refs, hyps = [], []

    for i, clip in enumerate(pilot_clips):
        print(f"\n  Clip [{i+1}/{n_pilot}]: {clip['filename']} ({clip['duration_sec']}s)")
        print(f"  Ref: \"{clip['reference']}\"")
        result = {
            "index": i + 1,
            "filename": clip["filename"],
            "video_id": clip.get("video_id", ""),
            "duration_sec": clip["duration_sec"],
            "reference": clip["reference"],
            "hyp_original": None,
            "hyp_shuffled": None,
            "hyp_mismatched_ref": None,
            "latency_original_ms": None,
            "latency_shuffled_ms": None,
            "tokens": None,
            "peak_vram_gb": None,
            "errors": [],
        }

        try:
            video_path = preprocess_video(clip["path"], cropper)
            hyp, lat, dbg = run_inference(model, processor, video_path)
            result["hyp_original"] = hyp
            result["latency_original_ms"] = lat
            result["tokens"] = dbg
            result["peak_vram_gb"] = dbg["peak_vram_gb"]
            print(f"  Hyp: \"{hyp}\"   [{lat:.0f} ms, {dbg['video_tokens']} video tokens]")
            refs.append(clip["reference"])
            hyps.append(hyp)
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            print(f"  ERROR: {err}")
            result["errors"].append(err)
            traceback.print_exc()

        pilot_results.append(result)

    # ── Input-dependence diagnostics (first 3 clips) ──
    print("\n[3] Input-Dependence Diagnostics (clips 1–3)")
    diag_clips = [r for r in pilot_results if r["hyp_original"] is not None][:3]
    for r in diag_clips:
        clip = next(c for c in pilot_clips if c["filename"] == r["filename"])
        # Condition B: shuffled frames
        try:
            shuf_path = shuffled_frames(clip["path"])
            proc_path = preprocess_video(shuf_path, cropper)
            hyp_s, lat_s, _ = run_inference(model, processor, proc_path)
            r["hyp_shuffled"] = hyp_s
            r["latency_shuffled_ms"] = lat_s
            print(f"  [{r['filename']}] Shuffled: \"{hyp_s}\"")
        except Exception as e:
            r["errors"].append(f"shuffled: {type(e).__name__}: {e}")

        # Condition C: mismatched video (use next clip's video)
        other_clips = [c for c in pilot_clips if c["filename"] != r["filename"]]
        if other_clips:
            mismatched_clip = other_clips[0]
            r["hyp_mismatched_ref"] = mismatched_clip["reference"]
            # We just record which ref the original hyp was evaluated against
            matched_b1 = bleu([clip["reference"]], [r["hyp_original"] or ""])["bleu1"]
            mismatched_b1 = bleu([mismatched_clip["reference"]], [r["hyp_original"] or ""])["bleu1"]
            r["matched_bleu1"] = matched_b1
            r["mismatched_bleu1"] = mismatched_b1
            r["matched_wins"] = matched_b1 > mismatched_b1

    # ── Optional expansion ──
    expand_results = []
    if args.expand and len(all_clips) > n_pilot:
        print(f"\n[4] Expanding to 20 Clips")
        extra_clips = all_clips[n_pilot:20]
        for i, clip in enumerate(extra_clips):
            print(f"  Clip [{n_pilot+i+1}/20]: {clip['filename']}")
            try:
                video_path = preprocess_video(clip["path"], cropper)
                hyp, lat, dbg = run_inference(model, processor, video_path)
                refs.append(clip["reference"])
                hyps.append(hyp)
                expand_results.append({
                    "filename": clip["filename"],
                    "reference": clip["reference"],
                    "hypothesis": hyp,
                    "latency_ms": lat
                })
                print(f"  Hyp: \"{hyp}\"")
            except Exception as e:
                print(f"  ERROR: {e}")

    # ── Compute aggregate metrics ──
    print("\n[5] Computing Metrics")
    valid_pairs = [(r, h) for r, h in zip(refs, hyps) if h]
    agg_refs = [p[0] for p in valid_pairs]
    agg_hyps = [p[1] for p in valid_pairs]
    bleu_stats = bleu(agg_refs, agg_hyps) if agg_refs else {}
    wer_val = word_error_rate(agg_refs, agg_hyps) if agg_refs else None
    exact_matches = sum(1 for r, h in zip(agg_refs, agg_hyps) if r.lower().strip() == h.lower().strip())

    shuffled_identical = 0
    n_shuffled = 0
    for r in diag_clips:
        if r["hyp_original"] and r["hyp_shuffled"] is not None:
            n_shuffled += 1
            if r["hyp_original"].lower().strip() == r["hyp_shuffled"].lower().strip():
                shuffled_identical += 1

    matched_win_count = sum(1 for r in diag_clips if r.get("matched_wins", False))
    n_diag = len(diag_clips)

    print(f"  BLEU-1: {bleu_stats.get('bleu1', 'N/A')}%")
    print(f"  BLEU-4: {bleu_stats.get('bleu4', 'N/A')}%")
    print(f"  WER: {wer_val}%")
    print(f"  Exact Match: {exact_matches}/{len(agg_refs)}")
    print(f"  Shuffled Output Identity: {shuffled_identical}/{n_shuffled}")
    print(f"  Matched Win Rate (vs Mismatched): {matched_win_count}/{n_diag}")

    # ── Final decision logic ──
    bleu1 = bleu_stats.get("bleu1", 0)
    shuffled_id_rate = shuffled_identical / max(1, n_shuffled)
    matched_win_rate = matched_win_count / max(1, n_diag)

    if bleu1 >= 20.0 and shuffled_id_rate < 0.5 and matched_win_rate >= 0.6:
        decision = "GO"
        rationale = "BLEU-1 >= 20%, shuffled identity < 50%, matched wins >= 60%. Credible video-dependent output detected."
    elif bleu1 >= 10.0 or matched_win_rate >= 0.5:
        decision = "CONDITIONAL GO"
        rationale = "Some video dependence, but insufficient for direct production use. Follow-up experiment required."
    else:
        decision = "NO-GO"
        rationale = "Output does not convincingly depend on the signing content. Language prior dominates."

    print(f"\n  Decision: {decision}")
    print(f"  Rationale: {rationale}")

    # ── Write results ──
    results = {
        "experiment": "Phase 2D.2 Cloud Inference Pilot",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hardware": {
            "gpu": gpu_name,
            "vram_total_gb": round(vram_gb, 2),
            "peak_load_vram_gb": round(peak_load_vram, 2),
        },
        "model": {
            "base_model_id": BASE_MODEL_ID,
            "adapter_id": MODEL_ID,
            "adapter_subdir": ADAPTER_SUBDIR,
            "load_stats": load_stats,
        },
        "generation_config": GEN_CONFIG,
        "metrics": {
            "clips_evaluated": len(agg_refs),
            "bleu1": bleu_stats.get("bleu1"),
            "bleu4": bleu_stats.get("bleu4"),
            "bp": bleu_stats.get("bp"),
            "wer_pct": wer_val,
            "exact_match": exact_matches,
            "shuffled_identical_pct": round(shuffled_id_rate * 100, 1),
            "matched_win_rate_pct": round(matched_win_rate * 100, 1),
        },
        "pilot_clips": pilot_results,
        "expansion_clips": expand_results,
        "decision": {
            "verdict": decision,
            "rationale": rationale,
        },
    }

    out_path = out_dir / "results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Results written to {out_path}")
    print("=" * 75)

    # Clean up temp files
    for tmp in [PHASE_DIR / "tmp_cropped.mp4", PHASE_DIR / "tmp_shuffled.mp4"]:
        if tmp.exists():
            tmp.unlink(missing_ok=True)

    gc.collect()
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
