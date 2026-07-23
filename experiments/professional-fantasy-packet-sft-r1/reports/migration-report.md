# Migration report — Dispatch 30A → 30A-R1

**30A-R1 supersedes Dispatch 30A in full.** No artifacts were deleted; prior work is preserved with
hashes and provenance and marked superseded where its assumptions changed.

## Preserved (reused, source-role-independent)

| Prior artifact (30A pilot) | Disposition in R1 |
|---|---|
| `verifier.py` (v1, validated 14/14 fixtures, hash `11e4d9f1…`) | **migrated unchanged** to `scripts/verifier.py`; re-validated 14/14 in the R1 root; hash identical (provenance continuity) |
| `validate_verifier.py`, `calibrate_signature_stacking.py` | migrated unchanged |
| Schemas `scene-packet`, `verifier-result`, `review-result` | carried over unchanged |
| Signature-stacking calibration (pros stack ≥2 families in 2.06% of ~201k sentences) | still valid; anti-slop floor stands |
| Experiment structure, freeze discipline, analysis-plan shape | reused |

The paused 30A pilot directory (`experiments/fantasy-compositional-sft-pilot/`) is retained with its
`PAUSE-30A-source-role-change.md` and a SUPERSEDED banner pointing here.

## Assumptions replaced

| Old (30A) | New (30A-R1) |
|---|---|
| Gary's AoS/Norse manuscripts supply the gold targets | **Selected scene-sized passages from the eleven professional files** are the gold targets |
| The eleven professional files are instrumentation only | They are gold-target sources **and** reference bands **and** the memorization-comparison corpus |
| Professional prose prohibited from the SFT dataset | Professional prose (unchanged) **is** the SFT completion |
| Same-book held-out passages could anchor evaluation | Held-out professional passages are a **secondary** set only; the headline is **original-world** |

## Data artifacts

No manuscript-derived material was ever created in 30A (it paused at the Phase 3/4 boundary before
scene selection), so none remains in the experiment. No AoS/Norse content exists in either root.
No training corpus, packets, pairings, or splits were built. No training was run.

## New R1 additions (this Phase 0)

- `manifests/professional-source-files.json` — 11 files fingerprinted (sha256 + word/sentence counts
  + three roles), statistics only, no prose; `HP.txt`/`got.txt` bound to the dispatch's `(1)` aliases.
- `freeze/source-policy.yaml` — the new source-role + privacy + retrieval-key policy.
- `freeze/experiment-contract.yaml`, `analysis-plan.yaml`, `model-revision.json`, `serializer-version.json`.
- New schemas `passage-manifest`, `training-record` (professional target + provenance/training packet),
  `overlap-result` (counts + locations, never matched text).

## Privacy posture (enforced)

`private-data/`, `datasets/`, `outputs/`, `checkpoints/`, `reviews/`, and every offset-bearing
passage/record/held-out manifest are git-ignored (an offset into a named book is a retrieval key).
Only design scaffolding, stats-only reports, the hash-only source manifest, and the original eval
sets are committed. Source prose is never reproduced in committed files or assistant output; verbatim
excerpts live only in local git-ignored storage, handled by offset + hash.
