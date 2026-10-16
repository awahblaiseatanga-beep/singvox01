import urllib.request
import json
from pathlib import Path

out_dir = Path(r"d:\Singvox\Singvox\experiments\continuous-asl\phase_2d_1")

def query_url(url, desc):
    print(f"\n--- Checking {desc} ---")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SingVox-Audit/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode("utf-8")
            print(f"Status: OK ({len(data)} bytes)")
            return data
    except Exception as e:
        print(f"Error ({desc}): {e}")
        return None

# 1. Check adapter folder
adapter_files = query_url("https://huggingface.co/api/models/mamounyosef/sign-language-bridge/tree/main/adapter", "HF adapter tree")
if adapter_files:
    files = json.loads(adapter_files)
    for f in files:
        print(f"  - {f.get('path')} (size: {f.get('size')} bytes)")

# 2. Check adapter_config.json in adapter/
cfg = query_url("https://huggingface.co/mamounyosef/sign-language-bridge/raw/main/adapter/adapter_config.json", "adapter/adapter_config.json")
if cfg:
    print("\nadapter_config.json:")
    print(cfg)
    with open(out_dir / "adapter_config.json", "w") as f:
        f.write(cfg)

# 3. Check base model on HF
base_meta = query_url("https://huggingface.co/api/models/Qwen/Qwen3-VL-2B-Instruct", "Qwen/Qwen3-VL-2B-Instruct")
if not base_meta:
    # check Qwen2-VL-2B-Instruct
    query_url("https://huggingface.co/api/models/Qwen/Qwen2-VL-2B-Instruct", "Qwen/Qwen2-VL-2B-Instruct")
    query_url("https://huggingface.co/api/models/Qwen/Qwen2.5-VL-3B-Instruct", "Qwen/Qwen2.5-VL-3B-Instruct")

# 4. Check GitHub repo contents
gh_files = query_url("https://api.github.com/repos/mamounyosef/sign-language-bridge/contents", "GitHub Repo Root Files")
if gh_files:
    try:
        items = json.loads(gh_files)
        print("\nGitHub Repo Files:")
        for it in items:
            print(f"  - {it.get('name')} ({it.get('type')})")
    except Exception as e:
        print(f"Error parsing GitHub files: {e}")
