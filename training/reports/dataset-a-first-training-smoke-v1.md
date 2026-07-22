# Dataset A first real training smoke (Dispatch 18B)

The first **real gradient training** on the frozen Dataset A experimental split, on
the GX10 (gx10-9141, `linewright-ternary-train:run001`, NVIDIA GB10, bf16). LoRA
first; ternary-QAT gated behind LoRA. This is an experimental **pipeline** smoke
test — **not** proof of model-quality improvement, and 7 held-out records prove
nothing about general quality.

> **Overall: passed_with_warnings.** The LoRA pipeline ran end to end (load → train
> → save → reload → evaluate). The ternary-QAT run **diverged and was aborted by the
> gradient-explosion safety rail** — a real training-instability finding, not a
> pipeline defect. The base checkpoint and repository were untouched throughout.

## Pipeline result

| stage | result |
|---|---|
| base model load | ok (Qwen3ForCausalLM, chat template, bf16) |
| LoRA train (20 steps) | **completed** |
| LoRA save (step-10, step-20) | ok |
| LoRA reload (fresh process) | ok (both checkpoints) |
| LoRA evaluation (7 records) | ok |
| ternary-QAT train (20 steps) | **aborted at step 14 — gradient_explosion** |
| ternary-QAT save/reload/eval | not reached |
| base-model + repository integrity | **unchanged** (unauthorized writes 0) |

## Training curves

**LoRA** (lr 2e-4, 252 modules, 33.0 M trainable / 0.81 %):
- loss **4.403287 → 2.778305** (min **0.086233**) — real, monotone-ish decrease.
- max gradient norm **3.628492**; gradient warnings **0**.
- peak CUDA **19259 MB**; both checkpoints reloaded in fresh processes.

**ternary-QAT** (lr 4e-3, 254 modules replaced, tie preserved, ~4.02 B trainable):
- loss **4.394992 → 45.695248** at step 13 — **diverged** (grew, not shrank).
- per-step gradient norms: `19.6, 125.5, 32.2, 149.0, 87.5, 100.0, 82.0, 74.5,
  120.5, 83.5, 136.0, 89.5, 106.5, …` — repeatedly above the 100.0 rail.
- **6 gradient warnings**; **aborted at step 14** on two consecutive norms > 100
  (steps 13 → 14). The threshold was **not** changed to avoid the abort.

## Evaluation (7 held-out records)

Structural-valid counts: **base 6/7 · LoRA 5/7 · QAT N/A (aborted)**.

| record | task | base | LoRA |
|---|---|---|---|
| dsa-boundary-001 | fiction_boundary | ✓ | ✓ |
| dsa-canon-003 | canon_extraction | ✓ | ✓ |
| dsa-constraint-002 | constraint_check | ✓ | ✗ |
| dsa-revision-002 | focused_revision (no-change) | ✗ | ✗ |
| dsa-revision-007 | focused_revision | ✓ | ✓ |
| dsa-revision-018 | focused_revision | ✓ | ✓ |
| dsa-scene-002 | scene_contract | ✓ | ✓ |

Per-record detail in `training/runs/dataset-a-smoke-v1/lora/eval-summary.md`;
mechanical table in `training/runs/dataset-a-smoke-v1/comparison/comparison.md`.

## Behavioral summary (cautious; 7 records)

- **canon extraction / constraint checking:** base emitted valid JSON on canon-003
  and constraint-002; after 20 LoRA steps constraint-002's output stopped parsing
  (a small **regression** on one record).
- **no-change restraint (revision-002):** neither base nor LoRA reproduced the exact
  `{"changed": false, "text": <source>}` object — expected; the model has not been
  taught the protocol in 20 steps.
- **anti-slop revision / scene-contract / fiction-boundary:** format validity held
  for both base and LoRA on the remaining records.
- No behavioral claim is warranted from seven records; this is a plumbing result.

## Interpretation

Separate the two clearly:

- **Pipeline success (LoRA):** proven. The verified HF backend loaded the pinned 4B,
  computed assistant-only loss, ran 20 real optimizer steps with a decreasing loss,
  saved two checkpoints, reloaded them in fresh processes, and evaluated on the
  held-out set — with the base checkpoint and repository untouched.
- **Quality improvement:** **not** demonstrated. LoRA format validity went 6 → 5
  (one regression); no improvement is shown. This is a smoke test, not a quality
  benchmark.
- **QAT finding:** full ternary-QAT with the provisional lr 4e-3 (~20× LoRA) **is
  unstable** — the loss diverged and gradients exploded within ~14 steps. The safety
  rail caught it exactly as designed. The one-step rehearsal (grad 96.5) had already
  signalled proximity to the rail.

## Recommendation for the next experiment

1. **Reduce the ternary-QAT learning rate substantially** (e.g. 2e-4–5e-4, at or
   near the LoRA range) and/or **add gradient clipping** (`max_grad_norm` ≈ 1.0)
   before retrying the QAT smoke. The current 4e-3 is too aggressive for full
   ternary STE updates on the 4B.
2. Consider a **warmup** and a **lower effective step count sanity pass** for QAT.
3. LoRA is the stable path; if the next goal is a behavioral delta, iterate LoRA
   (more steps / curated data) while QAT stability is calibrated separately.
4. Do not expand Dataset A on the basis of this smoke; it proves plumbing, not
   quality.

## Confirmations

- The real **28-record** training split was used for gradients.
- The **7** evaluation records never entered gradients.
- **No base-model file changed** (integrity ok). **No checkpoint binaries committed.**
- **No merge or `master` modification.**
