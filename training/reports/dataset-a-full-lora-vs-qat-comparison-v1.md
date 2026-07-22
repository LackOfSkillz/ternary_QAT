# Full Dataset A: LoRA vs. calibrated ternary-QAT (Dispatch 20)

A complete, start-to-finish controlled comparison run from a **single untouched base
checkpoint**: fresh base evaluation, a fresh 20-step LoRA run, a fresh 20-step
calibrated ternary-QAT run, checkpoint save/reload/eval for each, and a four-way
structural comparison. GX10 (`linewright-ternary-train:run001`, GB10, bf16).

> **Experimental only. Not production. Not a quality claim.** Seven held-out records
> cannot establish general quality. This dispatch proves that the *pipeline* runs
> end-to-end — load → train → save → reload → evaluate — for both methods, and that
> the ternary-QAT stability calibration (Dispatch 19) **holds for a full 20-step run**.
> It is a stability/plumbing result, not evidence that either method improved the model.

## Experimental controls (what makes this comparison interpretable)

- **Both methods start from the same untouched base.** The QAT run did **not** resume
  the LoRA checkpoint, the failed 4e-3 QAT checkpoint, or the successful 10-step
  calibration checkpoint. Each phase is a separate container that reloads the base
  model fresh. Verified: `lora_did_not_feed_qat: true`,
  `prior_qat_calibration_not_resumed: true`, `both_from_untouched_base: true`.
- **Shared config-critical fields** (seed 20260721, max_steps 20, effective batch 8,
  seq 2048, same train/eval files + base revision). Documented allowed differences:
  learning rate is identical here (both 2e-4), and QAT adds the `ternary_qat` module
  policy plus gradient clipping + 3-step warmup. LoRA uses neither warmup nor clipping.
- **Accepted base evaluation.** The base model was evaluated twice and gated for
  reproducibility before any training: disposition **`exact_match`** — both runs are
  byte-identical (`run1_raw_hash == run2_raw_hash`, all 7 records `raw_equal`).

## Results at a glance

| | base | 20-step LoRA | 10-step QAT (contextual) | 20-step QAT |
|---|---|---|---|---|
| structural-valid (of 7) | **6** | 4 | **6** | 3 |
| completed steps | — | 20/20 | 10/10 | 20/20 |
| initial → final loss | — | 4.403 → 2.787 | 4.395 → 1.567 | 4.395 → 3.454 |
| final / initial | — | 0.633 | 0.357 | **0.786** |
| min loss | — | 0.084 | 0.619 | 0.222 |
| max **raw** grad norm | — | 3.46 | 19.6 | **35.5** (rail 100) |
| gradient clipping | — | none (not configured) | to 1.0 every step | to 1.0 every step |
| gradient warnings | — | 0 | 0 | 0 |
| peak CUDA | — | 19.3 GB | — | **48.5 GB** |
| step-10 / step-20 reload | — | ok / ok | ok / — | ok / ok |

The 10-step QAT column is the prior Dispatch-19 calibration checkpoint, included only
for context. It was trained under identical model/data/seed but is a **different run**
(10 steps), so it is not a head-to-head competitor — it is the "less training" anchor.

## Stability — the actual finding

**The calibrated ternary-QAT trained stably for the full 20 steps.** With lr 2e-4, a
3-step warmup (lr 6.67e-5 → 1.33e-4 → 2e-4, confirmed in the step log), and gradient
clipping to max-norm 1.0:

- all 20 steps completed (`reason=max_steps_reached`), every loss and gradient finite;
- **raw** gradient norms rose to **35.5** (step 19) — higher than the 10-step run's
  19.6, but well under the 100 abort rail; the 4e-3 divergence had hit **149**;
- every step was clipped to exactly 1.0 (20/20), **zero** gradient warnings;
- final/initial loss ratio **0.786** (stability gate ≤ 3.0) — bounded, not diverging;
- both checkpoints (step-10, step-20) reloaded cleanly in a fresh process.

`stability_passed: true`. The loss oscillated in a bounded band (min 0.222, max 4.395)
with the same shape as the LoRA curve — expected, since both see the same examples in
the same order under the same seed. **Gradient clipping remains the decisive
stabilizer**: the raw norms (7–35) would have been destabilizing unclipped, exactly as
in the 4e-3 run, but clamping to 1.0 held the trajectory.

## Structural quality — more steps *hurt* structure here

Structural validity (does the output parse in the expected prose/JSON/YAML format) fell
with more training: base **6/7** and 10-step QAT **6/7**, but 20-step LoRA **4/7** and
20-step QAT **3/7**. Per record:

| record | task | base | LoRA-20 | QAT-10 | QAT-20 |
|---|---|---|---|---|---|
| dsa-boundary-001 | fiction_boundary (prose) | ✓ | ✓ | ✓ | ✓ |
| dsa-canon-003 | canon_extraction (json) | ✓ | ✗ | ✓ | ✗ |
| dsa-constraint-002 | constraint_check (json) | ✓ | ✗ | ✓ | ✗ |
| dsa-revision-002 | focused_revision (no-change json) | ✗ | ✗ | ✗ | ✗ |
| dsa-revision-007 | focused_revision (prose) | ✓ | ✓ | ✓ | ✓ |
| dsa-revision-018 | focused_revision (prose) | ✓ | ✓ | ✓ | ✓ |
| dsa-scene-002 | scene_contract (yaml) | ✓ | ✓ | ✓ | ✗ |

