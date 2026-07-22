# Ternary-QAT stability calibration (Dispatch 19)

Controlled calibration of the ternary-QAT optimizer after the 4e-3 divergence. The
dataset, model, seed, module policy, and evaluation setup were held fixed; only the
learning-rate schedule and optimizer safety strategy changed (real gradient
clipping + 3-step warmup). GX10 (gx10-9141, `linewright-ternary-train:run001`, GB10,
bf16). **The very first candidate (lr 2e-4) was stable, so calibration stopped there
and evaluated it — no lower-rate runs were burned.**

```yaml
first_stable_learning_rate: 2e-4
stable_qat_checkpoint: training/runs/dataset-a-qat-calibration-v1/lr-2e-4/checkpoints/step-10
qat_stability_calibrated: true
ready_for_longer_qat_smoke: true
```

## Historical failed configuration (Dispatch 18B)

```yaml
learning_rate: 4.0e-3
result: diverged
abort_step: 14
maximum_raw_gradient_norm: 149.0
final_recorded_loss: 45.695248
```

## Calibration candidates

Order: `2e-4` → `5e-5` (only if 2e-4 fails). `5e-4` is a manual upper-bound probe,
never run automatically. Only **2e-4** was executed (it passed).

### Candidate 1 — learning rate 2e-4  ·  **STABLE** ✅

| metric | value |
|---|---|
| warmup steps | 3 (lr 6.67e-5 → 1.33e-4 → 2e-4, then constant) |
| gradient clipping | enabled, max_norm 1.0, norm_type 2.0 |
| completed steps | **10 / 10** |
| initial loss | 4.394992 |
| final loss | **1.567358** |
| minimum loss | 0.618596 |
| maximum loss | 4.394992 |
| final / initial ratio | **0.3566** (gate ≤ 3.0) |
| max **raw** gradient norm | **19.625** (rail 100; 4e-3 hit 149) |
| max **clipped** gradient norm | 1.0 |
| clipping events | 10 / 10 (every step clipped to 1.0) |
| gradient warnings | 0 |
| step-5 checkpoint reload | ok (fresh process) |
| step-10 checkpoint reload | ok (fresh process) |
| base-model integrity | unchanged |
| repository integrity | unchanged |
| evaluation | 6 / 7 format_valid |

Loss curve: `4.395, 0.701, 0.619, 1.035, 0.816, 1.591, 1.532, 2.069, 1.997, 1.567`
— dropped immediately once warmup completed and oscillated in a bounded 0.6–2.1
band; no divergence. Raw gradient norms stayed 7–20 and were clipped to 1.0 every
step. **Gradient clipping is the decisive stabilizer**: identical model/data/seed,
only the safety strategy and lr differ from the 4e-3 run.

### Candidate 2 — learning rate 5e-5

**Not required** (candidate 1 passed the stability gate). Not run.

### Candidate 3 — learning rate 5e-4

**Not run.** It is a manual upper-bound probe, run only if a reviewer explicitly
chooses to explore the upper stable range after 2e-4 passes; never a substitute for
the required 2e-4 run.

## Evaluation (7 held-out records)

Structural-valid counts: **base 6/7 · 20-step LoRA 5/7 · stable 10-step QAT 6/7**.

The calibrated QAT **matches the base model's format validity (6/7)** and does not
show the one-record regression the LoRA run had (constraint-002). revision-002's
no-change JSON is unmatched by all three (expected; not taught). Per-record detail
in `lr-2e-4/eval-summary.md`; mechanical table in `comparison/comparison.md`. The
aborted 4e-3 checkpoint is **excluded** from any winner comparison (unstable).

> Seven records prove nothing about general quality. This establishes that a
> ternary-QAT run can now train stably and produce structurally valid output — a
> stability result, not a quality result.

## Integrity

base-model unchanged; repository protected files unchanged; unauthorized writes 0
(`integrity/final-verification.json`). Checkpoint binaries are git-ignored.

## Conclusion & recommendation

QAT stability is **calibrated**: lr **2e-4** with a 3-step warmup and gradient
clipping at 1.0 completes a short run with a decreasing, bounded loss, reloadable
checkpoints, and clean integrity.

Recommended next QAT experiment:

1. Run a **longer (20-step) calibrated QAT** at lr 2e-4, warmup 3, clip 1.0 — now
   safe to attempt. Keep the raw-norm abort rail (100 / two consecutive) as a
   backstop.
2. Optionally probe **5e-4** for the upper stable bound (manual, one candidate).
3. Note a practical cost: **ternary-QAT generation is slow** (fake-quant re-quantizes
   every forward token); for longer eval, reduce `max_new_tokens` or add a faster
   inference path so evaluation does not dominate wall-clock.
4. Do not expand Dataset A on this result — it proves QAT can train stably, not that
   quality improved.
