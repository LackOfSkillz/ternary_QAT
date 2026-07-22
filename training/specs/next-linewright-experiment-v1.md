# Next LineWright Experiment — Specification (v1, Dispatch 25)

Derived from the Dispatch-25 branch decision (`test_stronger_base`). **Not started.** No
training or generation is launched by this dispatch. One controlled variable at a time.

## Primary experiment — stronger-base comparison (no training)

**Objective:** determine whether a stronger base model clears the core-prose feasibility floor
the current 4B base misses (0.286 < 0.50), before any dataset scaling.

**Hypothesis:** the core-prose weakness is a base-capacity limit, not a data or method problem;
a stronger base will pass core-prose feasibility on the same frozen battery.

**Controlled variable:** the **base model only**. Everything else is held fixed — the frozen
fast battery (`benchmarks/manifests/fast-battery-v1.yaml`), behavior contracts, prompts,
generation settings, seeds, token limits, the mechanical gates + Module-J slop, and the blind
review workflow. No LoRA/QAT, no dataset change.

```yaml
objective: stronger-base feasibility comparison on the frozen fast battery
hypothesis: core-prose weakness is base-capacity limited; a stronger base clears the floor
base_model: a stronger known-good candidate (e.g. an 8B tier, or a stronger 4B) + the current base as control
training_method: none (evaluation only)
dataset_version: unchanged (no Dataset A / A.2 modification)
frozen_benchmark: fast-battery-v1 (same items, contracts, plan semantics)
evaluation_schedule: one dual/parallel run per base, absolute blind review after mechanical scoring
research_threshold: research-continuation-v0 (locked)
starter_threshold: starter-model-acceptance-v0 (locked)
critical_regression_rule: 0 critical regressions vs the current base
controlled_variables: base_model only
training_started: false
```

**Advancement:** a stronger base is preferred only if it passes the core-prose floor AND does
not regress mechanical/slop vs the current base AND survives blind review. Ambiguity does not
count as improvement (frozen threshold).

## Secondary experiment (separately authorized) — early-stop LoRA confirmation

Only if a base is chosen, and as a SEPARATE controlled run: test the over-exposure hypothesis
from the checkpoint curve (LoRA-10 neutral, LoRA-20 collapsed) with an **early-stop** recipe.

```yaml
objective: test whether degeneration is over-exposure rather than method
training_method: LoRA (unchanged rank/alpha/dropout from the full-comparison run)
dataset_version: unchanged (audit-informed changes are a LATER, separate experiment)
dataset_target_size: unchanged for the confirmation; a balanced ~200-500 record set is a
  SEPARATE future experiment (see audit: balance by TOKENS not just examples; add changed:true
  no-change coverage; strengthen structured protocol)
epochs_or_steps: fewer steps than 20 (e.g. <=10), with checkpoint_interval small
early_stop_rule: stop before severe-slop / token-cap onset (monitored on a held-out probe)
learning_rate: unchanged (do NOT co-vary LR and steps)
checkpoint_interval: frequent (every few steps) for curve selection
frozen_benchmark: fast-battery-v1
critical_regression_rule: 0 critical regressions vs base
controlled_variables: training_steps only
training_started: false
```

## Dataset scale (recommendation, not authorization)

If — after a stronger base clears feasibility — a scaled dataset is authorized, the audit
suggests **~200–500 carefully balanced records**, balanced by **token mass** (not just example
count), with added `changed:true` no-change coverage and strengthened structured-protocol
coverage. This is a **recommendation** contingent on task coverage, token balance, observed
(zero) template concentration, and human-review capacity — not a commitment, and not this
dispatch's work.

## Explicitly avoided

No simultaneous uncontrolled changes: the primary experiment changes only the base; the
secondary changes only the step count. Dataset, LR, rank, alpha, dropout, method, and decoding
are not co-varied. LoRA-20 is not continued. No broad hyperparameter sweep.
