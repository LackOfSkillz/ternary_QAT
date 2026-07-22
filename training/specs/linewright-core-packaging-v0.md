# LineWright Core — Packaging Recommendation (v0)

**Dispatch 26, Deliverable 8. Provisional. Publishes no weights. Foundation selection is
pending Phase A; this design is foundation-agnostic.** Machine-readable form:
[`linewright-core-packaging-v0.yaml`](linewright-core-packaging-v0.yaml).

## Goal

Ship the selected foundation as a local **LineWright Core** package that is *usable on an 8GB
system* at a well-tested 4-bit profile, *better on 12–16GB / 24GB unified memory*, and *able to
scale into larger future context without replacing the foundation*. The package must not
hard-code one inference engine and must not optimise only for today's 8GB constraint.

## Tiers

| Tier | Quantization | Memory | Default context | Notes |
|------|--------------|--------|-----------------|-------|
| **Minimum** | Q4_K_M (nearest 4-bit) | 8GB VRAM, 16GB+ RAM | 8K | CPU-offload fallback; long packets may need trimming |
| **Recommended** | Q5_K_M / Q6_K | 12–16GB VRAM or 24GB unified | 16K–32K | near-full-precision for craft tasks |
| **High-quality** | bf16 / official FP8 | 24–32GB+ | model native | reference quality |
| **External provider** | — | — | — | optional bring-your-own-key fallback; never required or default |

## Installer

Detect GPU/unified-memory + system RAM on first run, recommend a tier, and download only the
selected artifact against a **signed version manifest** (`linewright-core-models.json`:
`model_id, revision, quant, sha256, license`). Every artifact is **sha256-verified before first
load**. Apache-2.0 LICENSE + NOTICE are bundled (both candidates are Apache-2.0). Model download
is optional at install, required before first generation. CPU-offload is the low-VRAM fallback.
Upgrades install side-by-side; a foundation swap is a manifest + download change, not a code
rewrite. The primary backend is **llama.cpp/GGUF**, with optional transformers/vLLM backends
behind one interface (engine neutrality).

## Candidate-specific packaging outlook

- **Qwen3-8B** — GGUF path is **mature** (official `Qwen3-8B-GGUF` + community builds), so the
  8GB Q4_K_M target (~4.7–5.1 GB) is well-supported and low-risk. The shipped default **must
  disable thinking mode** and be verified free of `<think>` leakage.
- **Ministral-3-8B** — multimodal FP8 (`mistral3`); native runtime is **vLLM**, and transformers
  text-only needs `kernels==0.15.2`. Measured text-only resident footprint **~26.8 GB** (includes
  the vision tower). **The mistral3 GGUF/llama.cpp path is unverified**, so the 8GB *local* target
  may not be reachable with the current toolchain — a decisive packaging strike against selecting
  Ministral as the *local* foundation, independent of prose quality.

Concrete quantization sizes/quality deltas are filled from Deliverable 6 once a foundation is
chosen.
