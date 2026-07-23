# Phase 0 — Migrate + Freeze (Dispatch 30A-R1)

**Status: FROZEN.** Phase 0 only — migration + freeze. No scene selection, segmentation, packet
back-translation, dataset construction, or training. `master` untouched. No source prose committed.

## Frozen

| Item | Value / pointer |
|---|---|
| Supersession | 30A-R1 supersedes 30A in full — [`reports/migration-report.md`](migration-report.md) |
| Source policy | 11 files as gold-target + reference + memorization corpus; privacy = private_local_research — [`freeze/source-policy.yaml`](../freeze/source-policy.yaml) |
| Source manifest | 11 files fingerprinted by sha256 + word/sentence counts (stats only) — [`manifests/professional-source-files.json`](../manifests/professional-source-files.json) |
| Model | `Qwen/Qwen3-8B` @ `b968826d…`, thinking disabled |
| Arms | A base · B atomic (1–2) · C compositional (5–8) · D compositional+replay (deferred if no valid replay) |
| Recipe | rank16/α16, LR 1e-5 cosine, bf16, seq 2048, seed 20260723, low epochs, 25–33 / 50–66 / final checkpoints |
| Primary metric | original-world joint success; co-primary constraint-level pass rate |
| Memorization | **primary** validity/safety axis (lexical + retrieval probes + structural reconstruction + source attraction) |
| Headroom gate | original-world base joint success preferred [0.20, 0.65] |
| Verifier | `v1` migrated + re-validated 14/14 (hash `11e4d9f1…`); re-confirmed against professional-passage fixtures at Phase 8 |
| Analysis | McNemar paired + cells + constraint-clustered CIs — [`freeze/analysis-plan.yaml`](../freeze/analysis-plan.yaml) |
| Deferred | DPO/ORPO/KTO/RLHF, QAT, learned critic, public release, production replacement, named-author style prompts |

## Corpus fingerprint (stats only)

11 files present, ~2.85M words, ~240k sentences. Balanced sampling target: ≈ equal accepted passages
per file (not proportional to size), ≤ 15% of target tokens from any one source.

## Privacy / IP posture (enforced by construction)

- Gold targets are unchanged professional passages held in git-ignored `private-data/`; referenced by
  offset + hash. Offset-bearing passage/record/held-out manifests are git-ignored (offsets into a
  named book are retrieval keys).
- Model-visible packets exclude source filenames, author names, titles, passage IDs, and distinctive
  source wording; two-representation design (provenance vs training packet) + retrieval-risk review.
- Overlap/eval results record counts + locations, never matched text. Source prose is never
  reproduced in assistant output or committed files.

## Next: Phase 1 → Phase 2 (needs a go + human review)

- **Phase 1 (fingerprint):** done for the manifest (hashes + counts). A normalized private copy step
  (still Phase 1) would write normalized source copies to git-ignored `private-data/normalized-sources/`.
- **Phase 2 (segment candidate passages):** this is the first step that writes **verbatim scene-sized
  excerpts** to git-ignored `private-data/targets/` (by offset), and it explicitly requires
  **human review of scene boundaries and coherence**. It will not be surfaced in chat.

Phase 0 deliverable checklist: [x] migrate + supersede · [x] source policy · [x] 11-file manifest ·
[x] schemas · [x] freeze contract/analysis/model/serializer/verifier · [x] migration + freeze reports.
Pending: go-ahead + human boundary review to begin Phase 2 segmentation.
