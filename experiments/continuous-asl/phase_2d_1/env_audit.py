import sys
import os
import platform
import shutil
import urllib.request
import json
from pathlib import Path

print("=== STEP 1: ENVIRONMENT & HARDWARE AUDIT ===")
print(f"Python Executable: {sys.executable}")
print(f"Python Version:    {sys.version}")
print(f"Platform:          {platform.platform()} ({platform.machine()})")

# Disk Space
total, used, free = shutil.disk_usage("d:\\")
print(f"Disk D: Total: {total / (1024**3):.1f} GB, Used: {used / (1024**3):.1f} GB, Free: {free / (1024**3):.1f} GB")

# RAM
try:
    import psutil
    ram = psutil.virtual_memory()
    print(f"System RAM: Total: {ram.total / (1024**3):.1f} GB, Available: {ram.available / (1024**3):.1f} GB")
except ImportError:
    # Windows fallback
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
    print(f"System RAM: Total: {stat.ullTotalPhys / (1024**3):.1f} GB, Available: {stat.ullAvailPhys / (1024**3):.1f} GB")

# PyTorch & CUDA
try:
    import torch
    print(f"PyTorch Version:   {torch.__version__}")
    cuda_avail = torch.cuda.is_available()
    print(f"CUDA Available:    {cuda_avail}")
    if cuda_avail:
        print(f"CUDA Device Count: {torch.cuda.device_count()}")
        print(f"CUDA Device Name:  {torch.cuda.get_device_name(0)}")
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"CUDA Device VRAM:  {vram_gb:.2f} GB")
        print(f"CUDA Capability:   {torch.cuda.get_device_capability(0)}")
    else:
        print("Running in CPU-only mode (No CUDA acceleration detected).")
except ImportError:
    print("PyTorch is NOT installed!")

# Critical Libraries Check
packages_to_check = [
    "transformers",
    "peft",
    "accelerate",
    "cv2",
    "decord",
    "qwen_vl_utils",
    "torchvision",
    "mediapipe",
    "huggingface_hub"
]

print("\n--- Package Version Checks ---")
for pkg in packages_to_check:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, "__version__", "installed (no __version__)")
        print(f"  {pkg:<18}: {ver}")
    except ImportError:
        print(f"  {pkg:<18}: NOT INSTALLED")

# Test Hugging Face connectivity
print("\n--- Hugging Face API Connectivity ---")
hf_model_id = "mamounyosef/sign-language-bridge"
url = f"https://huggingface.co/api/models/{hf_model_id}"

try:
    req = urllib.request.Request(url, headers={"User-Agent": "SingVox-Audit/1.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
        print(f"Successfully reached Hugging Face API for {hf_model_id}!")
        print(f"Model ID:      {data.get('id')}")
        print(f"Private:       {data.get('private')}")
        print(f"Downloads:     {data.get('downloads')}")
        tags = data.get('tags', [])
        print(f"Tags:          {tags[:8]}")
        card_data = data.get('cardData', {})
        print(f"Base Model:    {card_data.get('base_model', 'N/A')}")
except Exception as e:
    print(f"Failed to connect to Hugging Face API: {e}")
