# Dataset A.2 — Expansion Plan (Dispatch 21, Phase I)

How to grow the validated pilot into a full corpus **after** it passes all gates. These
are planning ranges driven by the Phase-B coverage deficits, not quotas. Do not add filler
records to reach a count.

## Target scale

```yaml
training_records: 150-250
held_out_records: 40-60
```

## Planning ranges by task family

```yaml
focused_revision:   60-100   # incl. no-change + changed:true protocol, voice preservation
no_change_restraint: 25-40   # both halves; exact-preservation enforced
canon_extraction:   20-30    # belief/established discrimination, hearsay
constraint_checking: 20-30   # minimal causal set; no over-inclusion
scene_contract:     20-30    # exact field set (A.2 resolves the field ambiguity)
fiction_boundary:   15-25    # in-scene fulfillment vs real-harm refusal
```

## Priorities, from the evidence

Expansion is driven by the Phase-A/B deficits, in order:

1. **No-change protocol, both halves.** Dataset A taught `changed:false` twice and
   `changed:true` never. Reach 25–40 no-change records *and* enough `changed:true`
   structured revisions that the model learns *when* to emit the wrapper.
2. **Repetition/degeneration resistance.** Absent in Dataset A. Every family should carry
   *rejected* degenerate examples (loops, runaway length) so the failure mode is in-corpus.
3. **Schema exactness incl. nested keys.** Add rejected alternate-key examples
   (`speaker`/`claim`), stray-content-after-structure, and YAML field drift.
4. **Causal-set minimality.** Constraint records with rejected over-inclusion, since even
   the untouched base over-includes (`K1,K2,T1` vs `K1`).
5. **Voice preservation that performs the change.** Styled single-defect revisions with
   rejected imposed-minimalism / voice-flattening (reviewer-assisted) and rejected
   omitted-change (machine-detected).
6. **Held-out breadth.** Each important behavior must be tested by **several independent**
   evaluation records (Dataset A tested each by one), with disjoint source clusters.

## Rules during expansion

- Every record passes `scripts/validate_a2.py` (shape + content gates + split grouping)
  before entering the corpus.
- Story worlds / source families are tracked so `held_out` clusters never appear in train
  (Phase D), verified automatically.
- Provenance is truthful per record; model-authored stays model-authored regardless of
  human review.
- No expansion is justified by record count alone; each record repairs a named coverage
  deficit or adds an independent held-out test.
- Expansion does not begin until the pilot clears the Phase-J readiness gate.
