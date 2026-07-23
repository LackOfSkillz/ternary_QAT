# Fantasy Compositional SFT Pilot (Dispatch 30A)

> **⛔ SUPERSEDED (2026-07-23) by Dispatch 30A-R1** (`experiments/professional-fantasy-packet-sft-r1/`).
> This pilot is retained for provenance only. Its reusable infrastructure (verifier v1, schemas,
> calibration) was migrated to R1 unchanged. Do not resume work here.

> **⏸ PAUSED (2026-07-23) — source-role change.** The eleven professional files will now supply
> selected scene-sized **gold targets** (not instrumentation only). A replacement dispatch will
> redesign the data plan. Do not select scenes, back-translate packets, freeze a corpus, build
> atomic/compositional pairing, split train/eval, or run any LoRA. Completed scaffolding, schemas,
> scripts, verifier, and calibration are preserved and remain valid. The `source_roles` section of
> `freeze/experiment-contract.yaml` is **superseded**. See
> [`reports/PAUSE-30A-source-role-change.md`](reports/PAUSE-30A-source-role-change.md).

The first controlled fantasy-fiction LoRA experiment for LineWright. It tests one causal question:

> Does compositional packet-to-scene SFT improve useful fantasy prose on **entirely new worlds**
> more than an atomic packet-to-scene control — without reducing prose quality or memorizing the
> manuscript targets?

The tested variable is **constraint density** (Arm B: 1–2 load-bearing constraints vs Arm C: 5–8),
not task type. Both arms perform the same task: `scene packet → full prose scene`, against the same
Gary-authored gold scenes.

## Source roles (do not conflate)

- **Gary's AoS/Norse manuscripts** — the *only* authorized SFT gold targets. Each gold scene
  predates its back-translated packet and is never teacher-rewritten. Manuscript text is **private**
  and never enters git.
- **The 11 professional reference files** (`training text/`, git-ignored) — instrumentation and
  calibration only: professional prose bands, anti-slop null distribution, detector calibration,
  overlap screening, blind-review professional controls. **Never** SFT targets; their prose, names,
  places, canon, and scene structures never enter training data. See
  [`manifests/professional-reference-files.json`](manifests/professional-reference-files.json).

## What is committed vs. private

Committed (design/provenance, no prose): `schemas/`, `freeze/`, `configs/`, `scripts/`, `reports/`,
and the professional-reference manifest (hashes only). Git-ignored (private/data-bearing):
`datasets/`, `outputs/`, `checkpoints/`, `reviews/`, and any manifest that embeds manuscript or
same-world content (`manuscript-source-scenes.jsonl`, `atomic-records.jsonl`,
`compositional-records.jsonl`, `replay-records.jsonl`, `eval-same-world.jsonl`).

## Phases

0 freeze contract (**done**) → 1 select manuscript scenes → 2 back-translate + Gary's load-bearing
audit → 3 build + validate verifier → 4 build frozen eval sets (original-world / same-world /
non-fantasy) → 5 base headroom pre-flight (the gate into training: base joint-success 25–65%) →
6 freeze datasets + exposure matching → 7 train Arms B/C/D (33/66/final checkpoints) → 8 generate all
eval outputs → 9 mechanical + semantic verification → 10 targeted blind review → 11 analyze + report.

No training begins until the eval sets are frozen and base headroom clears the gate.

## Blocked on Gary (human-in-the-loop)

Phases 1–2 (manuscript scene selection + load-bearing audit), same-world eval authoring, and the
Phase 10 blind-review/adjudication time all require Gary's private manuscripts and his review. Those
cannot proceed from the repository alone. Phases 3 and 4 (verifier + original-world/non-fantasy eval
packets) are **not** blocked and can proceed next.
