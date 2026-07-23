# Professional Fantasy Packet-to-Prose SFT Pilot (Dispatch 30A-R1)

A controlled LoRA pilot that tests whether packet-conditioned SFT on professionally published fantasy
scenes (as gold completions) improves Qwen3-8B's execution of **entirely original** LineWright scene
packets — without unacceptable memorization, source reconstruction, prose collapse, or loss of
generality. Supersedes Dispatch 30A in full.

## Causal test

Arm B (atomic, 1–2 load-bearing constraints) vs Arm C (compositional, 5–8) — same task
(`scene packet → full prose scene`), **same professional gold passages**, constraint density the only
variable. Arm A = frozen base; Arm D = compositional + replay (deferred if no valid replay corpus).

## Source policy (see `freeze/source-policy.yaml`)

The eleven files under `training text/` are authorized for this **private, local** experiment as
gold-target sources, reference bands, and the memorization-comparison corpus. Gold targets are the
**unchanged** professional passages. The model-visible packet carries **no** source filename, author,
title, or distinctive wording. Two packet representations (provenance vs training) plus retrieval-risk
review keep packets from becoming retrieval keys.

## Privacy / what is committed

**Committed** (design/provenance/statistics, no prose): `schemas/`, `freeze/`, `scripts/`, stats-only
`reports/`, `manifests/professional-source-files.json` (hashes + counts), and the **original** eval
sets. **Git-ignored** (private): `private-data/` (verbatim targets + normalized sources), `datasets/`,
`outputs/`, `checkpoints/`, `reviews/`, and every offset-bearing passage/record/held-out manifest.
Source prose is never reproduced in committed files or assistant output. `model_distribution` and
`adapter_publication` require separate review; `dataset_publication` and `source_text_commit` are
prohibited.

## Evaluation

Headline = **original-world** fantasy packets (30–40; new worlds/characters/magic; no source canon or
names; structural-novelty gate vs the training-packet manifest). Held-out professional (11–22) and
non-fantasy control (8–12) are reported **separately** and never as the headline. No
similarity-to-gold scoring. Memorization is a **primary** axis (lexical overlap, retrieval probes,
structural reconstruction, source attraction).

## Phases

0 migrate+freeze (**done**) → 1 normalize+fingerprint → 2 segment candidates (**human boundary
review**) → 3 select balanced set → 4 provenance packets → 5 abstract training packets + retrieval
risk → 6 matched atomic/compositional records → 7 freeze eval → 8 verifier+overlap validation →
9 base headroom → 10 freeze config+datasets → 11 train B/C(/D) → 12 eval → 13 memorization probes →
14 blind review → 15 analyze+report.

Human gates: Phase 2 (boundaries), 3 (acceptance), 7 (novelty), 9 (headroom quality), 14 (review).
