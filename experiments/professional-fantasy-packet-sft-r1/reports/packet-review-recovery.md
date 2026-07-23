# Packet review recovery — Dispatch 30A-R1

**Recovery reason:** original browser decision export lost after workstation reboot; reconstructed from the recovered review (private `accept.txt`, never committed).

## Authoritative outcome
- 11 passages reviewed, **11 accepted**, 0 rejected, 0 deferred, 0 boundary changes requested.
- Passage IDs: abercrombe-c01, sanderson-c01, gord-c01, mouser-c01, wot-c01, pawn-c01, streams-c01, lies-c01, lor-c01, HP-c01, got-c01.

## Integrity verification
- **11/11 verified**: source SHA-256, target SHA-256, offsets, and word counts all recover from the frozen normalized sources.
- **Correction (1):** `got-c01` had been truncated to a 250-word slice (`1056715-1057980`) by an accidental in-app `adjust_start`. Restored to the original harvest scene **2,386 words @ `1045159-1057980`** (target SHA-256 `f2f78af8…`), matching the recovered review's word count and the harvest boundary. The recovery-table start value `1057247` was a transcription error and was not used. Other ten passages unchanged.

## Review gate
```yaml
packet_review_gate:
  passages_reviewed: 11
  passages_accepted: 11
  passages_excluded: 0
  human_gate_passed: true
```

## Retrieval-risk (diagnostic; reviewer accepted despite ratings)
```yaml
lexical_identifier_risk: {low: 11}
structural_reconstruction_risk: {low: 3, medium: 5, high: 3}
human_disposition: {accepted_after_review: 11, automatic_abstraction_requested: 0}
```

## Sequence length
- Frozen `max_sequence_length: 8192` retained. Exact Qwen3-8B totals — atomic {min(atom)}-{max(atom)}, compositional {min(comp)}-{max(comp)}; **fits_8192: 22/22**; gold targets never truncated.

## Privacy
- No source prose committed. `accept.txt`, provenance/training packets, records, targets, and the recovery audit remain git-ignored. This report contains only IDs, counts, offsets, and hash prefixes.