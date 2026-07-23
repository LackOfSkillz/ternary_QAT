# Dispatch 27 Phase B — Focused-Revision Failure Audit

**Primary target of the pilot.** Supplementary probe on the multi-constraint three-fix revision
items (`pf-focused_revision-{compact,realistic,long_salience_repaired}`) that the frozen 14-item
subset does not directly test. Machine-readable:
[`dispatch-27-focused-revision-audit.yaml`](dispatch-27-focused-revision-audit.yaml).

The three authorized corrections per item: remove the anachronistic phone, repair the "sleeping
giant" overwritten simile, and reduce the repeated "She" sentence-openers — while keeping the
protected opening line exact. An **unchanged-return** failure = all three defects retained.

| role | unchanged-return | mean fixes (of 3) | all-three-fixed | protected preserved |
|---|---|---|---|---|
| qwen3_8b_base | **0.667 (2/3)** | 0.333 | 0 | 1.0 |
| lora_step-3 … step-21, final | **0.667 (2/3)** | 0.333 | 0 | 1.0 |

## Answers to the five required questions

1. **Did any checkpoint reduce unchanged-return failures?** No — every checkpoint is 0.667, identical to base.
2. **Did any checkpoint apply all three authorized corrections?** No — all-three-fixed = 0 for base and every checkpoint.
3. **Did any checkpoint preserve the protected line while improving?** The protected line is preserved everywhere (1.0), but there is no improvement to accompany it.
4. **Did any checkpoint introduce over-editing?** No — protected preservation stays 1.0; no unauthorized rewrite of the protected sentence.
5. **Consistent across compact/realistic/long-salience forms?** Yes — uniformly neutral across all three packet forms.

**Conclusion:** the conservative LoRA does **not** touch the primary target. The base's
multi-constraint focused-revision weakness (returns unchanged 2/3 of the time) is **exactly
unchanged** by the pilot. This is a neutral, non-destructive result — the honest signal that 42
training records at LR 1e-5 is insufficient to move this behaviour.

**Measurement honesty:** this item-level unchanged-return rate (0.667 on 3 items) is NOT the same
measurement as the external reviewer-level fatal rate (~0.20 over 60 reviews) and is not compared
to it directly.
