# Dataset A — Failure Inventory (Dispatch 21, Phase A)

A behavioral classification of every held-out output from the Dispatch-20 experiment —
untouched **base**, **LoRA-20**, **QAT-10** (contextual), **QAT-20** — against the
**gold** targets, on all 7 frozen evaluation records. Each output was run through the
new Phase-E mechanical validators; the per-record machine evidence is in
[dataset-a-failure-inventory-v1.json](dataset-a-failure-inventory-v1.json).

> Experimental only. Seven records prove nothing about general quality. This inventory
> classifies *failures* to drive Dataset A.2; it is not a quality ranking.

## Headline: the parse-only gate hid the real failure

The Dispatch-20 evaluator reported a single `format_valid` (does it parse / is prose
non-empty). Re-scored on nine **separate** behavioral gates, the picture inverts:

| checkpoint | old `format_valid` (of 7) | mechanical pass, all decidable gates (of 7) |
|---|---|---|
| base | 6 | **4** |
| LoRA-20 | 4 | **4** |
| QAT-10 | 6 | not computable (raw outputs not persisted) |
| QAT-20 | 3 | **0** |

The dominant failure is **degeneration / runaway repetition under 20-step overfitting**,
which the parse-only gate scored *valid*. The clearest single example: QAT-20 on
`dsa-boundary-001` emitted **"The door creaks" 45 times** (type-token ratio 0.22, a
5-gram repeated 45×) and the old gate called it `format_valid = true`.

### Correction to a Dispatch-20 claim

The Dispatch-20 report stated both 20-step runs "memorized `dsa-revision-007`
verbatim." That was an artifact of a 130-character truncation. The full outputs show the
shared opening is the **source passage being preserved** in a focused-revision task
(correct behavior), after which the outputs diverge — LoRA into an incoherent metaphor,
QAT-20 into a repetition loop. The overlap validator confirms no memorization of *other*
records' training targets. The prior "verbatim memorization" framing is withdrawn.

## Per-record findings

| record | task | base | LoRA-20 | QAT-20 | dominant issue |
|---|---|---|---|---|---|
| dsa-boundary-001 | fiction_boundary (prose) | pass | pass | **loop ×45** | QAT-20 degeneration; parse-gate blind |
| dsa-canon-003 | canon_extraction (json) | pass | degenerate | schema-drift + loop | alt keys `speaker/claim`; repeated `note` blocks |
| dsa-constraint-002 | constraint_check (json) | over-include | degenerate | over-include + loop | causal-set minimality (K1,K2,T1 vs K1) |
| dsa-revision-002 | focused_revision (no-change) | no wrapper | no wrapper | loop | **no-change protocol absent** |
| dsa-revision-007 | focused_revision (prose) | pass | pass | loop | QAT-20 degeneration |
| dsa-revision-018 | focused_revision (prose) | **echoed source** | pass | loop | base did not perform the change |
| dsa-scene-002 | scene_contract (yaml) | pass | pass | yaml+JSON dump | schema field ambiguity; QAT-20 degeneration |

Notable per-record detail:

- **dsa-revision-002 (no-change) — critical gap.** Gold is
  `{"changed": false, "reason": ..., "text": <source>}`. Base and LoRA return **bare
  prose** (wrapper missing); QAT-20 loops the source ~10×. Root cause is a dataset gap:
  across all 35 records only **two** teach the no-change wrapper and **zero** teach
  `changed: true`, so the model never learns when to emit the wrapper.
- **dsa-revision-018 — the parse-gate's other blind spot.** Base returned the source
  **unchanged, verbatim**, on a task that required transforming gaze choreography into
  motivated action. The old gate scored this `format_valid = true`; the scope validator
  flags `omitted_required_change`. A "valid" that did nothing.
- **dsa-canon-003 — schema drift.** QAT-20 emitted syntactically-JSON output with the
  **wrong keys** (`speaker`/`claim` instead of `entity`/`fact`) plus repeated `note`
  blocks. Alternate-key drift is invisible to a parse-only check.
- **dsa-constraint-002 — causal-set over-inclusion.** Even the untouched base lists
  `["K1","K2","T1"]` where gold is `["K1"]`. The task's causal-minimality discipline is
  under-taught, and eval never enforced constraint-id set equality.
- **dsa-scene-002 — a dataset defect, not only a model failure.** The instruction says
  return fields `viewpoint, location, …`; the **gold** uses `viewpoint_character` +
  `narrative_perspective`. The target contradicts its own field spec, so a model that
  emits `viewpoint:` is following the instruction more literally than the gold. QAT-20
  additionally appended a JSON dump after the YAML (stray content).

## Failure causes, separated

Per the completion criteria, causes are attributed to four categories (full lists in the
JSON `summary.failure_cause_categories`):

- **Dataset** — no-change protocol taught by only 2 records and no `changed:true` golds;
  **no rejected examples teach degeneration/repetition avoidance** (the Opus teacher
  never loops, so the failure mode is absent from the corpus); causal-set minimality
  under-taught; thin structured families (canon 5, constraint 5, scene 3).
- **Evaluator** — parse-only `format_valid` passes catastrophic repetition; no
  schema-key / alternate-key check; no exact-preservation gate; no scope / did-it-change
  check; constraint-id set equality not gated at eval time.
- **Model** — 20 steps at effective batch 8 over 28 rows (~5 epochs) drives
  degeneration; ternary-QAT collapses into loops faster than LoRA at equal steps
  (QAT-20 0/7 vs LoRA-20 4/7 mechanically).
- **Uncertainty** — prose usefulness is reviewer-assisted, not decided here; QAT-10's
  non-format dimensions are not computable because its raw outputs were not persisted.

## What this means for Dataset A.2

The corrective record types most implicated (JSON `records[].corrective_record_types`),
in priority order: **no-change restraint / exact preservation** (critical),
**repetition control**, **schema adherence** (canon/scene/constraint), **causal-set
minimality**, **voice-preserving revision that actually performs the change**, and
**scope control**. These directly seed the Phase-F pilot coverage targets.
