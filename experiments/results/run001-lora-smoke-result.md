# Run 1 — LoRA Smoke Test Result

## Objective

Prove the conventional-LoRA training loop mechanically on one GX10: load →
train → save → checkpoint → reload adapter → generate. **No literary-quality
claim is made**, and no merge, GGUF conversion, or Q2_0 quantization was
performed.

**Result: PASS** — the pipeline completed end to end and the adapter verifies.

## Dataset

- Train: 80 synthetic examples (20 each: canon_extraction, constraint_check, focused_revision, fiction_compliance)
- Eval (held out): 24 synthetic examples (6 each)
- train sha256: `f2a3ef4dee6c725a2e7ade6fba9b59d8d046967679ce96fb59ec267b72614fdd`
- eval sha256: `44f92747520fc0591920e2da29ed0a5bd76645d18a351730787487f2835cf165`
- All examples synthetic; no manuscript / author-derived / copyrighted content. Eval `excluded_from_training: true`.

## Environment

- Host `gx10-9141` (GB10, driver 580.159.03, CUDA 13.0), Ubuntu 24.04 aarch64.
- Image `linewright-ternary-train:run001` (`sha256:31d26c6b…a724eb`); base `nvcr.io/nvidia/pytorch:25.11-py3`.
- torch 2.10.0a0+nv25.11, transformers 5.14.1, peft 0.19.1, accelerate 1.14.0. bf16, SDPA.
- Launch commit: `252bb06`. Config sha256: `f4b0f51e…4b876`.

## Training configuration

- Base: `prism-ml/Ternary-Bonsai-4B-unpacked` @ `4485fae7a00129467b9329b738110d88b2942a1a`
- Conventional LoRA (no ternary swap_linear): r=16, α=32, dropout=0.05
- Target modules matched: `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` (252 adapter layers)
- **Trainable params: 33,030,144 / 4,054,814,720 (0.8146%)**
- max_seq 2048, micro_batch 1, grad_accum 8, max_steps 100, lr 2e-4, cosine, warmup 0.03, adamw_torch, grad checkpointing, seed 20260721, workers 0, use_cache=False
- Loss: **assistant-response tokens only** (prompt masked to -100) — verified in dry-run (e.g. 42 of 113 tokens trained).

## Timing & throughput

- Start 2026-07-21T14:23:14Z; end ≈14:26:30Z.
- train_runtime **184.8 s** (~3 min); **4.328 samples/s**, **0.541 steps/s** (~1.77 s/step).
- Peak unified memory: **8.851 GB** train / 8.308 GB verify (of 121 GiB).

## Loss progression (logged every 10 steps)

| step | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 100 |
|---|---|---|---|---|---|---|---|---|---|---|
| train loss | 1.265 | 0.7977 | 0.3858 | 0.1449 | 0.02567 | 0.005719 | 0.002402 | 0.00182 | 0.001527 | 0.001447 |

- eval_loss: **1.22** (step 50) → **1.314** (step 100). Mean train_loss 0.2632.
- The train loss collapses toward zero and eval loss ticks up — **heavy overfitting on 80 examples over 10 epochs, which is the expected and acceptable behavior for a pipeline smoke test.**

## Checkpoints

- `checkpoint-50`, `checkpoint-100`, and final adapter saved under `/workspace/checkpoints/run001-lora-smoke`.
- Adapter: `adapter_model.safetensors` (132 MB) + `adapter_config.json`.

## Adapter verification

- Base + adapter loaded (not merged); adapter r16/α32/dropout0.05, 7 target modules, task CAUSAL_LM, weights present.
- Generation on a held revision prompt returned **"Nothing could change it."** — the exact trained target — confirming the adapter loads and affects output. Output finite and nonempty.
- No tied-weight error, no missing-target-module error. Peak mem 8.308 GB.

## Warnings

- Benign: `warmup_ratio`/`logging_dir` deprecation notices (transformers 5.x); `torch_dtype`→`dtype` notice; runpy warning on `python -m ternary.ste`.
- FlashAttention not used (SDPA) — GB10 sm_121 unsupported by FA3.

## Failures & corrections (all before/around the run)

1. **Editable install** failed (setuptools flat-layout) → fixed with `[tool.setuptools.packages.find] include=["ternary*"]`.
2. **peft ↔ torchao**: NGC torchao 0.14 caused peft 0.19.1 to raise in LoRA dispatch → removed torchao from the image (unused by Run 1); image rebuilt.
3. **Chat-template tokenization** returned non-int objects in transformers 5.x → render with `tokenize=False` then tokenize the string.
4. **Adapter-verify generation** passed a BatchEncoding positionally → fixed to `return_dict=True` + `**enc` (committed as `a0d5699`).
Each fix was re-validated (dry-run / re-run) before proceeding. Training itself ran once, cleanly, exit 0.

## Statement

No adapter merge, no GGUF conversion, and no Q2_0 quantization were performed.
No claim of prose improvement is made. Run 1's sole objective — proving the
training loop — is met.
