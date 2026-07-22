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

## Slop reports (Module J, Dispatch 23)

Slop = undesirable writing behaviours (repetition, semantic redundancy, stock-phrase
concentration, voice flattening, generic endings, corpus sameness). Read a **slop report**
([`lwdb-slop-report-v1.md`](../training/docs/lwdb-slop-report-v1.md)) as **four separate
evidence families** — deterministic, semantic, lexical/style, reviewer — each with evidence
spans and its own confidence. There is **no single opaque score**. All numeric thresholds
are unvalidated until calibration; the only escalation used now reuses the justified
Dispatch-21 repetition gate.

**False-positive risks the detector is built to avoid**: deliberate rhetorical repetition,
motif recurrence with progression, concise low-diversity prose, lyrical/unusual syntax,
character-specific diction, intentional fragmentation, a genre-appropriate stock phrase used
once. The slop calibration set proves these known-good cases are not flagged.

**Reference profiles** are not universally interchangeable: a lyrical passage is not judged
against a terse-noir rhythm profile. **Corpus-level** sameness (repeated openings, template
reuse, voice convergence) is measured per-run and compared across model roles only after
blind per-output scoring is locked.

## Execution-mode neutrality & pause/resume (Dispatch 23)

Parallel and sequential runs are semantically equivalent: same frozen plan, same normalized
results, only scheduling differs. Runs are durable (SQLite ledger) and survive graceful or
immediate pause, controller restart, network changes, and worker loss — resuming without
rerunning completed jobs. See
[`lwdb-execution-and-resume-v1.md`](../training/docs/lwdb-execution-and-resume-v1.md).
Mid-generation recovery is item-level, not token-level.

## Fast battery v1 & first execution (Dispatch 24)

The first **fast battery** (`benchmarks/active-core/fast-v1/`) is 20 items across modules A–J
with 7 controlled pairs (surface/restraint/canon/voice/length/constraint/turn), a locked
behavior contract + provenance per item, and a frozen hashed manifest. The run pipeline
(`linewright/evaluation/battery/`) freezes a generation plan, routes jobs by role (base vs
candidate) across two GX10s, scores each output with the mechanical gates + Module-J slop,
and builds **blind reviewer packets**: absolute scoring first, each output a standalone
identity-free unit with the 4 grader-calibration items seeded in indistinguishably, then
pairwise base-vs-candidate with content-shuffled candidate labels. Reviewer fatal flaws and
positive slop findings must cite exact spans — never "feels AI". Interpreting a **preliminary**
first run: report completion, instrument validity, mechanical failures, and preliminary slop
patterns — but declare no winner, no capability floor, no release readiness (those await
Dispatch 25). See the first-run report at `benchmarks/runs/lwdb-fast-v1-20260722/`.

## Relationship to Dispatch 21

The battery **builds on** the Dispatch-21 components, it does not recreate them: the nine
mechanical gates ([`linewright/evaluation/gates.py`](../linewright/evaluation/gates.py)),
blind reviewer packets, and machine-checkable advancement/readiness rules. The battery adds
the capability taxonomy, controlled pairs, prompt-surface control, confidence-aware
diagnosis, the benchmark lifecycle, and the reference-model calibration method.
