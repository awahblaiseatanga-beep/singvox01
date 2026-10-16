import urllib.request
from pathlib import Path

out_dir = Path(r"d:\Singvox\Singvox\experiments\continuous-asl\phase_2d_1")

files_to_fetch = [
    ("model_training_scripts/qwen3vl_testing.py", "qwen3vl_testing.py"),
    ("model_training_scripts/vram_feasibility_test.py", "vram_feasibility_test.py"),
    ("data_code/signer_cropper.py", "signer_cropper.py"),
]

for repo_path, local_name in files_to_fetch:
    url = f"https://raw.githubusercontent.com/mamounyosef/sign-language-bridge/main/{repo_path}"
    print(f"Fetching {repo_path}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SingVox-Audit/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            local_path = out_dir / local_name
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Saved {local_name} ({len(content)} chars).")
    except Exception as e:
        print(f"Error fetching {repo_path}: {e}")
