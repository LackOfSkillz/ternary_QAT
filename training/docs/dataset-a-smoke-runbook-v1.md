# Dataset A smoke-training runbook v1

Exact, paste-from-repo-root commands for the first end-to-end LoRA + ternary-QAT
smoke test on the `dataset-a-experimental-v1` freeze. **This dispatch does not run
any of steps 5–10.** The objective is to prove the pipeline works, not to produce
quality. Smoke results must never be represented as production evidence.

- Repo root: `C:\Dev\ternary_QAT` (host) / `/workspace` (GX10 container).
- Python: host `.venv\Scripts\python.exe`; container `linewright-ternary-train:run001`.
- Configs: `training/configs/dataset-a-lora-smoke-v1.yaml`,
  `training/configs/dataset-a-ternary-qat-smoke-v1.yaml`,
  `training/evaluation/dataset-a-smoke-eval-v1.yaml`.

Frozen artifacts (hashes are pinned in the configs and manifests):

```text
datasets/dataset-a/compiled/experimental-v1/train.jsonl        sha256 97778f2a…
datasets/dataset-a/compiled/experimental-v1/evaluation.jsonl   sha256 0f3ae426…
datasets/dataset-a/compiled/experimental-v1/manifest.json      sha256 9d067c32…
datasets/dataset-a/prompts/linewright-training-system-v1.txt   sha256 038d9ab8…
```

---

## 1. Environment verification

```bash
# host
.venv/Scripts/python.exe -c "import torch, transformers, peft; print(torch.__version__, transformers.__version__, peft.__version__)"
# GX10 (inside the run001 image) — record compat evidence, do NOT assume install == working stack
python -c "import torch; print('cuda', torch.cuda.is_available(), 'bf16', torch.cuda.is_bf16_supported())"
```

Expected: CUDA True, bf16 True on the GX10. Stop if either is False.

## 2. Dataset validation

```bash
.venv/Scripts/python.exe datasets/dataset-a/scripts/validate_dataset_a.py --root datasets/dataset-a
```

Expected: `ALL DATASET A RECORDS VALID` (35 records). Stop on any problem.

## 3. Compilation

```bash
.venv/Scripts/python.exe datasets/dataset-a/scripts/compile_dataset_a.py \
  --root datasets/dataset-a --out-subdir experimental-v1 \
  --freeze-id dataset-a-experimental-v1 \
  --system-prompt datasets/dataset-a/prompts/linewright-training-system-v1.txt
```

Expected: `compiled train=28 eval=7 pref=18`. Outputs under
`datasets/dataset-a/compiled/experimental-v1/`.

## 4. Compiled-artifact hash verification

```bash
.venv/Scripts/python.exe datasets/dataset-a/scripts/validate_compiled.py \
  --root datasets/dataset-a --out-subdir experimental-v1
# and confirm bytes are unchanged vs the committed freeze:
sha256sum datasets/dataset-a/compiled/experimental-v1/train.jsonl \
          datasets/dataset-a/compiled/experimental-v1/evaluation.jsonl
```

Expected: `ALL COMPILED ARTIFACTS VALID`; train sha256 `97778f2a…`, eval `0f3ae426…`.
**Stop if hashes differ unexpectedly.**

## 5. Base-model evaluation (baseline, before any training)

```bash
python -m linewright.eval \
  --harness training/evaluation/dataset-a-smoke-eval-v1.yaml \
  --target base \
  --out training/runs/dataset-a-smoke-v1/base/eval.json
```

Expected: `base/eval.json` with per-record generations + behavioral-check results.
This baseline must be reproducible (re-run and compare) before proceeding.

## 6. LoRA smoke training

```bash
python -m linewright.train --config training/configs/dataset-a-lora-smoke-v1.yaml
```

Expected: ~20 optimizer steps (~5 epochs over 28 rows), 2 checkpoints under
`training/runs/dataset-a-smoke-v1/lora/checkpoints/` (git-ignored), before/after
eval. **Stop** on NaN/inf loss, exploding grads, or a checkpoint that cannot reload.

## 7. LoRA evaluation

```bash
python -m linewright.eval \
  --harness training/evaluation/dataset-a-smoke-eval-v1.yaml \
  --target lora \
  --out training/runs/dataset-a-smoke-v1/lora/eval.json
```

## 8. Ternary-QAT smoke training

```bash
python -m linewright.train --config training/configs/dataset-a-ternary-qat-smoke-v1.yaml
```

Expected: same step budget as LoRA; ternary swap_linear applied (embed/lm_head kept
full precision). **Stop** if QAT modifies the base checkpoint on disk or any
unrelated files.

## 9. Ternary-QAT evaluation

```bash
python -m linewright.eval \
  --harness training/evaluation/dataset-a-smoke-eval-v1.yaml \
  --target ternary-qat \
  --out training/runs/dataset-a-smoke-v1/ternary-qat/eval.json
```

## 10. Comparison report generation

```bash
python -m linewright.compare \
  --base training/runs/dataset-a-smoke-v1/base/eval.json \
  --lora training/runs/dataset-a-smoke-v1/lora/eval.json \
  --ternary-qat training/runs/dataset-a-smoke-v1/ternary-qat/eval.json \
  --out training/runs/dataset-a-smoke-v1/comparison/comparison.md
```

Expected: a small trackable `comparison/comparison.md`. Large binaries and logs are
git-ignored; only JSON/MD/YAML metrics are committed.

> `linewright.train` / `linewright.eval` / `linewright.compare` are the intended
> entry points; wire them to the existing `ternary/` package (linear.py, ste.py,
> swap.py) and the trainer stack verified on the run001 image. Substitute the
> project's actual trainer invocation if it differs — the configs, splits, hashes,
> and stop conditions are the contract.

---

## Stop conditions (abort immediately)

- train/evaluation leakage detected
- loss is NaN or infinite
- gradients explode
- a checkpoint cannot reload
- assistant output format becomes invalid
- structured no-change output is corrupted (revision-002 / revision-019)
- base-model evaluation cannot be reproduced
- compiled hashes differ unexpectedly
- QAT modifies unrelated files or the base checkpoint
