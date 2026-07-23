# DISPATCH 30A — PAUSED (source-role change) — 2026-07-23

**Status: PAUSED at the Phase 3 / Phase 4 boundary, pending a replacement dispatch.**
Do not begin scene selection, packet back-translation, dataset freezing, atomic/compositional
pairing, train/eval splits, or any real LoRA. All completed scaffolding, schemas, scripts,
manifests, and reports are preserved.

## Why paused

The source policy has changed in a way that alters the experiment's central design:

- The active Dispatch-30A contract treats the **eleven professional fantasy files as instrumentation
  only** (never SFT targets).
- The **revised decision** is to use **selected scene-sized excerpts from those eleven files as the
  actual gold completions.**

This changes scene selection, packet back-translation, dataset manifests, memorization probes,
provenance rules, eval separation, and the interpretation of the atomic-vs-compositional arms.
Continuing under the old contract would build the wrong corpus.

## Safe checkpoint reached (preserved, still valid)

Everything below is **source-role-independent** and remains useful under the new plan:

- Experiment directory + artifact structure, README.
- Generic schemas (`scene-packet`, `training-record`, `verifier-result`, `review-result`).
- Frozen model revision, serializer version, analysis plan (McNemar paired, constraint-clustered CIs).
- **Verifier (Phase 3): `verifier.py` v1, validated 14/14 fixtures (100%, 0 false pos / 0 false neg),
  frozen (hash in `freeze/verifier-version.json`).** Deterministic checks + advisory-semantic stubs +
  signature-stacking + surface metrics.
- **Signature-stacking calibration:** professional prose stacks ≥2 families in only **2.06%** of
  ~201k sentences — anti-slop floor well-founded, detector not over-firing
  (`reports/signature-stacking-calibration.json`).
- Professional-reference manifest (11 files by sha256) — still the overlap-screening baseline.

## SUPERSEDED by the coming replacement dispatch

- `freeze/experiment-contract.yaml` → `source_roles` (professional files = instrumentation only) and
  the Gary-manuscript-only gold policy are **superseded**. Do not treat that section as authoritative.
- Any plan step that assumed manuscript-only gold targets or professional-files-excluded-from-targets.

## Redesign requirements the replacement dispatch must specify

1. **Gold-source policy** — selected excerpts from all eleven named files become targets.
2. **Scene segmentation** — coherent 500–1,400-word passages, with source offsets + hashes (segments
   stay local/git-ignored; never committed; never reproduced in chat).
3. **Balanced sampling** — ~equal accepted scenes per source, not proportional to file size.
4. **Packet abstraction** — back-translated packets capture transferable scene *mechanics* without
   becoming retrieval keys for the original passage (no source names/places/canon/distinctive beats).
5. **Atomic control** — full-scene generation from reduced packets, matched against compositional
   full-scene generation (same targets, constraint-density the only variable).
6. **Original-world primary evaluation** — no source worlds, characters, canon, or distinctive
   situations in the eval packets.
7. **Memorization testing** — exact overlap, paraphrased reconstruction, scene-sequence reproduction,
   source-name leakage, and training-packet continuation probes.
8. **Interpretation** — cleanly distinguish improved prose *behavior* from memorized/reconstructed
   published scenes.

## Aedan may continue (source-role-independent)

experiment structure · generic schemas · hashing/provenance utilities · overlap-detection tooling ·
detector hardening · training-harness smoke tests **with disposable data** · checkpoint + evaluation
infrastructure · blind-review tooling · generic packet validators.

## Aedan must stop (until the replacement dispatch)

selecting AoS/Norse scenes · requesting manuscript files · constructing manuscript-derived packets ·
freezing the training corpus · constructing atomic/compositional target pairing · finalizing
train/eval splits · running any real LoRA · assuming the professional files are excluded from target
data.

## Note for the replacement build (operational)

Under the new plan the gold targets are excerpts of third-party copyrighted prose. The tooling
processes them **locally only** — segment offsets + hashes, overlap detection, verification — and
those segments/targets must remain git-ignored and must never be reproduced in assistant output.
The existing gitignore already blocks `training text/` and the pilot's `datasets/`, `outputs/`,
and manuscript/same-world manifests; the replacement dispatch should extend the ignore set to any
new segment/target manifests it introduces.
