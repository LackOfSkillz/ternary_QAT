# Full accepted-set freeze — Dispatch 30A-R1 (metadata only)

**Accepted passages: 65** (target: 65). Integrity: all hashes recover, word counts match, 0 duplicate targets, 0 overlapping pairs.

## By source
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

## Ranges
- Word count: 1284–3713
- Target tokens (exact Qwen3-8B): 1828–5041
- Conservative compositional total (target + 609 max packet/system/template): 2437–5650
- **Context fit: 65/65 fit 8192; overflow: 0**  (gold targets never truncated)

## Boundary adjustments
- Valid round-2 start edits applied: mouser-c06, pawn-c06, got-c06.
- Accidental near-end adjust_start values IGNORED: got-c01 (1057247; kept 2386w) and sanderson-c02 (30428 → 17 words; kept original 3107w, **pending your confirmation**).

## Source-minimum gate
- Sources at/above 6: 10/11.  Below 6: sanderson.txt=5 → Phase 3B harvests sanderson-c06.

## Privacy
- No source prose, dialogue, scene summaries, or provenance contents committed. Targets, records, offsets, decisions, and audits remain git-ignored. This report is IDs/counts/ranges/hash-prefixes only.