import urllib.request
import json
from pathlib import Path

out_dir = Path(r"d:\Singvox\Singvox\experiments\continuous-asl\phase_2d_1")
out_dir.mkdir(parents=True, exist_ok=True)

def fetch_url(url, desc):
    print(f"\n--- Fetching {desc} from {url} ---")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SingVox-Audit/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            print(f"Success! Length: {len(content)} chars.")
            return content
    except Exception as e:
        print(f"Error fetching {desc}: {e}")
        return None

# 1. HF Model Tree (Files)
tree_json = fetch_url("https://huggingface.co/api/models/mamounyosef/sign-language-bridge/tree/main", "HF File Tree")
if tree_json:
    try:
        files = json.loads(tree_json)
        print("Files in Hugging Face repository:")
        for f in files:
            path = f.get("path")
            size = f.get("size", "N/A")
            print(f"  - {path:<30} (size: {size})")
    except Exception as e:
        print(f"Error parsing tree JSON: {e}")

# 2. adapter_config.json
adapter_cfg = fetch_url("https://huggingface.co/mamounyosef/sign-language-bridge/raw/main/adapter_config.json", "adapter_config.json")
if adapter_cfg:
    print("adapter_config.json content:")
    print(adapter_cfg)
    with open(out_dir / "adapter_config.json", "w", encoding="utf-8") as f:
        f.write(adapter_cfg)

# 3. Model Card README.md
readme = fetch_url("https://huggingface.co/mamounyosef/sign-language-bridge/raw/main/README.md", "HF Model Card README")
if readme:
    with open(out_dir / "HF_README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    # print first 1000 chars
    print("\n--- Model Card README snippet ---")
    print(readme[:1500])

# 4. GitHub README.md
gh_readme = fetch_url("https://raw.githubusercontent.com/mamounyosef/sign-language-bridge/main/README.md", "GitHub README")
if gh_readme:
    with open(out_dir / "GITHUB_README.md", "w", encoding="utf-8") as f:
        f.write(gh_readme)
    print("\n--- GitHub README snippet ---")
    print(gh_readme[:1500])
