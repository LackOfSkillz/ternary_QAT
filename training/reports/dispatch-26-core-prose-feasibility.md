# Dispatch 26 — Core-Prose Feasibility (frozen threshold applied)

The **frozen** research-continuation core-prose floor (**0.50**, `research-continuation-v0.yaml`
sha256 `2be4fddb…`, lock `a4451674`) applied unchanged to all three models over the 7 Fast-Battery
core-prose items (modules A + B, prose output). Machine-readable:
[`dispatch-26-core-prose-feasibility.yaml`](dispatch-26-core-prose-feasibility.yaml).

| Model | core-prose pass | clears 0.50 floor | clears ALL frozen floors | failed floors |
|-------|-----------------|-------------------|--------------------------|---------------|
| **Qwen3-8B (non-thinking)** | **0.857** | ✅ | ✅ | — |
| **Ministral-3-8B-Instruct** | **0.714** | ✅ | ❌ | `modules_with_usable < 7` (5/9) |
| Ternary-Bonsai 4B (control) | 0.286 | ❌ | ❌ | `core_prose < 0.50` |

**Both stronger bases decisively clear the 0.50 core-prose floor that the untouched 4B failed
(0.286).** This answers Dispatch 26's primary question: *yes* — a stronger ~8B base clears the
frozen core-prose research threshold, confirming the Dispatch-25 `test_stronger_base` branch was
correct (the bottleneck was base capacity, not the dataset).

All floors, per candidate (Fast Battery, comparable to the 4B's Dispatch-24 baseline):

| Floor (frozen) | Qwen3-8B | Ministral | 4B |
|----------------|----------|-----------|-----|
| mechanical ≥ 0.40 | 0.75 ✅ | 0.45 ✅ | 0.45 ✅ |
| core-prose ≥ 0.50 | 0.857 ✅ | 0.714 ✅ | 0.286 ❌ |
| modules_with_usable ≥ 7 | 7 ✅ | 5 ❌ | 7 |
| bare ≥ 0.40 | 0.737 ✅ | 0.421 ✅ | 0.421 |
| severe-slop ≤ 0.25 | 0.0 ✅ | 0.0 ✅ | 0.05 |
| token-cap ≤ 0.25 | 0.0 ✅ | 0.026 ✅ | 0.15 |
| realistic-packet ≥ 0.35 | 1.0 ✅ | 1.0 ✅ | 1.0 |
| reasoning-trace leak | 0.0 ✅ | 0.0 ✅ | — |

**Qwen3-8B clears every frozen floor.** Ministral clears core-prose but fails module-coverage
(mechanically passes only 5 of 9 modules; its failures concentrate in structured-protocol tasks).
The threshold was applied honestly and unchanged — not tuned to this result.
