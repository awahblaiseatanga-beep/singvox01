---
license: apache-2.0
base_model: Qwen/Qwen3-VL-2B-Instruct
language:
  - en
tags:
  - sign-language
  - sign-language-translation
  - asl
  - american-sign-language
  - video
  - video-text-to-text
  - peft
  - lora
  - rslora
datasets:
  - how2sign
  - openasl
library_name: peft
pipeline_tag: video-text-to-text
---

# sign-language-bridge: Qwen3-VL-2B fine-tuned for ASL to English translation

LoRA / RSLoRA fine-tune of
[`Qwen/Qwen3-VL-2B-Instruct`](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct)
for continuous American Sign Language (ASL) to English translation.

Checkpoint corresponds to global optimiser step **4,610** (selected on
validation loss). Source code, full technical report, and training pipeline:
[github.com/mamounyosef/sign-language-bridge](https://github.com/mamounyosef/sign-language-bridge).

## Test-set results (How2Sign, 944 clips)

| Metric        | Value   |
|---------------|--------:|
| Test loss     |  2.7896 |
| Perplexity    |  16.28  |
| BLEU-1        |  19.76  |
| BLEU-2        |   6.95  |
| BLEU-4        |   1.64  |
| chrF          |  17.42  |
| ROUGE-L       |  10.43  |
| METEOR        |   9.71  |
| WER (%)       | 112.51  |
| Distinct-2    |   0.103 |

Numbers are reported on a **custom 90/5/5 stratified split**, not the
official How2Sign / OpenASL splits, and are therefore **not directly
comparable to published results** on those corpora. See the
[GitHub repo](https://github.com/mamounyosef/sign-language-bridge) and the
technical report for the full evaluation protocol and the data-cleaning
passes that drove the custom split.

The model produces fluent English in the register of the target captions
and often captures the meaning of the signed input, but the word-level
overlap with the references is modest.

## Repository contents

```text
adapter/
  adapter_config.json          PEFT / LoRA configuration
  adapter_model.safetensors    LoRA weights + saved embedding & output-head modules
  README.md                    PEFT auto-generated card
training_state.pt              optimizer + scheduler states (per tier),
                               InfoNCE projection-head weights,
                               InfoNCE MoCo queues, RNG snapshots,
                               phase / step / epoch bookkeeping
```

`training_state.pt` is required only for resuming training or for reusing
the InfoNCE alignment. It is **not** needed for inference; loading the
`adapter/` folder on top of the base model is sufficient to generate.

## How to use (inference)

```python
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from peft import PeftModel

REPO_ID = "mamounyosef/sign-language-bridge"
BASE    = "Qwen/Qwen3-VL-2B-Instruct"

processor = AutoProcessor.from_pretrained(BASE)
base = AutoModelForImageTextToText.from_pretrained(
    BASE, torch_dtype=torch.bfloat16, device_map="auto",
)
model = PeftModel.from_pretrained(base, REPO_ID, subfolder="adapter")
model.eval()

# `video` should be a tensor / list of frames preprocessed by `processor`.
# For best results, replicate the training-time preprocessing:
#   1) pose-guided signer crop  (MediaPipe pose bbox)
#   2) CLAHE on L-channel in LAB (clip limit 2.0, 8x8 tile grid)
#   3) MediaPipe landmark overlay (21 keypoints/hand + 6 upper-body joints)
# See https://github.com/mamounyosef/sign-language-bridge for the exact code.

messages = [{
    "role": "user",
    "content": [
        {"type": "video", "video": video},
        {"type": "text",  "text":  "Translate the signed sentence to English."},
    ],
}]
inputs = processor.apply_chat_template(
    messages, add_generation_prompt=True, return_tensors="pt", tokenize=True,
).to(model.device)

out = model.generate(
    **inputs,
    max_new_tokens=32,
    num_beams=5,
    length_penalty=0.6,
    no_repeat_ngram_size=4,
    repetition_penalty=1.1,
)
print(processor.batch_decode(out, skip_special_tokens=True)[0])
```

## Training summary

- **Base model:** `Qwen/Qwen3-VL-2B-Instruct` (2B parameters: 24-layer vision
  tower, 28-layer Qwen3 decoder, M-RoPE, DeepStack mergers at vision layers
  5 / 11 / 17).
- **Adaptation:** multi-tier LoRA / RSLoRA, **34,321,920 trainable
  parameters (≈1.59%)** of the combined model.
  - T1 (LM attention + MLP): rank 16
  - T2 (Vision encoder): rank 32
  - T3 (Embeddings + output head): rank 8 (plus `modules_to_save`)
  - T4 (InfoNCE projection heads): full-rank, trained from scratch
- **Auxiliary loss:** symmetric InfoNCE between pooled vision and caption
  embeddings (256-dim, τ = 0.07, λ = 0.3 with 200-step linear warmup,
  MoCo-style negative queue of size 64).
- **Schedule:** OpenASL stage (2 epochs, 2,448 steps) → How2Sign stage
  (6 epochs, 3,540 steps). Within OpenASL, Phase 1 (first 20% of steps)
  trains only T2 and T4; Phase 2 unfreezes all four tiers. Per-tier cosine
  LR schedules with a 5% linear warmup.
- **Preprocessing (always-on):** pose-guided signer crop, CLAHE contrast
  enhancement, and pre-extracted MediaPipe landmark overlays
  (21 keypoints / hand + 6 upper-body joints).
- **Compute:** 1× NVIDIA A100 80GB, effective batch size 24
  (per-device 6 × 4 gradient-accumulation steps), bfloat16,
  FlashAttention 2, gradient checkpointing, 8-bit AdamW, Liger fused
  Triton kernels. **Total wall-clock ≈ 4d 18h.**

For full details, see the technical report and source code in the
[GitHub repository](https://github.com/mamounyosef/sign-language-bridge).

## Generation defaults used for evaluation

| Parameter             | Value |
|-----------------------|------:|
| Beam size             |   5   |
| Length penalty        |   0.6 |
| No-repeat n-gram      |   4   |
| Repetition penalty    |   1.1 |
| Max new tokens        |  32   |

## Datasets

- [How2Sign](https://how2sign.github.io/) — multi-view ASL corpus of
  instructional "How To" videos with manually verified English captions.
- [OpenASL](https://github.com/chevalierNoir/OpenASL) — large open-domain
  ASL corpus collected from online video.

Both datasets are subject to their own upstream terms of use. This
repository does **not** redistribute the raw videos.

## Limitations and intended use

- This is a **research preview**, not a production translation system.
  Word-level accuracy is low (BLEU-4 = 1.64, WER = 112.51% on the How2Sign
  test partition); outputs are fluent and often topically appropriate but
  frequently disagree with the reference at the word level.
- The model was trained on a **custom data split**, so reported numbers are
  not directly comparable to published How2Sign / OpenASL results.
- Outputs may be plausibly fluent but **factually wrong** with respect to
  the signed input. Do **not** use this model in any setting where a
  mistranslation could cause harm (medical, legal, safety-critical,
  emergency, etc.).
- The model has been trained almost exclusively on the signers, framings,
  and lighting conditions present in How2Sign and OpenASL, and may
  generalise poorly to out-of-distribution signing.

## License and attribution

- This adapter is released under the **Apache License 2.0**.
- The base model
  [`Qwen/Qwen3-VL-2B-Instruct`](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct)
  is also under Apache 2.0 ([upstream LICENSE](https://github.com/QwenLM/Qwen3-VL/blob/main/LICENSE)).
  Use of this adapter, together with the base model, remains subject to
  Qwen's Apache 2.0 terms.
- Built using 🤗 [`peft`](https://github.com/huggingface/peft) and
  🤗 [`transformers`](https://github.com/huggingface/transformers).

## Citation

If you use this model or its results, please cite the project repository:

```bibtex
@misc{yosef2026signbridge,
  author       = {Ma'moun Yosef},
  title        = {sign-language-bridge: Fine-Tuning Qwen3-VL-2B for ASL to
                  English Translation},
  year         = {2026},
  howpublished = {\url{https://github.com/mamounyosef/sign-language-bridge}}
}
```

and the base model:

```bibtex
@article{qwen3vl2025,
  author        = {{Qwen Team}},
  title         = {{Qwen3-VL} Technical Report},
  journal       = {arXiv preprint arXiv:2511.21631},
  year          = {2025}
}
```
