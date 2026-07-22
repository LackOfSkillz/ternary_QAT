# LineWright Diagnostic Battery — evaluation guide

Evaluation-facing overview of the **LineWright Model Capability, Reliability, and Tuning
Diagnostic Battery** (LWDB). The authoritative architecture is
[`training/docs/linewright-diagnostic-battery-architecture-v1.md`](../training/docs/linewright-diagnostic-battery-architecture-v1.md);
the machine-readable form is
[`benchmarks/manifests/diagnostic-battery-architecture-v1.yaml`](../benchmarks/manifests/diagnostic-battery-architecture-v1.yaml).
**Status: `architecture_only` (Dispatch 22).**

## Capability modules

A–I: long-form scene drafting, focused revision, restraint/no-change judgment, canon &
constraint reasoning, structured output & protocol, context & robustness, multi-turn
authoring, refusal & fiction-boundary calibration, and stability & degeneration. Each
module weights the reviewer dimensions differently; there is no universal score that hides
a module-specific failure.

## Controlled-pair design

Pairs are the primary diagnostic structure — one variable changes, the rest are invariant:
voice (terse↔lyrical), surface (bare↔compiled), length, canon (extract↔apply), restraint
(needs-change↔already-correct), context (clean↔noisy), turn (single↔multi), constraint load,
and a difficulty family. **No causal diagnosis is emitted without a matched comparison.**

## Grader calibration

The instrument validates itself first (Layer 1): hidden known-good / known-broken items
seeded into reviewer packets, deterministic mechanical replay, and reviewer-reliability
classification (`calibrated` / `conditionally_usable` / `unreliable_for_run`). Numeric
cutoffs are calibrated in Dispatch 23, not invented now. If the instrument fails to
validate, findings are quarantined and the run verdict is `insufficient_evidence`.

## Confidence tiers

Findings carry `high` / `moderate` / `low` / `inconclusive`, and `insufficient evidence` is
a first-class outcome. Confidence comes from evidence type (mechanical, matched-pair,
reviewer-consensus, split, single-reviewer, mixed) and sample size — never from training
loss or parse rate.

## Bare vs compiled testing

Prompt surface is a controlled variable (`bare` / `compact_packet` / `full_compiled_packet`
/ `noisy_compiled_packet`). Matched bare↔compiled arms localize whether a failure is the
context compiler, the base model, or training — no context-compiler diagnosis without the
matched surfaces.

## Model lineup

Routine minimum: `target_base`, `previous_best`, `new_candidate`. Optional roles:
`alternate_method`, `strong_reference` (calibrates difficulty/range; not automatically the
deployment target), `weak_reference`. Model identity lives only in the role manifest and the
un-blinding key — never in a reviewer packet or anonymous output.

## Diagnosis output & advancement

Each finding names capability, direction, effect size, evidence type, confidence, likely
causes (from the fixed bottleneck cause space), competing explanations, and a recommended
next test/change. Advancement uses the Dispatch-21 rule
([`linewright/evaluation/advancement.py`](../linewright/evaluation/advancement.py)):
mechanical gates pass, zero regressions, all reviewers prefer over base, zero fatal flags —
a single fatal flag blocks advancement, and disagreement is investigated, not averaged.

## Relationship to Dispatch 21

The battery **builds on** the Dispatch-21 components, it does not recreate them: the nine
mechanical gates ([`linewright/evaluation/gates.py`](../linewright/evaluation/gates.py)),
blind reviewer packets, and machine-checkable advancement/readiness rules. The battery adds
the capability taxonomy, controlled pairs, prompt-surface control, confidence-aware
diagnosis, the benchmark lifecycle, and the reference-model calibration method.
