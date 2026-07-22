# Dataset A.3 pilot — audit report

**48 records** (pilot; training_only; single-teacher `claude-opus-4-8`; review_status=draft, Gate-3 review PENDING). Below the 300–500 production target — the **documented justified exception** (see DESIGN-CONTRACT): the remainder requires human authorship/curation + teacher diversification + Gary review.

## Task mix (records)
- anti_repetition_and_slop: 2 (0.042) vs target 0.05
- canon_application: 5 (0.104) vs target 0.1
- focused_revision: 10 (0.208) vs target 0.2
- multi_turn_revision: 2 (0.042) vs target 0.05
- no_change_and_restraint: 5 (0.104) vs target 0.1
- scene_drafting: 12 (0.25) vs target 0.25
- structured_protocol: 5 (0.104) vs target 0.1
- voice_preservation: 7 (0.146) vs target 0.15

## Token mass (word-count proxy — logged substitution)
- anti_repetition_and_slop: share 0.02, avg 21.5, max 24
- canon_application: share 0.102, avg 44.6, max 69
- focused_revision: share 0.136, avg 29.5, max 47
- multi_turn_revision: share 0.01, avg 11.0, max 14
- no_change_and_restraint: share 0.046, avg 20.0, max 29
- scene_drafting: share 0.51, avg 92.5, max 103
- structured_protocol: share 0.037, avg 16.0, max 29
- voice_preservation: share 0.14, avg 43.4, max 67

## Coverage
- changed_true=17, changed_false=4 (both present ✓)
- structured_protocol records=5
- distinct style registers=14, genres=13

## Integrity
- benchmark overlap: CLEAN (max 0.0, threshold 0.10)
- max pairwise template Jaccard: 0.0 (near-dup pairs: 0)
- provenance: {'model_authored': 48}; unknown never guessed
- pools: {'training': 48}; zero benchmark/calibration/permanent-trend in training

## Freeze
- record_count=48, training=48, token_proxy=2177
- train_sha256=91e572421fe6bdef110bbf2855e331286987b0377de7013886782c608d3a206e
- full_corpus_sha256=91e572421fe6bdef110bbf2855e331286987b0377de7013886782c608d3a206e

Dataset A and Dataset A.2 are unchanged by this work.
