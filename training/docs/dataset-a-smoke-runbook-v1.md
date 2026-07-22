# Dataset A smoke-training runbook v1

Exact, paste-from-repo-root commands for the first end-to-end LoRA + ternary-QAT
smoke test on the `dataset-a-experimental-v1` freeze. The `linewright.*` commands
are **real, executable entry points** (see `training/reports/dataset-a-execution-
hardening-v1.md`). Pipeline validation only; never production quality. Smoke results
must never be represented as production evidence.

- Repo root: `C:\Dev\ternary_QAT` (host) / `/workspace` (GX10 container).
- Backend: `stub` on a plain CPU host (pipeline rehearsal); `hf` on the GX10 run001
  image (real 4B model). Select with `--backend`.
- Authorized output root: `training/runs/dataset-a-smoke-v1/`.

Pinned artifacts:

```text
train.jsonl        97778f2a…    evaluation.jsonl   0f3ae426…
manifest.json      9d067c32…    system prompt      038d9ab8…
```

Steps 1–11 were completed in **Dispatch 18A** on the CPU host with the stub backend.
The real **HFBackend is implemented and verified on the GX10** (Dispatch 18A.1):
base evaluation ×2 reproducible (exact_match), and real LoRA + ternary-QAT one-step
rehearsals passed with finite loss/gradients, fresh-process checkpoint reloads, an
unchanged base checkpoint, and clean repository integrity. See
`training/reports/dataset-a-hf-backend-verification-v1.md`. Steps 12–18 (the real
20-step runs) are **reserved for Dispatch 18B** and run on the GX10 with
`--backend hf`.

### Verified GX10 invocation (Dispatch 18A.1)

```bash
docker run --rm --gpus all --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
  -v /home/gary/projects/ternary_QAT:/workspace \
  -v /home/gary/linewright-model-training/hf-cache:/workspace/hf-cache \
  -w /workspace -e PYTHONPATH=/workspace -e PYTHONDONTWRITEBYTECODE=1 \
  -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
  linewright-ternary-train:run001 \
  python -m linewright.hf_verify \
    --base-model-dir /workspace/hf-cache/prism-ml/Ternary-Bonsai-4B-unpacked
```

---

## Dispatch 18A — completed (pipeline hardening, stub backend)

### 1. Git and environment verification
```bash
.venv/Scripts/python.exe -c "import torch,transformers,peft;print(torch.__version__,transformers.__version__,peft.__version__)"
git rev-parse --abbrev-ref HEAD && git rev-parse HEAD
```

### 2. Config validation
```bash
.venv/Scripts/python.exe -m linewright.train --config training/configs/dataset-a-lora-smoke-v1.yaml --validate-only
.venv/Scripts/python.exe -m linewright.train --config training/configs/dataset-a-ternary-qat-smoke-v1.yaml --validate-only
```
Expect: `CONFIG VALID / INPUT HASHES VALID / TRAIN/EVALUATION SPLITS DISJOINT / AUTHORIZED OUTPUT PATH VALID`.

### 3. Dataset validation
```bash
.venv/Scripts/python.exe datasets/dataset-a/scripts/validate_dataset_a.py --root datasets/dataset-a
```

### 4. Deterministic compilation
```bash
.venv/Scripts/python.exe datasets/dataset-a/scripts/compile_dataset_a.py \
  --root datasets/dataset-a --out-subdir experimental-v1 \
  --freeze-id dataset-a-experimental-v1 \
  --system-prompt datasets/dataset-a/prompts/linewright-training-system-v1.txt
```

### 5. Compiled-artifact validation
```bash
.venv/Scripts/python.exe datasets/dataset-a/scripts/validate_compiled.py --root datasets/dataset-a --out-subdir experimental-v1
```
Confirm train sha256 `97778f2a…`, eval `0f3ae426…`. **Stop if hashes differ.**

### 6. Base-model integrity inventory  &  ### 7. Repository integrity inventory
Captured automatically by `linewright.train` (before/after) under
`training/runs/dataset-a-smoke-v1/integrity/`. On GX10 pass `--base-model-dir` (or
set `model.base_model_path`) to the real base checkpoint so it is inventoried and
protected.

