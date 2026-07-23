# Phase 0 — Experiment Contract Freeze (Dispatch 30A)

**Status: FROZEN.** No training, no generation, no dataset construction in Phase 0. `master`
untouched. This report records the frozen decisions the rest of the pilot references.

## What is frozen

| Item | Value / pointer |
|---|---|
| Model revision | `Qwen/Qwen3-8B` @ `b968826d…` (thinking disabled) — [`freeze/model-revision.json`](../freeze/model-revision.json) |
| Serializer | production scene-packet serializer `scene-packet.schema.json@1`, system prompt `lw-scene-executor-v1` — [`freeze/serializer-version.json`](../freeze/serializer-version.json) |
| Training arms | A frozen base · B atomic (1–2 constraints) · C compositional (5–8) · D compositional+replay |
| Training recipe | conservative LineWright LoRA: rank16/α16, dropout 0.05, LR 1e-5 cosine, wd 0, grad-clip 1.0, bf16, seq 2048, ~1 epoch, seed 20260723; ≥3 checkpoints (33/66/final) |
| Source roles | Gary AoS/Norse manuscripts = only SFT gold; 11 professional files = instrumentation only |
| Record cap | ≤ 2 records per source scene (1 atomic + 1 compositional) |
| Primary metric | original-world **joint success** (all hard constraints pass AND quality ∈ {3,4}) |
| Co-primary | constraint-level pass rate (by type), packet-clustered intervals |
| Analysis plan | McNemar paired, discordant counts, CIs — [`freeze/analysis-plan.yaml`](../freeze/analysis-plan.yaml) |
| Verifier plan | required deliverable; frozen at Phase 3 after fixture validation — [`freeze/verifier-version.json`](../freeze/verifier-version.json) |
| Headroom gate | base original-world joint success must land in **[0.25, 0.65]** before training |
| Deferred | DPO/ORPO/KTO/RLHF, QAT, learned critic, training on professional books, author-imitation profiles, thousands of records, production replacement |

Full contract: [`freeze/experiment-contract.yaml`](../freeze/experiment-contract.yaml).

## Single-variable causal test (the point of the pilot)

Arm B vs Arm C hold everything equal — same task (packet→full scene), same Gary gold targets, matched
source-scene distribution, matched approximate output tokens, matched model/optimizer — and differ
**only** in explicit constraint density (1–2 vs 5–8). Target-token exposure is the exposure match of
record, because the response prose is identical between the twins.

## Privacy & IP posture (enforced by construction)

- Manuscript text never enters git (STOP condition). Data-bearing paths are git-ignored; only design
  scaffolding + hash-only manifests are committed.
- The 11 professional files are referenced by sha256 only (see the professional-reference manifest);
  their prose/names/places/canon/scene-structure are prohibited from training data. They serve as the
  overlap-screening baseline and the professional reference bands.
- Two memorization gates are pre-registered: professional-corpus overlap and Gary-target
  memorization probes. Substantial reproduction fails the gate even if eval scores improve.

## Filename note

The dispatch lists `HP(1).txt` and `got(1).txt`; the actual local files are `HP.txt` and `got.txt`.
The manifest binds to the real files by hash and records the mapping.

## Blocked-on-Gary dependency map

| Needs Gary | Phase |
|---|---|
| AoS/Norse manuscript scenes (private) | 1 select, 2 back-translate |
| Load-bearing audit ("would I care if a generated scene violated this?") | 2 |
| Final record approval; same-world eval authoring | 2, 4 |
| Blind-review + adjudication time | 10 |

## Not blocked (can proceed next without manuscripts)

- **Phase 3** — build + validate the packet-execution verifier against a manually-labeled fixture set
  of *original* examples.
- **Phase 4 (partial)** — author the **original-world** (22–28) and **non-fantasy control** (6–10)
  eval packets (new invented worlds; no Gary canon, no professional prose). Same-world eval waits on
  Gary.
- Once those exist, **Phase 5** base headroom pre-flight (GX10 base generation + mechanical scoring +
  a blind quality pass) can run and set the training gate.

## Phase 0 deliverable checklist

- [x] Experiment root scaffolded; data-bearing paths git-ignored
- [x] Professional-reference manifest (11 files, roles, prohibited uses, sha256)
- [x] Schemas: scene-packet, training-record, verifier-result, review-result
- [x] Freeze: experiment-contract, analysis-plan, model-revision, serializer-version, verifier-version(planned)
- [x] Phase-0 freeze report (this file)
- [ ] Gary provides manuscript access + audit (Phases 1–2) — pending
