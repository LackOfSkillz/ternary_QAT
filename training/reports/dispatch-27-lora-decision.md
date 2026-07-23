# Dispatch 27 Phase B — LoRA Advancement Decision

**Branch: `revise_Dataset_A3`. LoRA does NOT advance. QAT NOT authorized (and not started).**
Machine-readable: [`dispatch-27-lora-decision.yaml`](dispatch-27-lora-decision.yaml). Provisional;
no production-ready claim; no weights published; `master` untouched.

## The evidence — three independent measurements, all NEUTRAL

1. **Mechanical checkpoint curve (14 frozen items × base + 8 checkpoints):** every checkpoint is
   IDENTICAL to base — mechanical 0.786, core-prose 0.857, structured 1.0, canon 1.0 — with **zero
   critical regressions, zero severe slop, zero token-cap, zero reasoning-trace leakage**.
2. **Focused-revision audit (the primary target, supplementary 3-fix probe):** base unchanged-return
   rate **0.667 (2/3)**; **every checkpoint identical at 0.667** — no checkpoint reduces the failure,
   none applies all three authorized fixes, the protected line is preserved everywhere (1.0).
3. **Blind base-vs-`lora_step-18` prose review** (two independent, perfectly-calibrated blind LM
   reviewers; human review waived this round → **model-review-only, NOT human-confirmed**):
   base prose **3.455**, LoRA prose **3.455** — **prose_gain 0.0**, voice_gain −0.045, instruction
   drop 0.0, **zero new fatal**. The frozen effect floor (prose gain ≥0.25, voice ≥0.25) is **not
   cleared**.

## Why `revise_Dataset_A3` (not the other branches)

The conservative pilot is **non-destructive** (zero regressions, zero degeneration, protected text
intact) but **neutral** (below the effect floor on every axis, and untouched on the primary target).
At 42 training records / LR 1e-5 / ~1 epoch this is the expected feasibility signal: **the pipeline
and recipe are safe; the dataset is simply too small and thin to move the targeted behaviour.** The
lever to pull is the **dataset**, so:

- **`retain_Qwen_base`** — rejected: framing the neutral result as "base is better, stop" ignores
  that a clear, addressable data defect (scale/density) explains it.
- **`revise_LoRA_recipe`** — rejected: there is no early-improves/later-declines pattern; the curve
  is flat and clean, so exposure/optimization is not the culprit.
- **`run_one_bounded_confirmation`** — rejected: nothing is narrowly ambiguous; three measurements
  agree on a flat neutral.
- **`stop_Qwen_tuning_direction`** — rejected: failures are NOT broad degradation; the model is
  simply unchanged. A 42-record pilot cannot support "the model resists specialization."
- **`select_LoRA_checkpoint`** — rejected: zero blind prose gain, far below the frozen floor.

## Next step (revise Dataset A.3)

Scale + curate Dataset A.3 toward the 300–500 production target with: higher **focused-revision
density** (especially multi-constraint three-fix items with protected text — the measured gap),
**teacher diversification**, contrastive bad→good pairs, and **Gate-3 human review** — then retrain
under the same frozen recipe. This is a dataset revision, not a new sweep or a base change.

## QAT gate

Denied. `qat_gate`: foundation_confirmed=true, but **lora_checkpoint_selected=false** and
**blind_advancement_floor_passed=false** → `qat_authorized: false`, `qat_started: false`. No QAT
spec is created.

## Unresolved risks

- The base's multi-constraint focused-revision weakness (unchanged-return 0.667) remains **unfixed**
  and is now a confirmed, quantified training target for the scaled dataset.
- The blind confirmation is **model-review-only** (Gary/human review waived this round); a scaled
  retrain that DOES show a gain must pass a human-inclusive blind review before selection.
