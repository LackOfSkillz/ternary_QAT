# Dispatch 25 — Branch Decision (v1)

A threshold-bound decision from the completed Dispatch-24 live run, the existing-checkpoint
curve, the dataset audit, and the packet profile. **Provisional, evidence-grounded,
reversible.** The thresholds were authored and **frozen/committed before this analysis**
(lock `benchmarks/thresholds/threshold-lock-v0.json`, verified valid); they were NOT tuned to
produce this branch, and — per the honesty note in the threshold file — they are post-hoc with
respect to Dispatch 24 and prospective for this decision and future runs.

## Decision

```yaml
branch: test_stronger_base
threshold_result: fail            # base fails the research-continuation feasibility floors
base_feasible: false
```

## Evidence applied to the frozen threshold

| base feasibility floor | threshold | observed (Dispatch-24 base) | pass |
|---|---|---|---|
| total mechanical pass rate | ≥ 0.40 | 0.45 | ✓ |
| **core prose pass rate** | **≥ 0.50** | **0.286** | **✗** |
| modules with ≥1 usable result | ≥ 7 | 7 | ✓ |
| severe slop rate | ≤ 0.25 | 0.05 | ✓ |
| runaway token-cap rate | ≤ 0.25 | 0.15 | ✓ |
| bare-prompt success | ≥ 0.40 | 0.421 | ✓ |
| realistic-packet success | ≥ 0.35 | 1.0 (compact packet, n=1) | ✓ |

The single failing floor is **core prose** (scene + focused-revision, mechanical): the
untouched base passes only 2 of 7 core-prose items mechanically (completion / scope / source
fidelity). Per the frozen branch rule, *"base FAILS feasibility on core prose → a data problem
cannot fix a base-capacity problem → test a stronger base."*

Corroborating evidence (does not change the branch):

- **Checkpoint curve (9-item subset):** mechanical pass base 5 / LoRA-10 5 / LoRA-20 2; severe
  slop 0 / 0 / 6; token-cap 2 / 2 / 6. **No checkpoint improves over base; LoRA-10 is neutral;
  LoRA-20 collapses (degeneration onset at step-20); the curve is monotone-worsening.** So
  there is no better earlier checkpoint to select, and continuing this training regime is
  contraindicated.
- **Comparison:** candidate improves on 1 item, causes **5 critical regressions** (base-clean →
  candidate-severe).
- **Dataset audit:** token mass ≠ example balance (canon dominates tokens with 5 examples); the
  no-change protocol is half-taught (2 `changed:false`, 0 `changed:true`) — a real gap, but a
  base too weak on core prose is addressed first.

## Rejected branches

- **continue_scaled_dataset** — rejected: 0 capabilities improve over base and the checkpoint
  curve is monotone-worsening; scaling data cannot be justified.
- **checkpoint_selection_only** — rejected: LoRA-10 is *neutral* (matches base, does not
  improve); there is no better earlier checkpoint to keep.
- **revise_training_objective** — not selected: the recipe is indeed part of the problem (the
  audit + curve suggest over-exposure and token imbalance), but the base fails the core-prose
  floor, and a training-recipe fix cannot repair a base-capacity shortfall. Held as a secondary
  action *after* a stronger base is in hand.
- **pause_current_direction** — rejected: the base is feasible on most floors (not merely
  marginal); the direction is not dead, the base is under-powered.

## Ambiguous-middle rule

Applied as written: ambiguity is **not** counted as improvement. Here the result is a clear
*fail* (a floor is missed), not the ambiguous middle, so the conservative confirmation clause
is not invoked — but the decision remains provisional and reversible.

## Honest limitations

- **Core prose is measured mechanically** (completion / scope / repetition), a coarse proxy;
  full prose quality is a **blind-reviewer** judgement that has **not** been run. The
  reviewer pass could revise the core-prose feasibility read and thus the branch.
- The compiled-packet arm is **compact/partial** (packet ratio 1.35, 6 components missing); a
  full packet-length family is required before any context-compiler diagnosis.
- Two experimental smoke checkpoints on a 20-item first battery. No winner, no capability
  floor, no ship claim.

## Next experiment

Specified (not started) in `training/specs/next-linewright-experiment-v1.md`: a **stronger-base
comparison** on the same frozen fast battery — change ONLY the base model, hold method / data /
decoding fixed — to isolate base capacity. A bounded early-stop LoRA confirmation (to test the
over-exposure hypothesis from the curve) is a secondary, separately-authorized experiment. No
training was started in this dispatch.
