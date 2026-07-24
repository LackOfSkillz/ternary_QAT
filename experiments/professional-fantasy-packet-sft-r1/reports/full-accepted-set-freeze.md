# Full accepted-set freeze — Dispatch 30A-R1 (metadata only)

```yaml
corpus_freeze:
  status: final
  total_passages: 65
  source_minimum_gate: passed_with_one_approved_exception
  approved_exceptions: [sanderson.txt]
```

**65 passages, FINAL.** Integrity: all hashes recover, word counts match, 0 duplicate targets, 0 overlapping pairs.

## By source (final)
```yaml
HP.txt: 6
abercrombe.txt: 6
gord.txt: 6
got.txt: 6
lies.txt: 6
lor.txt: 6
mouser.txt: 6
pawn.txt: 6
sanderson.txt: 5
streams.txt: 6
wot.txt: 6
```

## Ranges & context fit
- Word count: 1284–3713
- Target tokens (exact Qwen3-8B @ b968826d): 1828–5041
- Conservative compositional total (target + 609 max packet/system/template): 2437–5650
- **Context fit: 65/65 fit 8192; overflow: 0. Gold targets never truncated.**

## Boundary adjustments
- Valid round-2 start edits applied: mouser-c06, pawn-c06, got-c06.
- Accidental near-end adjust_start values ignored (both confirmed by Gary): got-c01 (kept 2386w) and sanderson-c02 (kept original 3107w).

## Source-minimum gate
- 10/11 sources at 6. **sanderson.txt = 5: approved source-length exception** — its ~14,042-word narrative body is fully covered by five non-overlapping coherent passages (14,032 words; largest free gap ~3 words). No replacement pending; no overlap or re-slicing used.

## Privacy
- No source prose, dialogue, scene summaries, or provenance contents committed. Accepted manifest, targets, decisions, token payloads, and source-bearing audits remain git-ignored. This report is IDs/counts/ranges/hash-prefixes only.