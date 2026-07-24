# Held-Out c01 — Final (Dispatch 30F)

**Status:** frozen_heldout_eval  ·  **set_id:** heldout-c01  ·  **Authority:** Dispatch 30F  ·  **Serializer:** `lw-scene-packet-serializer-v1`

Permanent held-out EVALUATION + retrieval-safety set. `training_eligible: 0`, `evaluation_eligible: 11`.
Never enters SFT training (enforced by scripts/serialization_guard.py). Metadata only.

## Records & split
| | value |
|---|---|
| records | 11 |
| training_eligible | 0 |
| evaluation_eligible | 11 |
| schema-valid | 11 |
| target-hash match | True |
| lexical risk | low x11 |
| id / name leaks | 0 / 0 |
| target 5-gram overlap (max) | 0 |
| context fit 8192 (22 records) | 22 |

## Atomic purity (independent)
| records_checked | clean | hidden_compound_flags | revised | unresolved |
|---|---|---|---|---|
| 11 | 11 | 0 | 0 | 0 |

## Structural risk — independent audit, one targeted re-abstraction (metadata, NOT an inclusion gate)
| | low | medium | high |
|---|---|---|---|
| before revision | 2 | 5 | 4 |
| after revision | 2 | 6 | 3 |

1 targeted pass on 4 high; lor high->medium; sanderson/HP/got remain high (retained as retrieval-safety probes, NOT excluded)

## Evaluation cohorts (analysis-only)
| cohort | records |
|---|---|
| heldout_low | 2 |
| heldout_medium | 6 |
| heldout_retrieval_sensitive | 3 |

## Constraint distribution
- meaningful: {7: 6, 8: 3, 9: 2} (range 7-9)
- load-bearing: {5: 5, 6: 5, 7: 1} (range 5-7)
- identical_across_all_11: **False** — natural variation restored (loosened brief) — meaningful spans 7-9, not the prior uniform 8

## Limitation
- **opening_scene_bias_noted: True** — the set is drawn from each source's earliest harvested chapter and may overrepresent setup/introduction/orientation/inciting structures vs the c02-c06 training distribution. (Note: several c01 records were found NOT to be literal chapter-one openings — some are mid/late-book scenes — which partly diversifies scene type. Do not "correct" the bias by adding later scenes to the held-out set.)

Token totals: compositional 3801-5784, atomic 3322-5370.
Guard: scripts/serialization_guard.py rejects split=heldout_eval / training_eligible=false.