This is **overfitting**, and it was expected: 20 steps at effective batch 8 over 28
training rows is ~5 epochs. Both 20-step runs memorized `dsa-revision-007` **verbatim**
(output byte-for-byte equals the gold opening) — a memorization signal, not a
generalization win. The prose tasks (boundary-001, revision-007, revision-018) survived
in all four columns; the structured-format tasks are where the 20-step runs regressed:

- **QAT-20 regressions are schema drift, not collapse.** canon-003 produced clean JSON
  but with the wrong keys (`speaker`/`claim` instead of `entity`/`fact`); scene-002
  produced YAML that failed to parse cleanly; constraint-002 produced valid JSON with
  extra `constraint_ids`. The text stays coherent throughout — there is no gibberish or
  divergence in the generations, only structural/schema mismatch.
- **`format_valid` overstates quality even for the "winners".** LoRA's boundary-001 is
  counted valid (it is prose) but the content is degenerate repetition ("She's in the
  front room. She's in the front room."). A parseable-format check is not a quality
  rubric. Behavioral scoring is deferred to human Gate review.
- **No one solves the no-change case** (revision-002): the task wants a
  `{"changed": false, ...}` wrapper preserving the original; base, LoRA, and both QAT
  runs all emit bare prose. The base can't do it either — it isn't taught by this data.

Head-to-head at equal training (20 steps), **LoRA-20 (4/7) edged QAT-20 (3/7)** on
structural validity — the single-record difference being scene-002 (LoRA's YAML parsed,
QAT's did not). Neither is a quality verdict; both regressed below the base.

## Cost note — ternary-QAT evaluation is slow

The QAT evaluation dominated wall-clock. Fake-quant re-quantizes all 398 ternarized
modules on **every** generated token; with `max_new_tokens: 512` greedy over 7 records
and structured tasks that often run to the token cap, the QAT eval alone took roughly
**40–50 minutes** (vs. seconds-to-minutes for base/LoRA). Peak CUDA for QAT training was
**48.5 GB** (vs. 19.3 GB for LoRA) — fake-quant holds FP master weights alongside the
quantized copies. This is the practical cost flagged in the Dispatch-19 report. For any
longer QAT evaluation, reduce `max_new_tokens` or add a faster (packed/real-quant)
inference path so evaluation does not dominate the run.

## Integrity

`integrity/final-verification.json` (results echoed in `full-comparison-summary.json`):

- `base_model_unchanged: true` — SHA-256 inventory identical before → after-lora →
  after-qat → final;
- `repository_protected_files_unchanged: true` (datasets, configs, `ternary/`,
  `linewright/`);
- `unauthorized_writes: 0`;
- `lora_step_20_reload_ok: true`, `qat_step_20_reload_ok: true`;
- base / LoRA / QAT evaluations all completed.

Checkpoint binaries (253 MB LoRA, 15 GB QAT) and the machine-specific integrity/manifest
inventories are git-ignored; their verdicts are preserved in the tracked summary JSONs.

## Conclusion & recommendation

**Overall: passed with warnings.** The full pipeline ran end-to-end for both methods
from one untouched base; both trained to completion with finite losses and reloadable
checkpoints; base reproducibility was bit-exact; integrity is clean. The calibrated
ternary-QAT is confirmed **stable at 20 steps** — the Dispatch-19 calibration
generalizes past 10 steps.

Warnings (not failures):
1. **Structural quality regressed with more steps** for both methods (overfitting on 28
   rows). This is expected and is *not* a defect in the training code.
2. **QAT evaluation is slow and memory-heavy** (fake-quant); future QAT eval needs a
   faster inference path or a smaller token budget.

Recommended next steps:
- Do **not** expand Dataset A or draw quality conclusions from this. Seven records
  prove stability and plumbing, nothing about general quality.
- If a longer QAT smoke is attempted, keep lr 2e-4 / warmup 3 / clip 1.0 and the 100
  raw-norm abort rail, and add a faster QAT inference path before scaling eval.
- Behavioral (rubric) scoring of these generations is deferred to human Gate review;
  the per-record outputs are in `comparison/per-record-comparison.json` and the two
  `eval-summary.md` files.

## Evidence (tracked)

- `training/runs/dataset-a-full-comparison-v1/full-comparison-summary.json` — master result
- `.../phase-lora-summary.json`, `.../phase-qat-summary.json` — per-phase metrics + verdicts
- `.../base/eval-reproducibility.json` — base accept gate (`exact_match`)
- `.../comparison/comparison.md`, `.../per-record-comparison.json`, `.../training-curves.json`
- `.../base/eval.json`, `.../lora/eval.json`, `.../ternary-qat/eval.json` + `eval-summary.md`
- configs: `training/configs/dataset-a-lora-full-comparison-v1.yaml`,
  `training/configs/dataset-a-ternary-qat-full-comparison-v1.yaml`
- orchestrator: `linewright/full_comparison.py`
