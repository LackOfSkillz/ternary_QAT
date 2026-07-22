# LineWright Model Capability, Reliability, and Tuning Diagnostic Battery — Architecture (v1)

**Status: `architecture_only` (Dispatch 22).** This document defines the permanent
evaluation instrument LineWright runs after every meaningful model-tuning experiment. It
is the authoritative specification; the machine-readable form is
[`benchmarks/manifests/diagnostic-battery-architecture-v1.yaml`](../../benchmarks/manifests/diagnostic-battery-architecture-v1.yaml).

Short names: **LineWright Diagnostic Battery**, **LWDB**. It is a **diagnostic
instrument, not a ranking test** — never "model test", "quality test", "eval prompts", or
"head-to-head".

This dispatch creates **no** benchmark prompts, model outputs, thresholds, comparisons,
training, or dataset changes. It defines the system later dispatches implement and
calibrate.

---

## 1. Purpose

The battery must answer, after any tuning experiment:

1. Is the base model capable enough for LineWright?
2. Did tuning improve the model?
3. Did tuning introduce regressions?
4. Which capabilities improved or degraded?
5. Which is the likely bottleneck — dataset coverage, dataset balance, training duration,
   learning rate, training method, quantization, context compilation, decoding, or
   base-model capacity?
6. What should change before the next run?
7. How confident should we be in each diagnosis?

It builds on the Dispatch-21 hardened evaluation components
([`linewright/evaluation/`](../../linewright/evaluation/)) — the nine mechanical gates,
blind reviewer packets, and machine-checkable advancement rules — rather than recreating
or bypassing them. The Dispatch-20/21 finding stands: a parse-only evaluator marked
catastrophic repetition as valid; the battery never regresses to that.

## 2. Non-goals

The battery does **not**: rank models with a single number; certify quality from training
loss or parse rate; let a strong subjective score cancel a mechanical fatal flaw; invent
capability thresholds; or treat a benchmark item that influenced a change as independent
evidence for that change. Dispatch 22 additionally does not create prompts, run models,
set thresholds, expand Dataset A.2, or train.

## 3. Fast battery

Runs after meaningful checkpoints to catch catastrophic regressions, locate early
overfitting, decide whether a candidate deserves the full battery, and compare the
25/50/75/100% checkpoint curve. **Provisional size ~24–30 items** (a size, not a
threshold), composed across scene drafting, focused revision, restraint/no-change,
canon/constraint, structured protocol, bare↔compiled pairs, multi-turn, refusal boundary,
and grader-calibration items. Counts overlap because paired items cover several modules.

## 4. Full battery

Runs for major dataset-version decisions, base-model selection, quantization changes,
release candidates, final certification, and diagnosis of ambiguous fast-battery results.
**Provisional size ~60–80 items.** Adds long-form scenes, more voices/genres, longer and
adversarial context, short↔long generation pairs, deeper multi-turn chains, negative-space
damage tests, harder refusal-boundary cases, reserve items, and additional calibration
controls.

**Fast and full share one architecture** — the same schemas, capability taxonomy, scoring
model, confidence model, provenance rules, and diagnosis engine. They differ only in
depth, sample size, difficulty, and cost. There are never two incompatible evaluation
systems.

## 5. Instrument calibration (Layer 1 — the battery validates itself)

The instrument is not trusted until it proves it can recognize obvious success and obvious
failure.

- **Grader-calibration items** are seeded, hidden, into reviewer packets: a mechanically
  perfect output; schema-invalid output; canon-violating output; a severe repetition loop;
  a polished but out-of-scope rewrite; a correct no-change response; an incorrect no-change
  response; attractive prose that violates a hard constraint; an ordinary dark-fiction
  request that should not be refused; and a harmful real-world instruction disguised as
  fiction that should not be answered directly.
- **Mechanical reproducibility**: every deterministic gate produces identical
  booleans, failure labels, evidence values, and defined ordering on repeated runs of the
  same input. A differing replay is an instrument failure.
- **Reviewer reliability**: reviewers are classified `calibrated`,
  `conditionally_usable`, or `unreliable_for_run` from their calibration-item performance.
  The **mechanism** is defined now; the numeric cutoffs are set in Dispatch 23 against real
  calibration data.

If the instrument fails to validate, findings are quarantined and the run's overall verdict
must be `insufficient_evidence`.

## 6. Capability modules (Layer 2)

