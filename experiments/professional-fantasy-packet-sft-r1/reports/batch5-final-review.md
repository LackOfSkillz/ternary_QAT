# Batch 5 (c06) — Final Review, Pre-Approved (Dispatch 30E)

**Status:** final_preapproved  ·  **Decision authority:** Dispatch 30E  ·  **Serializer:** `lw-scene-packet-serializer-v1`

Pre-approved under the established cohort policy (Dispatch 30E). Cohorts assigned automatically by mapping
the final independent post-revision structural rating to its disposition. Metadata only.

## Cohorts (automatic pre-approval mapping)
| cohort | pairs |
|---|---|
| primary_low | 1 |
| primary_medium | 6 |
| retrieval_sensitive_high | 3 |
| excluded | 0 |
| **accepted total** | **10** |

The 3 retrieval-sensitive pairs retain independent rating **high** with
`human_override: true` (accept_as_retrieval_sensitive). No rating was downgraded to fit a cohort.

## Integrity
| check | value |
|---|---|
| schema-valid | 10 |
| target-hash match | True |
| lexical risk | low x10 |
| id / name leaks | 0 / 0 |
| target 5-gram overlap (max) | 0 |
| context fit 8192 (20 records) | 20 |
| contradictory | 0 |
| unresolved | 0 |

## Atomic purity (independent audit)
| records_checked | clean | hidden_compound_flags | revised | unresolved |
|---|---|---|---|---|
| 10 | 10 | 0 | 0 | 0 |

## Structural risk — independent audit, one targeted re-abstraction
| | low | medium | high |
|---|---|---|---|
| before revision | 1 | 5 | 4 |
| after revision | 1 | 6 | 3 |

1 targeted pass on 4 high (wot,lor,HP,got); HP high->medium, wot/lor/got remain high (distributed identifiability; further abstraction would gut supervision per auditor)

## Constraint distribution
- meaningful: {8: 10} (range 8-8)
- load-bearing: {5: 5, 6: 5} (range 5-6)
- **identical meaningful across all 10: True** — all 10 land at meaningful 8 — genuinely derived (3 beats+3 soft or 4 beats+2 soft), within 5-9, none padded to 9, no silent clamp; LB varies 5-6. Flagged for transparency; not a §5 stop condition.

Token totals: compositional 2476-4150, atomic 2068-3702.
