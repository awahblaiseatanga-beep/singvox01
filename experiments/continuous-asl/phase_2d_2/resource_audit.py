"""
Resource audit for Phase 2D.2 Zero-Budget feasibility.
Measures local disk space, available RAM, existing package versions,
and calculates theoretical CPU-inference RAM budget.
Does NOT download or load any model weights.
"""
import sys, os, shutil, platform, json, time
from pathlib import Path

# ── 1. Platform
print("=" * 65)
print("  PHASE 2D.2 — ZERO-BUDGET RESOURCE AUDIT")
print("=" * 65)
print(f"\n  Python:    {sys.version}")
print(f"  Platform:  {platform.platform()}")

# ── 2. RAM
try:
    import psutil
    ram = psutil.virtual_memory()
    ram_total = ram.total / (1024**3)
    ram_avail = ram.available / (1024**3)
except ImportError:
    import ctypes
    class MEMSTAT(ctypes.Structure):
        _fields_ = [("dwLength",ctypes.c_ulong),("dwMemoryLoad",ctypes.c_ulong),
                    ("ullTotalPhys",ctypes.c_ulonglong),("ullAvailPhys",ctypes.c_ulonglong),
                    ("ullTotalPageFile",ctypes.c_ulonglong),("ullAvailPageFile",ctypes.c_ulonglong),
                    ("ullTotalVirtual",ctypes.c_ulonglong),("ullAvailVirtual",ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual",ctypes.c_ulonglong)]
    m = MEMSTAT(); m.dwLength = ctypes.sizeof(MEMSTAT)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    ram_total = m.ullTotalPhys / (1024**3)
    ram_avail = m.ullAvailPhys / (1024**3)

print(f"\n  RAM Total:     {ram_total:.2f} GB")
print(f"  RAM Available: {ram_avail:.2f} GB  (MEASURED)")

# ── 3. Disk
for drive in ["d:\\", "c:\\"]:
    try:
        total, used, free = shutil.disk_usage(drive)
        print(f"  Disk {drive}:      {free/(1024**3):.1f} GB free / {total/(1024**3):.1f} GB total")
    except Exception:
        pass

# ── 4. CUDA
import torch
print(f"\n  PyTorch:       {torch.__version__}")
print(f"  CUDA Available: {torch.cuda.is_available()}")

# ── 5. Package availability
pkgs = {
    "transformers": "NOT INSTALLED",
    "peft": "NOT INSTALLED",
    "qwen_vl_utils": "NOT INSTALLED",
    "accelerate": "NOT INSTALLED",
    "mediapipe": "NOT INSTALLED",
    "cv2": "NOT INSTALLED",
    "numpy": "NOT INSTALLED",
}
for pkg in list(pkgs.keys()):
    attr = pkg
    try:
        mod = __import__(pkg)
        ver = getattr(mod, "__version__", "?")
        pkgs[pkg] = ver
    except ImportError:
        pass

print("\n  Package Versions:")
for k, v in pkgs.items():
    status = "[OK]" if v != "NOT INSTALLED" else "[MISSING]"
    print(f"    {status} {k}: {v}")

# ── 6. RAM budget calculation for CPU inference
print("\n  CPU Inference RAM Budget (ESTIMATES — no weights loaded):")
base_weights_gb = 4.06     # Qwen3-VL-2B safetensors on disk (measured from HF file list)
adapter_gb = 0.72          # adapter_model.safetensors (HF file)
fp32_overhead = 2.0        # dtype conversion overhead: bfloat16→float32 on CPU
kv_cache_gb = 0.5          # attention KV cache for 32-token generation
video_tokens_gb = 1.2      # pixel_values_videos for 4s clip at 2fps/256px (estimated)
os_overhead_gb = 1.5       # OS + Python runtime baseline

total_needed_gb = base_weights_gb + adapter_gb + fp32_overhead + kv_cache_gb + video_tokens_gb + os_overhead_gb
print(f"    Base weights (bfloat16 on CPU): ~{base_weights_gb:.2f} GB")
print(f"    RSLoRA adapter weights:          ~{adapter_gb:.2f} GB")
print(f"    dtype conversion (CPU uses fp32): ~{fp32_overhead:.1f} GB")
print(f"    KV cache (32 output tokens):     ~{kv_cache_gb:.1f} GB")
print(f"    Video pixel tensors (4s @2fps):  ~{video_tokens_gb:.1f} GB")
print(f"    OS + runtime baseline:           ~{os_overhead_gb:.1f} GB")
print(f"    ---")
print(f"    TOTAL estimated minimum:         ~{total_needed_gb:.2f} GB")
print(f"    RAM AVAILABLE:                   {ram_avail:.2f} GB")
gap = total_needed_gb - ram_avail
feasible = gap <= 0
print(f"    Gap (needed - available):        {gap:+.2f} GB")
print(f"    CPU inference feasible locally:  {'YES' if feasible else 'NO — OOM EXPECTED'}")

# ── 7. Latency estimate for CPU
if feasible:
    tokens_per_sec_cpu = 0.5  # Qwen-2B on CPU: ~0.3–0.8 tok/s measured reports
    latency_per_clip_s = 32 / tokens_per_sec_cpu
    print(f"    Est. latency per clip (CPU):     ~{latency_per_clip_s:.0f}s (32 tokens @ {tokens_per_sec_cpu} tok/s)")
else:
    print(f"    Latency estimate: N/A (OOM)")

# ── 8. Clip selection audit
manifest_path = Path(r"d:\Singvox\Singvox\experiments\continuous-asl\phase_2d_1\matched_sample_clips.json")
clips = json.load(open(manifest_path, "r", encoding="utf-8"))

# Pick 5 clips from different source video IDs
seen_vids = {}
selected = []
for c in clips:
    vid = c["video_id"]
    if vid not in seen_vids and len(selected) < 5:
        seen_vids[vid] = c["filename"]
        selected.append(c)

print(f"\n  Selected 5 Clips (different source video IDs):")
for i, c in enumerate(selected):
    print(f"    [{i+1}] {c['filename']} (video_id={c['video_id']}, {c['duration_sec']}s)")
    print(f"         Ref: \"{c['reference'][:70]}{'...' if len(c['reference'])>70 else ''}\"")
    exists = "EXISTS" if Path(c['path']).exists() else "MISSING"
    print(f"         File: {exists}")

# Save for report
audit = {
    "ram_total_gb": round(ram_total, 2),
    "ram_available_gb": round(ram_avail, 2),
    "cpu_inference_feasible": feasible,
    "ram_required_gb": round(total_needed_gb, 2),
    "gap_gb": round(gap, 2),
    "packages": pkgs,
    "selected_clips": [
        {"filename": c["filename"], "video_id": c["video_id"],
         "duration_sec": c["duration_sec"], "reference": c["reference"],
         "file_exists": Path(c["path"]).exists()}
        for c in selected
    ]
}
out = Path(r"d:\Singvox\Singvox\experiments\continuous-asl\phase_2d_2\resource_audit.json")
json.dump(audit, open(out, "w"), indent=2)
print(f"\n  Audit saved: {out}")
print("=" * 65)
