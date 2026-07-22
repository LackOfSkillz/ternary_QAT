# Dataset A HF backend verification v1 (Dispatch 18A.1)

Real Hugging Face backend implemented and **verified on the GX10 against the actual
4B model**. Every result below is derived from the real model; nothing is
synthesized. No real 20-step Dataset A training occurred and the real 28-record
train file was never used for gradients.

```yaml
real_hf_backend_ready: true
ready_for_dispatch_18b: true
```

## Environment

- starting HEAD: `9f88407`; verification HEAD: `2421d96`
- GX10 host: **gx10-9141**; container image `linewright-ternary-train:run001`
  (id `31d26c6bbcf9`), base `nvcr.io/nvidia/pytorch:25.11-py3`
- torch **2.10.0a0+b558c986e8.nv25.11**, transformers **5.14.1**, peft **0.19.1**,
  accelerate **1.14.0**
- CUDA available **true**, runtime **13.0**, device **NVIDIA GB10**, compute
  capability **12.1**, unified memory **124610 MB**, bf16 **true**

## Model + tokenizer

- base-model path: `/workspace/hf-cache/prism-ml/Ternary-Bonsai-4B-unpacked`
- configured revision `4485fae7a00129467b9329b738110d88b2942a1a`; the unpacked
  directory carries no `_commit_hash`, so revision verification is **path_pinned**
  (load is `local_files_only`; a mismatched `_commit_hash` would fail).
- model class **Qwen3ForCausalLM**, tokenizer class **Qwen2Tokenizer**
- chat template: **present and used** (the tokenizer's `chat_template.jinja`)
- pad/eos set; padding side right; load ~0.9 s

## Assistant-only masking (first synthetic batch)

input tokens **33**, masked (prompt+pad) **30**, assistant target **3**, truncated
**0** — prompt/pad labels are `-100`, only assistant tokens keep labels.

## Base-model inventory

file count **51**, root hash `890df375f933302e…` (captured before load; re-verified
after every phase).

## Base evaluation ×2 + reproducibility gate

- 7 held-out records, batch size 1, temperature 0 (greedy), fixed seed.
- `base/hf-eval-run-1.json` and `base/hf-eval-run-2.json` (the file hashes differ
  **only** by per-record generation timing in metadata; raw model outputs are
  identical).
- reproducibility disposition **exact_match** (exact 7, normalized 0, materially
  equivalent 0, failed 0) → **accepted**. `base/hf-eval-reproducibility.json`.

## LoRA one-step (real PEFT)

- target modules **252 matched** (q/k/v/o/gate/up/down); trainable params
  **33,030,144** of **4,054,814,720** total (**0.8146 %**).
- real forward → **loss 1.769024**; backward → global **grad norm 5.838365**;
  optimizer + scheduler step; batch record id `hf-syn-001`.
- checkpoint `training/runs/dataset-a-smoke-v1/rehearsal-hf-lora/checkpoints/step-1`
  reloaded **in a fresh process** (`PeftModelForCausalLM`, load 3.6 s, missing/
  unexpected keys 0, CUDA peak 7866 MB) → non-empty generation. **ok**.

## Ternary-QAT one-step (real ternary swap)

- linear modules before **253**; **254 replaced** (nn.Linear → TernaryLinear incl.
  lm_head + embed → TernaryEmbedding, norms excluded → **0 plain linears remain**);
  **tied weights preserved**; trainable params **4,021,784,576**.
- real forward → **loss 1.810558**; backward (straight-through estimator) → global
  **grad norm 96.5** (finite, below the 100.0 gradient-explosion rail); one step.
- checkpoint `…/rehearsal-hf-qat/checkpoints/step-1` reloaded in a fresh process
  (`Qwen3ForCausalLM` + swap + state dict, load 23.7 s, missing/unexpected keys 0,
  CUDA peak 12190 MB) → non-empty generation. **ok**.

## Integrity

- base-model integrity after eval / after LoRA / after QAT: **all ok** — no changed
  bytes, no missing/new file, no symlink change. (`integrity-hf/base-model-verification.json`)
- repository integrity: **ok** — HEAD unchanged, no protected file changed, no file
  written outside `training/runs/dataset-a-smoke-v1/`
  (`integrity-hf/repository-verification.json`). Transformers/PEFT wrote only into
  the authorized run directory.

## GPU memory diagnostics

LoRA checkpoint reload CUDA peak **7866 MB**; QAT checkpoint reload CUDA peak
**12190 MB** (of 124610 MB unified). Load/step/generate timings recorded per phase.
Performance is operational-debugging data, not a quality result.

## Limitations

- The unpacked model directory has no `_commit_hash`; revision verification is
  path-pinned (local_files_only enforces no download).
- `ternary/swap.py` follows the Bonsai paper (embeddings + attn + MLP + lm_head
  ternary; norms FP). The smoke config's `keep_modules_full_precision` hint for
  embed/lm_head is therefore superseded by the authoritative implementation —
  flagged for Gary; not a blocker for the one-step plumbing check.

## Confirmations

- The real Dataset A train file was **not** used for gradients (both rehearsals use
  disposable synthetic fixtures).
- No real 20-step LoRA or ternary-QAT training occurred.
- No base checkpoint changed; no checkpoint binaries committed; no merge / `master`
  modification.

## Readiness

All real-model gates pass: base evaluation works, the reproducibility gate is
accepted (exact_match), the real LoRA and ternary-QAT one-steps pass with finite
loss/gradients, both checkpoints reload in fresh processes, the base checkpoint is
unchanged, and repository integrity holds. `ready_for_dispatch_18b: true`.
