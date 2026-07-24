# Batch 1 structural re-abstraction — Dispatch 30A-R1 (metadata only)

One targeted revision pass on the 10 flagged c02 packets. Provenance and targets unchanged.

```yaml
batch_1_revision:
  packets_revised: 10
  compositional_revised: 10
  atomic_revised: 0 (where the same identifier appeared)
  provenance_changed: 0
  target_changed: 0
```

## Fair before/after (same auditor calibration)
```yaml
structural_risk_before: {'high': 7, 'medium': 4}
structural_risk_after:  {'high': 5, 'medium': 6}
high_resolved_by_revision: 2   # of 7 originally high
unresolved_high: 5
recommendations_after: {'abstract_further': 5, 'accept_with_medium_risk': 6}
```

## Validation
```yaml
schema_valid: True
target_hash_match: True
context_fit_8192: 22/22
lexical_risk: {low: 11}
compositional_constraints: [9, 9] meaningful, [7, 7] load-bearing
atomic_constraints: [1, 2]
atomic_total_tokens: [2922, 4685]
compositional_total_tokens: [3160, 4921]
```

## Finding
One pass moved 2 of 7 high-risk packets to medium; the other 9 held. **5 packets remain HIGH** — their distinctive core (fused two-segment structure, source-specific world rule, iconic set-piece reveal) is inherent to supervising those specific scenes, and cannot be removed without gutting the supervision. Per protocol these 5 require individual Gary review. Per-passage reasons kept private (they are themselves scene-identifying).

## Privacy
No source prose, packet text, names, or scene descriptions committed. Revised packets, provenance, targets, audits, and the viewer stay git-ignored.