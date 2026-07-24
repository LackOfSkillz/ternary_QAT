# Batch 2 (c03) — Provisional Review (Dispatch 30A-R1)

**Status:** provisional_pending_review — paused for Gary's review. Metadata only (no packet text, prose, offsets, or full hashes).

## Production
| check | value |
|---|---|
| passages processed | 11 |
| matched pairs | 11 |
| schema-valid | 11 |
| target-hash match | True |
| lexical risk | low ×11 |
| id / name leaks | 0 / 0 |
| target 5-gram overlap (max) | 0 |
| context fit 8192 (22 records) | 22 |
| compositional token totals | 4051–5257 |
| atomic token totals | 3564–4765 |

## Constraint distribution — now VARIED (Batch 1 was uniform 9 meaningful / 7 LB)
- meaningful: {'7': 3, '8': 7, '9': 1} (range 7–9)
- load-bearing: {'5': 3, '6': 7, '8': 1} (range 5–8)
- identical across all 11: **False**

## Structural risk — independent audit, one targeted re-abstraction
| | low | medium | high |
|---|---|---|---|
| before revision | 3 | 5 | 3 |
| after revision | 3 | 6 | 2 |

Re-abstraction scope: 3 high (lor,HP,got); HP high->medium, lor+got remain high (further abstraction would gut supervision)

## Provisional cohorts (pending human dispositions)
| cohort | pairs |
|---|---|
| primary_low | 3 |
| primary_medium | 6 |
| retrieval_sensitive_high | 2 |
| excluded | 0 |

Viewer (private): `private-data/packet-review-batch2rev/index.html`

Batch 3 started: False · serialization: False · training: False
