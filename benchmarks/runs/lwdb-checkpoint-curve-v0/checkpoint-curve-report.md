# Existing-Checkpoint Curve (Dispatch 25, D8)

A real comparison of the untouched base and the two existing LoRA checkpoints (step-10,
step-20) from the `dataset-a-full-comparison-v1` run, on a **9-item diagnostic subset frozen
before generation**. Threshold-locked analysis. **No new checkpoints were invented; no winner
is declared.** Subset: short scene, long scene, surface bare, surface compiled, restraint
clean, focused revision, canon application, structured protocol, stability-long.

## Curve (9 items per checkpoint)

| checkpoint | mechanical pass /9 | severe slop /9 | token-cap hits /9 |
|---|---|---|---|
| target_base | 5 | 0 | 2 |
| LoRA step-10 | 5 | 0 | 2 |
| LoRA step-20 | **2** | **6** | **6** |

## Answers

```yaml
early_improvement: false          # LoRA-10 does NOT beat base (it matches it)
late_collapse: true               # LoRA-20 collapses vs LoRA-10
degeneration_onset: step-20       # between step-10 and step-20
best_observed_checkpoint: target_base
monotone_worsening: true
stable_capabilities: "the same items base handles (structured-protocol scene contract, etc.) survive at step-10"
regressed_capabilities: "scene drafting, canon application, surface, stability — all collapse to severe/token-cap at step-20"
```

## Interpretation (evidence-grounded, provisional)

- **LoRA step-10 is neutral**, not an improvement: it matches the base (5/9 mechanical, 0
  severe). The training taught nothing measurable by step-10 on this subset.
- **LoRA step-20 collapses**: mechanical pass halves and severe slop / token-cap jump to 6/9.
  The degeneration onset is **between step-10 and step-20** — an over-exposure / over-training
  signature (consistent with Dispatch-20: min-loss 0.08 at step-20, ~5 epochs over 28 records).
- Because no checkpoint improves over base and the curve is monotone-worsening, **selecting an
  earlier checkpoint is not a path to a better model** here, and continuing this training regime
  is contraindicated. This corroborates (does not by itself decide) the Dispatch-25 branch.

## Limitations

- 9-item diagnostic subset, not the full battery.
- Only existing checkpoints (base, step-10, step-20); step-5/step-15 were not saved.
- Greedy decoding; slop thresholds unvalidated. Prose quality is reviewer-pending.
