# SFT Training Results (Dispatch 30G)

Both runs completed on GX10 (NVIDIA GB10). Identical recipe; only the packet representation differs.

## Smoke tests (5 steps)
| arm | finite loss | finite grads | OOM | peak GB |
|---|---|---|---|---|
| atomic | true | true | false | 36.96 |
| compositional | true | true | false | 39.07 |

## Full runs (1 epoch, 27 steps, 9 checkpoints each)
| | atomic | compositional |
|---|---|---|
| train loss start -> end | 2.5349 -> 2.6602 | 2.546 -> 2.6489 |
| min loss | 2.5349 | 2.5124 |
| peak GPU (GB) | 39.46 | 41.61 |
| seconds | 479.8 | 538.3 |
| finite throughout | True | True |
| NaN/inf events | 0 | 0 |
| interruptions | 0 | 0 |
| final adapter (prefix) | 810461f6f60a | 232ee7e7103d |

Loss divergence between arms: none (both ~2.5->2.65). Held-out used for tuning: false.

## Adapter load checks (synthetic generation only; no held-out data)
| arm | loadable | base_revision_match | generation_test |
|---|---|---|---|
| atomic | true | true | successful |
| compositional | true | true | successful |