Nine permanent modules (details in the manifest and each item's `module`):

- **A — Long-form scene drafting**: coherence, prose, voice, pacing, dialogue,
  characterization, emotional progression, setting, required beats, canon fidelity,
  knowledge boundaries, forbidden outcomes, degeneration over length.
- **B — Focused revision**: targeted improvement, scope control, voice/protected-text
  preservation, authorized vs unauthorized change, minimal intervention, collateral damage.
- **C — Restraint & no-change judgment**: recognizing already-good prose, false-premise
  edits, deliberate fragments/repetition/ambiguity, canon-conflicting or out-of-scope edit
  requests, exact preservation, correct changed/unchanged protocol.
- **D — Canon, continuity & constraint reasoning**: fact extraction, belief vs fact,
  unreliable narration, conflicting claims, chronology/geography/inventory/injuries,
  character knowledge, presence, relationships, magic/technology limits, minimal causal
  constraint sets, applying canon during generation.
- **E — Structured output & protocol compliance**: exact JSON/YAML schema, required/
  forbidden keys, nested item shapes, wrong types, no trailing prose, missing-data
  behavior, no-change/revision wrappers, scene contract, constraint verdict, canon
  extraction.
- **F — Context & robustness**: bare prompt, compact/full/noisy packets, conflicting or
  incomplete source, impossible constraints, misleading premise, long context, instruction
  hierarchy, critical-information placement.
- **G — Multi-turn authoring**: revision-of-revision, restoring an earlier line, changing
  only the latest element, canon/voice across turns, avoiding cumulative collateral damage,
  correcting a previous bad revision, obeying updated direction.
- **H — Refusal & fiction-boundary calibration**: tests both over-refusal and unsafe
  under-refusal — ordinary dark fiction, villain dialogue, crime/battlefield fiction,
  emotionally abusive characters, fictional threats, harmful real-world guidance, harm
  disguised as fiction, ambiguous boundary cases.
- **I — Stability & degeneration**: repeated sentences/n-grams/beats/openings, lexical
  collapse, runaway continuation, output-to-source ratio, token-cap and structure
  truncation, long-output drift, premature stopping. Partly standalone, partly embedded
  across every module.

Each module may weight the reviewer dimensions differently; there is no universal score
that hides a module-specific failure.

## 7. Controlled pairs (Layer 3)

Controlled pairs are the **primary diagnostic structure**. Each pair changes one meaningful
variable and holds the rest invariant. **No causal diagnosis is emitted without a
controlled comparison supporting it.** Mandatory family types: voice (terse↔lyrical),
surface (bare↔compiled), length (short↔long), canon (extract↔apply), restraint
(needs-change↔already-correct), context (clean↔noisy), turn (single↔multi), constraint
(low↔high load), and a difficulty family (easy/moderate/hard/adversarial). Every item
carries `pair_id`, `family_id`, `controlled_variable`, `invariant_features`,
`expected_diagnostic_if_split`, and `paired_item_ids`; standalone items are permitted only
when pairing adds no diagnostic value (e.g. rare calibration or refusal cases) and must
justify it.

## 8. Prompt surfaces

Prompt surface is a controlled variable: `bare`, `compact_packet`, `full_compiled_packet`,
`noisy_compiled_packet`. The engine reasons over matched surfaces:

- bare passes, compiled fails → likely context-compiler / salience / length / attention;
- bare fails, compiled passes → the compiler provides useful scaffolding;
- both fail → likely base capability / training / task understanding;
- both pass → model and compiler both appear functional.

**No context-compiler diagnosis may be emitted without a matched surface comparison.**

## 9. Mechanical evaluation

Deterministic gates from Dispatch 21, one result per output
(`mechanical-result-schema`): `format_valid`, `schema_valid`, `protocol_valid`,
`constraint_valid`, `source_fidelity`, `no_change_valid`, `repetition_valid`,
`memorization_valid`, `completion_valid`, and `negative_space_valid`. Dimensions stay
**separate**; a null gate is not-applicable/reviewer-assisted, never a silent pass.
Negative-space measurements (unauthorized-change ratio, protected-span/fact changes, new
proper nouns, unrelated rewrites, paragraph reordering, collateral-damage flag) detect what
the model silently broke; the mechanical diff and reviewer judgement stay separate.

## 10. Reviewer evaluation

Blind absolute scoring first, on twelve dimensions (`reviewer-score-schema`):
instruction compliance, scope control, canon fidelity, constraint fidelity, voice
preservation, scene coherence, characterization, dialogue, pacing, emotional progression,
prose quality, usefulness to author. Reviewers never see model identity, checkpoint,
method, loss, base-vs-tuned, or prior scores (blind packets from
`linewright/evaluation/reviewer_packet.py`). Close or important cases may then receive blind
**pairwise** comparison, which never replaces absolute scoring. **A strong subjective score
never cancels a mechanical fatal flaw.**

## 11. Confidence model (Layer 5)

Every finding (`diagnostic-finding-schema`) carries capability, comparison, direction,
effect size, sample size, evidence type, reviewer agreement, mechanical support,
confidence, likely causes, competing explanations, and recommended next test/change.
Evidence types: `mechanical`, `matched_pair_mechanical`, `reviewer_consensus`,
`matched_pair_consensus`, `reviewer_split`, `single_reviewer`,
`mixed_mechanical_and_reviewer`. Confidence tiers: `high`, `moderate`, `low`,
`inconclusive`. Illustrative anchors — *high*: schema accuracy collapsed, no-change exact
preservation failed, severe repetition rose materially, bare passes while its compiled twin
repeatedly fails; *moderate*: all calibrated reviewers prefer tuned scenes, repeated
advantage across controlled pairs; *low*: "feels slightly flatter", one genre better in two
examples, reviewers disagree; *inconclusive*: effect below the (future) floor, sample too
small, calibration failed, or mechanical and reviewer evidence conflict. The engine may — and
must be able to — emit **insufficient evidence**.

## 12. Benchmark lifecycle (Layer 6)

Directories: `development/`, `active-core/`, `rotating/`, `reserve/`, `calibration/`,
`burned/`, plus `manifests/` and `schemas/`. Item states:
`development → candidate → active → used_for_measurement → used_for_diagnosis → burned →
retired`. Every item carries provenance and append-only usage history
(`benchmark-provenance-schema`). Active-core items rotate; reserve items are hidden during
routine dataset development.

## 13. Burned-item policy

1. Benchmark items are excluded from training **by construction** (`benchmark_only: true`).
2. Any item that **directly informs** a dataset or training change becomes **burned**.
3. Burned items may remain regression checks.
4. Burned items are **not** independent evidence of improvement for the change they inspired.
5. Reserve items are not visible during routine dataset development.
6. Provenance/usage history is append-only — never rewritten to hide a burn.

## 14. Reference-model calibration (capability floors are empirical)

No percentage thresholds are invented in this dispatch. Future floors are calibrated
against a lineup: the untouched target base, the current tuned checkpoints, a stronger
known-good reference model, and optionally a weaker reference. The **method** is defined
now; the numeric values remain unset until calibration data exists (Dispatch 23+). The
strong reference calibrates task difficulty and score range — it is **not** automatically
the deployment target, and its win does not by itself advance a candidate.

## 15. Checkpoint-curve testing

Where checkpoints exist, evaluate 25/50/75/100% (fractions, never a fixed step count) and
report the earliest meaningful improvement, the peak checkpoint, the onset of regression,
capability-specific peaks, and whether long-form prose and protocol compliance peak at
different times.

## 16. Diagnosis engine contract

Data flow: **benchmark item** (+ locked behavior contract) → **generation manifest** (model
roles, decoding) → **anonymous output records** → in parallel **mechanical results**
(Dispatch-21 gates) and **blind reviewer scores** (+ reviewer calibration) → **diagnostic
findings** → **battery run summary**. Interfaces: mechanical gates consume
`(output, output_contract, expectations)` and return the ten-dimension result; reviewer
packets consume anonymous outputs and return blind scores; the diagnosis engine consumes
findings-with-evidence and emits confidence-tagged diagnoses plus recommended actions,
choosing `likely_causes` only from the bottleneck cause space and only naming a causal cause
when a controlled comparison supports it. If `instrument_valid` is false the run's `overall`
is `insufficient_evidence`. Package responsibilities: `linewright/evaluation/` owns the
mechanical gates, reviewer packets, advancement, and (future) diagnosis engine;
`benchmarks/` owns items, schemas, manifests, and lifecycle state.

## 17. Roadmap

| dispatch | title | status |
|---|---|---|
| 22 | architecture & specification | **current** |
| 23 | instrument calibration & grader validation | planned |
| 24 | fast battery construction & first execution | planned |
| 25 | fast battery validation & diagnostic engine | planned |
| 26 | full battery construction | planned |
| 27 | full battery baseline & certification | planned |

## 18. Implementation status

Implemented in Dispatch 22: the architecture, twelve schemas, the machine-readable
manifest, the `benchmarks/` directory skeleton, documentation, and validation tests.
**Not** implemented (by design): benchmark prompts, grader-calibration outputs, model
generation/scoring, empirical thresholds, model comparisons, dataset expansion, training,
checkpoint selection.

## 19. Future dispatch boundaries

Dispatch 22 may implement only architecture, schemas, manifests, documentation, validation
tests, the directory skeleton, and interfaces/contracts. It must not implement benchmark
prompts, grader-calibration outputs, model generation or scoring, empirical thresholds,
model comparisons, dataset expansion, training, or checkpoint selection. The next dispatch
begins only when the architecture is stable enough that calibration items can be built
without inventing new concepts during implementation.

### Architecture questions intentionally deferred to Dispatch 23

- Numeric reviewer-calibration cutoffs mapping performance → `calibrated` /
  `conditionally_usable` / `unreliable_for_run`.
- Numeric capability floors and minimum effect sizes per capability (from the calibration
  lineup).
- The concrete negative-space diff algorithm and its `allowed_diff_budget` defaults.
- Rotation cadence for `active-core` and the reserve-exposure policy specifics.
- The exact strong/weak reference models for the calibration lineup.
- Aggregation rules turning per-reviewer scores + mechanical results into a single finding
  (without averaging away a fatal flaw).
