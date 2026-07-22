# Dataset A — Split & Leakage Report (Dispatch 21, Phase D)

Leakage audit of the current 28/7 train/evaluation split and the split policy A.2 will
enforce. Machine-generated; data in
[dataset-a-split-leakage-v1.json](dataset-a-split-leakage-v1.json).

## Policy: split clusters, not records

Whole **source clusters** must move together across the split — never individual
records. A source cluster is any of: a story world, a manuscript, a chapter family, a
scene and its revisions, a document family, a shared canon packet, or a synthetic
template family. Nothing below may cross train↔evaluation:

- the same source passage, or a lightly-edited version of it;
- records derived from the same scene;
- records sharing a distinctive gold completion;
- the same document family or story world (unless an explicit experiment permits it);
- paraphrased copies or shared response templates.

Dataset A already approximates this through the schema's `(template_family,
semantic_cluster)` uniqueness constraint. A.2 formalizes it with an explicit
`split_restrictions.group_key` per record and an automated cross-split check
(Phase F applies it to the pilot).

## Current split: clean

| check | result |
|---|---|
| exact duplicate source hashes | **none** |
| `template_family` spanning train+eval | **none** |
| `semantic_cluster` (story world) spanning train+eval | **none** |
| shared gold openings (first 80 chars) | **none** |
| longest cross-split verbatim character span | **66 chars** (incidental shared phrasing) |
| longest cross-split shared token span | **7 tokens** |
| highest cross-split gold SequenceMatcher ratio | **0.549** (driven by common short fragments, not copied passages) |
| **verdict** | **clean** |

A 66-character / 7-token maximum verbatim overlap and a 0.55 ratio with no shared opening
reflect ordinary English overlap between short literary passages, not leakage. No record
in the evaluation split shares a source family, story world, source hash, or gold opening
with any training record.

## Consequence for the Dispatch-20 interpretation

Because the split is clean, the Dispatch-20 failures are **not** attributable to
train/evaluation leakage. They are explained by (a) tiny-data overfitting driving
degeneration at 20 steps and (b) the coverage gaps in Phase B — not by the model having
seen held-out material. This strengthens, rather than weakens, the Phase-A conclusion.

## What A.2 automates

1. Every record carries `split_restrictions.group_key` (story world / document family /
   template family) and `must_not_share_group_across_splits: true`.
2. A split validator refuses to assign records to different splits if they share a
   `group_key`, a `source_hash`, a gold opening, or exceed a verbatim-overlap threshold.
3. The pilot manifest records the group assignment per split so the check is reproducible
   (see Phase F `manifest.json`).
