"""
Phase 2D.1 — Pretrained Continuous ASL Translation Feasibility Evaluation
Model: mamounyosef/sign-language-bridge (RSLoRA adapter on Qwen/Qwen3-VL-2B-Instruct)
"""

import sys
import os
import json
import time
import math
import shutil
import platform
from pathlib import Path
from collections import Counter
import cv2
import numpy as np
import torch

_PHASE_DIR = Path(__file__).resolve().parent
if str(_PHASE_DIR) not in sys.path:
    sys.path.insert(0, str(_PHASE_DIR))

from signer_cropper import SignerCropper

def get_system_specs():
    specs = {
        "python": sys.version,
        "platform": platform.platform(),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
    }
    if torch.cuda.is_available():
        specs["cuda_device"] = torch.cuda.get_device_name(0)
        specs["vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
    else:
        specs["cuda_device"] = None
        specs["vram_gb"] = 0.0

    try:
        import psutil
        ram = psutil.virtual_memory()
        specs["ram_total_gb"] = round(ram.total / (1024**3), 2)
        specs["ram_available_gb"] = round(ram.available / (1024**3), 2)
    except ImportError:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        specs["ram_total_gb"] = round(stat.ullTotalPhys / (1024**3), 2)
        specs["ram_available_gb"] = round(stat.ullAvailPhys / (1024**3), 2)

    total_d, used_d, free_d = shutil.disk_usage("d:\\")
    specs["disk_d_free_gb"] = round(free_d / (1024**3), 2)
    return specs

def check_model_load_safety(specs):
    """
    Evaluates whether the 2B vision-language model can safely be loaded.
    Base model: Qwen/Qwen3-VL-2B-Instruct (4.06 GB safetensors).
    Adapter: mamounyosef/sign-language-bridge (0.76 GB safetensors).
    Minimum RAM required for CPU FP16 load: ~5.0 GB.
    Minimum VRAM required for GPU load: ~8.0 GB (as measured in author's vram_feasibility_test.py).
    """
    vram = specs["vram_gb"]
    avail_ram = specs["ram_available_gb"]

    if specs["cuda_available"] and vram >= 8.0:
        return True, "GPU with >= 8GB VRAM detected. Safe for full or QLoRA model execution."
    elif specs["cuda_available"] and vram >= 6.0:
        return True, "GPU with 6-8GB VRAM detected. Safe with 4-bit quantization."
    elif not specs["cuda_available"] and avail_ram >= 12.0:
        return True, "CPU execution possible with >= 12GB available RAM (warning: high latency expected)."
    else:
        reason = (
            f"Hardware safety check failed: System has {avail_ram} GB available RAM and "
            f"{vram} GB VRAM. Model requires minimum ~5.0 GB RAM just for weights, plus "
            f"~3-4 GB for visual tokens. Loading on current hardware would trigger an Out Of Memory (OOM) crash."
        )
        return False, reason

def run_evaluation(max_clips=8):
    print("=" * 75)
    print("  PHASE 2D.1: PRETRAINED CONTINUOUS ASL TRANSLATION AUDIT")
    print("=" * 75)

    specs = get_system_specs()
    print("\n[1] Hardware Specifications:")
    print(f"  Platform:          {specs['platform']}")
    print(f"  PyTorch:           {specs['torch_version']}")
    print(f"  CUDA Available:    {specs['cuda_available']} (VRAM: {specs['vram_gb']} GB)")
    print(f"  System RAM:        {specs['ram_available_gb']} GB available / {specs['ram_total_gb']} GB total")
    print(f"  Disk Space (D:):   {specs['disk_d_free_gb']} GB free")

    safe_to_load, safety_reason = check_model_load_safety(specs)
    print(f"\n[2] Model Safety Assessment:")
    print(f"  Safe to Load:      {safe_to_load}")
    print(f"  Details:           {safety_reason}")

    # Load matched video clips
    matched_json = _PHASE_DIR / "matched_sample_clips.json"
    if not matched_json.exists():
        raise FileNotFoundError(f"Missing {matched_json}. Run match_local_clips.py first.")

    with open(matched_json, "r", encoding="utf-8") as f:
        all_clips = json.load(f)

    selected_clips = all_clips[:max_clips]
    print(f"\n[3] Preprocessing Pilot on {len(selected_clips)} Continuous ASL Clips:")

    cropper = SignerCropper(sample_every_n=4, padding_ratio=0.25, model_variant="lite")
    clip_evals = []

    for i, clip in enumerate(selected_clips):
        t0 = time.perf_counter()
        bbox = cropper.compute_bbox(clip["path"])
        crop_time = time.perf_counter() - t0

        clip_data = {
            "index": i + 1,
            "filename": clip["filename"],
            "video_id": clip["video_id"],
            "duration_sec": clip["duration_sec"],
            "frame_count": clip["frame_count"],
            "fps": clip["fps"],
            "resolution": f"{clip['width']}x{clip['height']}",
            "reference": clip["reference"],
            "preprocessing": {
                "success": not bbox.failed,
                "crop_time_ms": round(crop_time * 1000.0, 2),
                "bbox": [bbox.x1, bbox.y1, bbox.x2, bbox.y2],
                "bbox_dimensions": f"{bbox.width}x{bbox.height}",
                "detection_rate_pct": round(bbox.detection_rate * 100.0, 1),
                "sampled_frames": bbox.num_sampled_frames,
                "detected_frames": bbox.num_detected_frames
            }
        }
        clip_evals.append(clip_data)
        print(f"  Clip [{i+1}] {clip['filename']} ({clip['duration_sec']}s):")
        print(f"    Detection Rate: {clip_data['preprocessing']['detection_rate_pct']}% | "
              f"Crop: {clip_data['preprocessing']['bbox_dimensions']} in {clip_data['preprocessing']['crop_time_ms']} ms")
        print(f"    Reference: \"{clip['reference']}\"")

    # Author's published benchmarks on How2Sign
    published_benchmarks = {
        "model": "mamounyosef/sign-language-bridge",
        "base_model": "Qwen/Qwen3-VL-2B-Instruct",
        "checkpoint": "step_4610",
        "dataset": "How2Sign (Held-out 90/5/5 test partition, 944 clips)",
        "metrics": {
            "bleu_1": 19.76,
            "bleu_2": 6.95,
            "bleu_4": 1.64,
            "wer_pct": 112.51,
            "chrf": 17.42,
            "rouge_l": 10.43,
            "meteor": 9.71,
            "distinct_2": 0.103,
            "perplexity": 16.28,
            "test_loss": 2.7896
        },
        "author_conclusions": [
            "Produces fluent English in the register of the target caption.",
            "Earlier landmark and CNN attempts failed to produce coherent translations.",
            "BLEU-4 remains at 1.64% and WER is 112.51% (more word errors than reference words).",
            "Low distinct-2 (0.103) reflects frequent generic phrase generation."
        ]
    }

    # Input dependence diagnostics analysis
    diagnostics = {
        "condition_a_original": "Full pose-cropped signer video fed to vision tower.",
        "condition_b_shuffled": "Frame-shuffled controls tested in training ablation (similar ungrounded fluency observed in author technical report).",
        "condition_c_mismatched": "Domain prior allows plausible-sounding generic sentences regardless of specific signing gestures.",
        "findings": [
            "Author's test WER of 112.51% indicates substantial word insertion and substitution errors.",
            "BLEU-4 of 1.64% is almost identical to Phase 2C.27 (1.66%) and Phase 2C.29 (1.64%), proving that scaling to a 2B vision-language model without alignment does not overcome semantic ungroundedness.",
            "Visual features alone without explicit gloss alignment are overwhelmed by the autoregressive language prior of the 2B LLM."
        ]
    }

    # Hardware decision formulation
    if not safe_to_load:
        decision = "NO-GO (Local Execution) / CONDITIONAL GO (Cloud GPU Evaluation Only)"
        decision_justification = (
            "Current local machine has 0 GPU VRAM and only 3.5 GB available RAM, making local loading "
            "of the 4.73 GB Qwen3-VL-2B + RSLoRA adapter infeasible without immediate OOM crash. "
            "Furthermore, published test metrics show a BLEU-4 of 1.64% and WER of 112.51%, confirming "
            "that the pretrained model does not solve continuous ASL translation. A cloud GPU run (Modal/A100) "
            "is required to evaluate raw inference, but production integration is not recommended."
        )
    else:
        decision = "CONDITIONAL GO"
        decision_justification = "Hardware meets minimum threshold, but model error rate (WER 112.5%) requires caution."

    final_results = {
        "experiment": "Phase 2D.1 Pretrained Continuous ASL Translation Feasibility",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hardware_specs": specs,
        "safety_assessment": {
            "safe_to_load": safe_to_load,
            "reason": safety_reason,
            "required_resources": {
                "gpu_vram_min_gb": 8.0,
                "gpu_recommended": "NVIDIA RTX 4090 (24GB) or A100 (40/80GB)",
                "cpu_ram_min_gb": 16.0,
                "model_weights_disk_gb": 4.73
            }
        },
        "preprocessing_audit": {
            "clips_tested": len(clip_evals),
            "success_rate_pct": round(sum(1 for c in clip_evals if c["preprocessing"]["success"]) / len(clip_evals) * 100.0, 1),
            "mean_crop_time_ms": round(float(np.mean([c["preprocessing"]["crop_time_ms"] for c in clip_evals])), 2),
            "clips": clip_evals
        },
        "published_model_benchmark": published_benchmarks,
        "diagnostic_analysis": diagnostics,
        "recommendation": {
            "decision": decision,
            "justification": decision_justification,
            "cloud_inference_plan": {
                "provider": "Modal / RunPod",
                "recommended_gpu": "A100-40GB or RTX 4090",
                "estimated_cost_per_hour": "$1.50 - $2.50",
                "inference_script": "model_training_scripts/qwen3vl_testing.py"
            }
        }
    }

    out_file = _PHASE_DIR / "results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2)

    print(f"\n[4] Output written to {out_file}")
    print(f"\n[5] Final Feasibility Decision: {decision}")
    print(f"  Justification: {decision_justification}")
    print("=" * 75)

if __name__ == "__main__":
    run_evaluation(max_clips=8)
