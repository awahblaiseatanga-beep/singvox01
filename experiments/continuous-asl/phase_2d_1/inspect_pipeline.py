import urllib.request
import json
from pathlib import Path

out_dir = Path(r"d:\Singvox\Singvox\experiments\continuous-asl\phase_2d_1")

def query_json(url, desc):
    print(f"\n--- {desc} ---")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SingVox-Audit/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except Exception as e:
        print(f"Error ({desc}): {e}")
        return None

# 1. Base model files and size
base_tree = query_json("https://huggingface.co/api/models/Qwen/Qwen3-VL-2B-Instruct/tree/main", "Qwen3-VL-2B-Instruct Files")
if base_tree:
    total_size = 0
    print("Files in Qwen/Qwen3-VL-2B-Instruct:")
    for f in base_tree:
        path = f.get("path")
        size = f.get("size", 0)
        total_size += size
        print(f"  - {path:<35} ({size / (1024**2):.1f} MB)")
    print(f"Total Base Model Weight Size: {total_size / (1024**3):.2f} GB")

# 2. GitHub data_code directory
dc_items = query_json("https://api.github.com/repos/mamounyosef/sign-language-bridge/contents/data_code", "data_code contents")
if dc_items:
    print("\nGitHub data_code files:")
    for it in dc_items:
        print(f"  - {it.get('name')} (path: {it.get('path')})")

# 3. GitHub model_training_scripts directory
mts_items = query_json("https://api.github.com/repos/mamounyosef/sign-language-bridge/contents/model_training_scripts", "model_training_scripts contents")
if mts_items:
    print("\nGitHub model_training_scripts files:")
    for it in mts_items:
        print(f"  - {it.get('name')} (path: {it.get('path')})")
