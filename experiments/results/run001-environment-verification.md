# Run 1 Environment Verification

Verified 2026-07-21 on the head GX10. **No training occurred** — only environment
build, import/smoke tests, a public model download, and a tiny forward/generation
smoke test. This file contains no secrets.

## Host inventory

- **Host:** `gx10-9141` (ASUSTeK GX10, GB10 Grace-Blackwell, sm_121)
- **OS / kernel:** Ubuntu 24.04.4 LTS, kernel 6.17.0-1026-nvidia, **aarch64**
- **CPU:** 20-core Grace (10× Cortex-X925 + 10× Cortex-A725)
- **Unified memory:** 121 GiB
- **GPU:** NVIDIA GB10, driver **580.159.03**, **CUDA 13.0**
- **Disk:** `/home/gary` on `/` (3.6 TB, ~2.2 TB free)
- **Docker:** 29.2.1; NVIDIA container access via CDI (`nvidia-ctk`), `--gpus all` works.

## Container images

- **Base:** `nvcr.io/nvidia/pytorch:25.11-py3` (NVIDIA Release 25.11, pulled unauthenticated; ~19.5 GB)
  - Python 3.12.3, torch `2.10.0a0+b558c986e8.nv25.11`, CUDA 13.0, bf16 supported.
  - Preinstalled: datasets 4.4.1, safetensors 0.6.2, huggingface_hub 1.1.2, pyyaml 6.0.3, pytest 8.1.1.
  - Not preinstalled: transformers, peft, accelerate, sentencepiece.
- **Derived:** `linewright-ternary-train:run001`
  - Image ID: `sha256:e2d9ed828c2e39411689e1f0fd197810f7d870139a8e43bc7a21d3efdf030991` (19.7 GB)
  - Dockerfile: `docker/Dockerfile.train`

## Package versions (verified, pinned in the image)

Pins were resolved by an unpinned install in the base image, confirmed to leave
the NGC torch untouched, then pinned:

| Package | Version |
|---|---|
| torch | 2.10.0a0+b558c986e8.nv25.11 (base image) |
| transformers | 5.14.1 |
| peft | 0.19.1 |
| accelerate | 1.14.0 |
| datasets | 4.4.1 |
| safetensors | 0.8.0 |
| huggingface_hub | 1.24.0 |
| pyyaml | 6.0.3 |
| pytest | 8.1.1 |
| sentencepiece | 0.2.2 |

## CUDA / BF16 verification

- `torch.cuda.is_available()` → **True**; device `NVIDIA GB10`.
- `torch.version.cuda` → **13.0**.
- `torch.cuda.is_bf16_supported()` → **True**; model loads and generates in bf16.
- Attention: **SDPA** (FlashAttention deliberately not used — FA3 does not support sm_121).

## `ternary_QAT` smoke-test results (on CUDA)

- `import ternary` → ok (via `PYTHONPATH`; see deviation below).
- Ternarize forward/backward: **PASS** — shape `(4,256)` preserved, group levels ∈ {-1,0,1}, gradient reached the original tensor (`sum|grad|`=1024).
- Tied-weight `swap_linear()`: **TIED PRESERVED** — shared Parameter before and after swap; `embed_tokens`→TernaryEmbedding, `lm_head`→TernaryLinear; forward `(2,8,256)` finite.
- `python -m ternary.ste` → `ste ok` (benign runpy RuntimeWarning only).

## Model download (unauthenticated)

- `prism-ml/Ternary-Bonsai-4B-unpacked` via `snapshot_download`, **no token**.
- Result: **success** — public repo (only an unauthenticated-rate-limit warning; no gate).
- Size: **7.6 GB on disk / 8.044 GB weights**, 16 files, 2 safetensors shards.

## Model configuration summary

- Architecture: **Qwen3ForCausalLM** (`qwen3`)
- hidden_size 2560 · num_hidden_layers 36 · attention heads 32 · KV heads 8 (GQA)
- vocab_size 151669 · **tie_word_embeddings: True**
- max_position_embeddings 32768 · intermediate_size 9728 · rms_norm_eps 1e-6 · rope_theta 5,000,000
- dtype bf16 (2 shards, 8.044 GB) · BPE tokenizer (tokenizer.json + merges.txt + vocab.json; no sentencepiece .model)

## Model-load smoke test

- Tokenizer load 0.31 s; model load **1.65 s** (`device_map={"":0}`, bf16, `attn_implementation="sdpa"`, `low_cpu_mem_usage=True`).
- Forward: logits `(1, 8, 151669)`, finite.
- Generation (32 new tokens, greedy): coherent — *"The door was locked, and no one could get in or out…"*.
- **Peak unified memory: 8.065 GB** (of 121 GiB) — ample headroom for LoRA.
- Warnings: only `torch_dtype` → `dtype` deprecation (transformers 5.x). No custom-code (`trust_remote_code`) requirement. No tied-weight warnings.

## Known warnings / notes

- **Editable install blocked:** `pip install -e ".[peft,transformers]"` fails because setuptools flat-layout auto-discovery finds multiple top-level dirs at the repo root (`docker/`, `ternary/`, `experiments/`) and refuses. Worked around with `PYTHONPATH=/workspace/ternary_QAT`. **Recommended fix (future dispatch, upstream-friendly):** add to `pyproject.toml`:
  ```toml
  [tool.setuptools.packages.find]
  include = ["ternary*"]
  ```
- FlashAttention 3 unsupported on GB10 (sm_121) → use SDPA.
- Unsloth not installed; GB10 support needs manual transformers patches — deferred.

## Host mount paths (container ← host)

| Container | Host |
|---|---|
| `/workspace/ternary_QAT` | `/home/gary/projects/ternary_QAT` |
| `/workspace/hf-cache` | `/home/gary/linewright-model-training/hf-cache` |
| `/workspace/outputs` | `/home/gary/linewright-model-training/outputs` |
| `/workspace/checkpoints` | `/home/gary/linewright-model-training/checkpoints` |
| `/workspace/datasets` | `/home/gary/linewright-model-training/datasets` |
| `/workspace/logs` | `/home/gary/linewright-model-training/logs` |
| `/workspace/exports` | `/home/gary/linewright-model-training/exports` |

## Reproduce the container

```bash
# Build
cd ~/projects/ternary_QAT
docker build -f docker/Dockerfile.train -t linewright-ternary-train:run001 .

# Run (verification / interactive), one GX10:
docker run --rm --gpus all --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
  -v /home/gary/projects/ternary_QAT:/workspace/ternary_QAT \
  -v /home/gary/linewright-model-training/hf-cache:/workspace/hf-cache \
  -v /home/gary/linewright-model-training/outputs:/workspace/outputs \
  -v /home/gary/linewright-model-training/checkpoints:/workspace/checkpoints \
  -v /home/gary/linewright-model-training/datasets:/workspace/datasets \
  -v /home/gary/linewright-model-training/logs:/workspace/logs \
  -v /home/gary/linewright-model-training/exports:/workspace/exports \
  -w /workspace/ternary_QAT \
  linewright-ternary-train:run001 bash
# Inside: export PYTHONPATH=/workspace/ternary_QAT  (until the pyproject fix lands)
```

## Statement

No training (LoRA or otherwise) was run. Only environment build, import/smoke
tests, a public model download, and a ≤32-token generation smoke test were
performed.
