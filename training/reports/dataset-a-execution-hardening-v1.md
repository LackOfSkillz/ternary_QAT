# Dataset A execution hardening v1 (Dispatch 18A)

Hardens the training pipeline before the first real Dataset A run. **No real
Dataset A gradient training occurred.** On this CPU host the pipeline is exercised
end to end with a deterministic **stub backend** (the 4B checkpoint and CUDA live on
the GX10 run001 image); the guards, integrity inventory, checkpoint/reload, run
manifests, reproducibility gate, and one-step rehearsal are all real.

```yaml
ready_for_dispatch_18b: true
```

## Actual CLI status

Real, executable entry points implemented (no longer placeholders):

| command | module |
|---|---|
| `python -m linewright.train --config … [--validate-only\|--dry-run\|--max-steps-override N]` | `linewright/train.py` |
| `python -m linewright.eval --harness … --target … --out …` | `linewright/eval.py` |
| `python -m linewright.compare --base … --lora … --ternary-qat … --out …` | `linewright/compare.py` |
| reproducibility gate | `linewright/reproducibility.py` |
| checkpoint reload (fresh process) | `linewright/reload_check.py` |
| one-step rehearsal | `linewright/rehearsal.py` |

Shared modules: `linewright/config.py`, `linewright/integrity.py`,
`linewright/runtime.py`, `linewright/backends.py` (`StubBackend` + `HFBackend`
placeholder for GX10). Registered in `pyproject.toml` (`linewright*`).

## Step-count reconciliation

Both real smoke configs use `max_steps: 20`, `checkpoint_interval_steps: 10`,
`eval_interval_steps: 10`, `logging_interval_steps: 1`, `eval_before_training:
true`. No active "60" reference remains (grep clean). A test asserts both configs
use 20 steps and that LoRA/QAT agree on all shared-critical fields.

## Configuration validation

`--validate-only` for both real configs prints:

```text
CONFIG VALID
INPUT HASHES VALID
TRAIN/EVALUATION SPLITS DISJOINT
AUTHORIZED OUTPUT PATH VALID
```

Rejections implemented: missing field, missing input file, hash mismatch,
output outside the authorized root, non-positive `max_steps`, invalid batch size,
train/eval overlap, `production_approved != false`, `experimental_use_only != true`,
and LoRA/QAT shared-field drift.

## Path-guard behavior

Authorized output root: `training/runs/dataset-a-smoke-v1/`. `AuthorizedWriter`
resolves absolute paths and rejects `../` traversal and absolute unauthorized
paths (tested). Symlink-escape rejection is implemented and tested **where
supported** (skipped on this Windows host: symlink creation requires privilege).

## Stop conditions (enforced in code)

| condition | enforcement | test |
|---|---|---|
| non-finite loss (NaN/±Inf) | `check_loss_finite` → abort | ✓ (3 cases) |
| non-finite gradient | `check_gradients_finite` → abort | ✓ (2 cases) |
| gradient explosion | `GradientMonitor` (max_global_norm 100.0, consecutive_step_limit 2): 1 breach warns, 2 consecutive abort | ✓ |
| stalled optimizer | `StallMonitor` | (monitor implemented) |
| checkpoint reload failure | fresh-process reload; invalid ⇒ run aborts | ✓ |
| invalid structured output | `structural_check` reports, never repairs | ✓ |
| structured no-change corruption | text-vs-source equality check | ✓ |
| unauthorized file modification | base-model + repository inventory verification | ✓ |

Integration: an injected NaN loss aborts a full synthetic run
(`status=aborted`, `stop_reason=loss_non_finite`, exit 2).

## Integrity inventory

- **Base-model inventory** (rehearsal stub base): file count **2**, root hash
  `c97ac4e0506f0a35…`. Pre/post verification: **ok = true** (no changed bytes, no
  missing file, no new file, no symlink change). SHA-256 authoritative; mtime is a
  supporting signal only.
- **Repository inventory**: pre/post verification **ok = true** — HEAD unchanged,
  no protected tracked file changed (`datasets/.../compiled/*.jsonl`,
  `prompts/*.txt`, `ternary/*.py`), no unexpected file outside authorized run
  paths. New files appeared only under `training/runs/dataset-a-smoke-v1/`.

## One-step rehearsal (Part 10)

- config: disposable synthetic 2-train / 1-eval dataset + stub base, `max_steps`
  overridden to **1**, output under the authorized run root.
- completed steps: **1**; loss finite (synthetic 1.0/(step+1)); status `completed`.
- disposable checkpoint saved and **reloaded in a fresh process** → `ok = true`,
  non-empty output.
- base-model inventory unchanged; repository verification ok.
- **The real 28-record Dataset A train file was NOT used for gradients.**

## Baseline evaluation + reproducibility

- base evaluation run twice on the 7 held-out records with the pinned system
  prompt and generation settings (`eval-run-1.json`, `eval-run-2.json`); both files
  are **byte-identical** (sha256 `e77c716ddc2742d0…`).
- record count 7; format_valid 3/7 (the 3 prose-target records; the 4 structured
  records are honestly recorded invalid because the **stub** does not emit JSON/YAML
  — the real 4B model is expected to; invalid output is reported, never repaired).
- reproducibility disposition: **exact_match** (exact 7, normalized 0, materially
  equivalent 0, failed 0; accepted = true).

## Environment

`python 3.11.0`, `torch 2.13.0+cpu`, `transformers 5.14.1`, `peft 0.19.1`,
`accelerate 1.14.0`; **CUDA available: false**, device `cpu`. This is the CPU
hardening host; the real 4B run uses the GX10 run001 image (bf16/CUDA verified
there per the smoke configs' compatibility evidence).

## Limitations

- The real 4B base-model evaluation + reproducibility gate must be **re-run on the
  GX10** with `backend: hf` as the **first action of Dispatch 18B**; this dispatch
  proves the pipeline with a deterministic stub, not the real model's outputs.
- Stub structured outputs are invalid by design (they exercise plumbing, not
  quality); do not read the 3/7 format-valid figure as a model result.

## Confirmations

- No real Dataset A gradient training occurred.
- No base checkpoint changed; no checkpoint binaries committed.
- No merge or `master` modification occurred.

## Queue-discipline note (Part 14)

VOICE-P0A status was not used to alter or bypass any technical safety check. Actual
Dispatch 18B execution remains a Gary scheduling decision.

## Readiness

All hardening gates pass. `ready_for_dispatch_18b: true`. The first 18B action is
the real-model baseline evaluation-twice + reproducibility gate on the GX10, then
LoRA smoke training only if that is accepted.
