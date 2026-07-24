# Batch 4 (c05) — Provisional Review (Dispatch 30C)

**Status:** provisional_pending_review — paused for Gary's review. Metadata only (no packet text, prose, offsets, or full hashes).

## Production
| check | value |
|---|---|
| passages processed | 11 |
| matched pairs | 11 |
| schema-valid | 11 |
| target-hash match | True |
| lexical risk | low x11 |
| id / name leaks | 0 / 0 |
| target 5-gram overlap (max) | 0 |
| context fit 8192 (22 records) | 22 |
| compositional token totals | 3295-4692 |
| atomic token totals | 2809-4321 |

## Atomic purity (hidden-compound detection)
| records_checked | clean | hidden_compound_flags | revised |
|---|---|---|---|
| 11 | 11 | 0 | 0 |

## Constraint distribution — spine-first authoring (fixes Batch 3 drift)
- meaningful: {7: 1, 8: 8, 9: 2} (range 7-9); 2 at the 9 cap (stop threshold >7)
- load-bearing: {5: 3, 6: 7, 7: 1} (range 5-7)
- identical_across_all_11: **False**
- spine-first authoring fixed Batch 3 drift: meaningful now spans 7-9 with mode at 8 (only 2 at the cap, well under the >7 stop threshold); 9 packets were initially over-cap and revised explicitly (no silent clamp)

## Structural risk — independent audit, one targeted re-abstraction
| | low | medium | high |
|---|---|---|---|
| before revision | 3 | 3 | 5 |
| after revision | 4 | 2 | 5 |

Re-abstraction scope: 6 flagged (5 high + wot medium); after 1 pass wot medium->low, the 5 high remained high

Auditor note: auditor: abercrombe/got/mouser could drop further with one more targeted move (a different element); lor/HP are distributed-identifiability (would gut supervision, rec exclude). Held per one-pass policy for Gary's revise/accept/exclude decision. mouser had a leaked identifier in character_goals which was scrubbed (model-visible cleanup, not a rating pass).

## Provisional cohorts (pending human dispositions)
| cohort | pairs |
|---|---|
| primary_low | 4 |
| primary_medium | 2 |
| retrieval_sensitive_high | 5 |
| excluded | 0 |

Viewer (private): `private-data/packet-review-batch4rev/index.html`

Batch 5 started: False - serialization: False - training: False
