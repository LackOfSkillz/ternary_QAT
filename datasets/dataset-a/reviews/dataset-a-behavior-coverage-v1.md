# Dataset A — Behavior Coverage Matrix (Dispatch 21, Phase B)

What the current 35-record Dataset A actually *teaches*, measured per behavior rather
than by record totals. Machine-generated from the frozen corpus; data in
[dataset-a-behavior-coverage-v1.json](dataset-a-behavior-coverage-v1.json).

> A behavior is never marked adequate on the strength of one record. "adequate-for-pilot"
> means only that it is not a blocking gap for a *pilot*, not that it is production-ready.

## Coverage by behavior

| behavior | train | eval | negative/rejected | uniq families | status |
|---|---|---|---|---|---|
| no_change_restraint | 1 | 1 | — | 2 | **critical** |
| exact_preservation | 1 | 1 | — | 2 | **critical** |
| schema_adherence_json | 12 | 4 | 2 | — | moderate |
| schema_adherence_yaml | 2 | 1 | — | 3 | **critical** |
| hard_constraint_fidelity | 4 | 1 | — | 5 | thin |
| canon_fidelity_hearsay | 4 | 1 | 0 | 5 | thin |
| voice_preserving_revision | 19 | 1 | many | — | adequate-for-pilot |
| scene_boundary_classification | 1 | 1 | — | 2 | **critical** |
| scope_restraint | 19 | 1 | many | — | adequate-for-pilot |
| **repetition_control** | 0 | 0 | 0 | 0 | **absent** |
| **memorization_resistance** | 0 | 0 | 0 | 0 | **absent** |

(Counts are behavior-predicate matches over the compiled splits; a record can serve
several behaviors. Full per-behavior detail and recommended A.2 targets in the JSON.)

## Required questions (answered)

| question | answer |
|---|---|
| Records that explicitly teach exact no-change preservation | **2** |
| `changed: true` structured golds (the other half of the protocol) | **0** |
| Rejected examples demonstrating schema drift | 2 |
| Records preserving an unusual author voice (styled revisions) | 20 |
| Records with attractive-but-canon-invalid prose (rejected canon) | **0** |
| Records distinguishing belief / opinion / intent / objective fact | 5 (canon only) |
| Train/eval records sharing a story world or source family | **0** (see Phase D) |
| Duplicated or near-duplicate golds | 0 |
| Records teaching the model to stop after a narrow edit | 20 |
| Evaluation records independently testing each important behavior | 7 total — **1 per behavior** |

## The three structural gaps

1. **The no-change protocol is a stub.** Two records teach `changed:false`; **zero** teach
   `changed:true`. The model has no basis to decide *when* to emit the wrapper, which is
   exactly the Phase-A `dsa-revision-002` failure. Both halves must be taught, with
   exact-preservation enforced.

2. **Two behaviors are entirely absent.** Nothing teaches **repetition/degeneration
   avoidance** or **memorization resistance** — because the Opus teacher never produces
   those failures, so no rejected example demonstrates them. These are precisely the
   modes the 20-step checkpoints collapsed into. A.2 must add *synthetic rejected*
   examples that show a degenerate/looping response being corrected.

3. **The held-out set tests each behavior with a single record.** Seven eval records
   across ~9 behaviors means most behaviors are decided by one example — statistically
   meaningless. A.2's held-out set must test each important behavior with several
   independent records.

## Thin structured families

`canon_extraction` (5), `constraint_check` (5), and `scene_contract` (3) are each thin,
and their evaluation is a single record apiece. Combined with the Phase-A schema-drift
and causal-set-over-inclusion findings, these need both more positives and explicit
*rejected* examples (alternate-key JSON, over-included constraint sets, YAML-plus-stray-
content) so the model learns the exact contract, not an approximation.

## Recommended pilot coverage (feeds Phase F)

The absent/critical behaviors set the pilot's minimum coverage: no-change restraint,
exact preservation, repetition control, schema adherence (json + yaml), hard-constraint
fidelity, and voice-preserving revision that *performs* the change — each carried by
multiple records and paired with at least one rejected example.
