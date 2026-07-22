# Qwen3-8B LoRA checkpoint curve — report

Base + 8 LoRA checkpoints on the frozen 14-item subset (126 generations, non-thinking, greedy). All roles have 14 items: True.

| role | mechanical | core-prose | focused-rev | structured | no-change | canon | severe-slop | token-cap | reason-leak | critical-regr |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen3_8b_base | 11/14 (0.786) | 0.857 | 1.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | - |
| lora_step-3 | 11/14 (0.786) | 0.857 | 1.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0 |
| lora_step-6 | 11/14 (0.786) | 0.857 | 1.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0 |
| lora_step-9 | 11/14 (0.786) | 0.857 | 1.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0 |
| lora_step-12 | 11/14 (0.786) | 0.857 | 1.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0 |
| lora_step-15 | 11/14 (0.786) | 0.857 | 1.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0 |
| lora_step-18 | 11/14 (0.786) | 0.857 | 1.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0 |
| lora_step-21 | 11/14 (0.786) | 0.857 | 1.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0 |
| lora_final | 11/14 (0.786) | 0.857 | 1.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 0 |

**Result: the LoRA is mechanically NEUTRAL** — every checkpoint matches the base on mechanical pass, core-prose, and structured output, with **zero critical regressions**, zero severe slop, zero token-cap, zero reasoning-trace leakage. The conservative pilot (42 records, LR 1e-5, ~1 epoch) is completely non-destructive but produces no measurable mechanical improvement.

Provisional best (mechanical, pre-blind): **lora_step-3** (all checkpoints tie; earliest eligible).

No-change accuracy is 0.0 for base AND all checkpoints (a base weakness on the single no-change item, unchanged by the LoRA).