### 8. Base evaluation run 1  &  ### 9. Base evaluation run 2
```bash
.venv/Scripts/python.exe -m linewright.eval --harness training/evaluation/dataset-a-smoke-eval-v1.yaml \
  --target base --backend stub --out training/runs/dataset-a-smoke-v1/base/eval-run-1.json
.venv/Scripts/python.exe -m linewright.eval --harness training/evaluation/dataset-a-smoke-eval-v1.yaml \
  --target base --backend stub --out training/runs/dataset-a-smoke-v1/base/eval-run-2.json
```
On GX10 use `--backend hf`. Do not silently repair invalid model output.

### 10. Reproducibility gate
```bash
.venv/Scripts/python.exe -m linewright.reproducibility \
  --run1 training/runs/dataset-a-smoke-v1/base/eval-run-1.json \
  --run2 training/runs/dataset-a-smoke-v1/base/eval-run-2.json \
  --out training/runs/dataset-a-smoke-v1/base/eval-reproducibility.json
```
Require disposition `exact_match` or `normalized_match` (or `materially_equivalent`
**with** a documented serving/kernel-nondeterminism reason). **Abort progression on
`failed`.** 18A result (stub): `exact_match`.

### 11. One-step rehearsal
```bash
.venv/Scripts/python.exe -m linewright.rehearsal
```
Expect: 1 step completed, disposable checkpoint reloaded in a fresh process,
base-model inventory unchanged, repository verification ok. The real 28-record
train file is never used for gradients here.

---

## Dispatch 18B — reserved (real training, GX10, `--backend hf`)

> Precondition (met in Dispatch 18A.1): steps 8–10 were run on the GX10 with
> `--backend hf` against the real 4B model and the reproducibility gate was accepted
> (exact_match), and the real LoRA + ternary-QAT one-step rehearsals passed. The
> 20-step runs below remain disabled until Gary schedules Dispatch 18B.

### 12. LoRA smoke training
```bash
python -m linewright.train --config training/configs/dataset-a-lora-smoke-v1.yaml --backend hf
```
20 steps, checkpoints at 10 and 20, eval before/mid/after. Abort on any stop
condition (non-finite loss/grad, gradient explosion, checkpoint reload failure).

### 13. LoRA reload and evaluation
```bash
python -m linewright.eval --harness training/evaluation/dataset-a-smoke-eval-v1.yaml \
  --target lora --backend hf --out training/runs/dataset-a-smoke-v1/lora/eval.json
```

### 14. Integrity verification
Confirm `integrity/base-model-verification.json` and `repository-verification.json`
report `ok: true`. **Stop if the base checkpoint changed.**

### 15. Ternary-QAT smoke training — only if LoRA passed
```bash
python -m linewright.train --config training/configs/dataset-a-ternary-qat-smoke-v1.yaml --backend hf
```
Abort if QAT modifies the base checkpoint or unrelated files.

### 16. QAT reload and evaluation
```bash
python -m linewright.eval --harness training/evaluation/dataset-a-smoke-eval-v1.yaml \
  --target ternary-qat --backend hf --out training/runs/dataset-a-smoke-v1/ternary-qat/eval.json
```

### 17. Final integrity verification
Re-verify base-model + repository inventories after both runs.

### 18. Comparison report
```bash
python -m linewright.compare \
  --base training/runs/dataset-a-smoke-v1/base/eval.json \
  --lora training/runs/dataset-a-smoke-v1/lora/eval.json \
  --ternary-qat training/runs/dataset-a-smoke-v1/ternary-qat/eval.json \
  --out training/runs/dataset-a-smoke-v1/comparison/comparison.md
```

---

## Stop conditions (abort immediately; enforced in code)

train/eval leakage · NaN/±Inf loss · non-finite gradient · gradient explosion
(2 consecutive breaches) · checkpoint cannot reload · invalid assistant output
format · corrupted structured no-change output · base-model evaluation not
reproducible · compiled hashes differ · QAT modifies the base checkpoint or
unrelated files.
