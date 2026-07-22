# Dataset A.2 — Pilot & Blind-Review Report (Dispatch 21, Phases F–H)

The corrective pilot dataset, the blind-review workflow, and the machine-checkable
advancement rule. Experimental only; **no training was run** in this dispatch.

## The pilot corpus

`datasets/dataset-a.2/pilot/` — **23 train + 10 evaluation** records, all newly authored
(not lightly-edited Dataset A copies), each passing static + content validation
(`scripts/validate_a2.py`: golds pass the gates, rejected examples fail their declared
labels, train/eval story worlds disjoint).

| task family | train | eval |
|---|---|---|
| focused_revision | 14 | 5 |
| canon_extraction | 4 | 2 |
| constraint_check | 3 | 1 |
| scene_contract | 2 | 1 |
| fiction_boundary | 0 | 1 |

Behavior coverage (train records; a record serves several behaviors), targeting the
Phase-B gaps:

| behavior | train count | Phase-B status it repairs |
|---|---|---|
| no_change_restraint | 6 | was **critical** (2) |
| exact_preservation | 6 | was **critical** (2) |
| changed_true_protocol | 3 | was **absent** (0 changed:true golds) |
| repetition_control | 5 | was **absent** (0) |
| schema_adherence | 18 | was moderate/critical |
| voice_preservation | 5 | adequate → maintained |
| hard_constraint_fidelity | 3 | was thin |
| canon_fidelity | 4 | was thin |
| scope_control | 10 | — |

Every record carries `preferred_response` + explicit `rejected_responses`. The rejected
examples deliberately demonstrate the failure modes Dataset A never taught: a bare-prose
no-change (wrapper missing), a wrapped-but-edited no-change (exact-preservation failure),
degenerate loops (repeated n-grams), alternate JSON keys (`speaker`/`claim`), an
over-included constraint set, an unchanged source echo (omitted change), and — as
reviewer-assisted labels the machine cannot decide — an invalid refusal.

## Clean split

The pilot split passes the Phase-D grouping check: no `group_key`, `source_family`,
`story_world`, or source opening is shared across train and evaluation. Train and
evaluation use **disjoint story worlds** (train: lighthouse-keeper, desert-well, …;
evaluation: observatory, estuary-ferry, greenhouse, …). `manifest.json` records the group
keys per split and SHA-256 digests for reproducibility.

## Blind-review workflow

`training/reviewer-packets/dataset-a.2-pilot/` holds one identity-free packet per
evaluation record (`linewright/evaluation/reviewer_packet.py`):

- candidates are labeled **Candidate A/B/…** in a deterministic, content-derived order —
  the order cannot leak identity and is reproducible without an RNG;
- the packet body never contains base/LoRA/QAT, checkpoint step, loss, gate scores, or
  model identity (`anonymization_ok` confirmed **zero leaks** across all 10 packets);
- gold and mechanical gate results live only in `keys.json`, consulted **after** a reviewer
  locks their preference;
- three reviewers (Aedan, Claude, ChatGPT) score 1–5 on nine dimensions, choose an overall
  preference, and flag fatal flaws, **independently, before discussion**.

(Dispatch 21 has no checkpoints, so the packets use the pilot's own authored responses as
stand-in candidates to exercise the workflow end-to-end.)

## Advancement — machine-checkable, not averaged

`linewright/evaluation/advancement.py::check_advancement` returns `advance` only when:
mechanical gates pass; schema / no-change / memorization / material regressions are all 0;
all three reviewers prefer the candidate over base; and there are zero fatal reviewer flags.
A single fatal flag blocks advancement even if the other two approve; genuine disagreement
sets `needs_investigation` rather than being averaged into a pass. Lower loss, a higher
parse rate, winning a majority of a few records, and one impressive sample are **not**
accepted as advancement reasons.

## What this does and does not establish

It establishes a *system*: a failure-driven pilot, gates that catch the real failure modes,
a clean split, blinded review, and a hard advancement rule. It establishes **nothing** about
model quality — no model was trained. Quality evidence awaits a future run that trains on an
expanded, gate-passing dataset (Phases I–J) and survives blind review.
