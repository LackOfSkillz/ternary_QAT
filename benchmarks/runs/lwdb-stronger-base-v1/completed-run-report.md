# Stronger-Base Comparison — Completed Run Report (Dispatch 26)

**Run `lwdb-stronger-base-v1`, plan_hash `d45a04a9…`.** Controlled three-model comparison; the
base model is the ONLY changed variable. No training, no dataset change, no threshold change.

## Execution

- **94 / 94 jobs completed**, **0 integrity problems**, **mechanical replay identical**
  (instrument-valid). Fast Battery 20 items × {Ministral, Qwen} = 40 (4B reused from Dispatch 24);
  Packet Family 18 items × 3 roles = 54.
- Greedy/deterministic (temp 0.0, seed 20260722, max_new_tokens 1024), settings identical to
  Dispatch 24. Ministral FP8 text-only via `kernels==0.15.2` (`fix_mistral_regex=True`); Qwen3
  `enable_thinking=False` — **zero `<think>` traces in any of its 38 outputs**.
- Roles: `target_base_4b` (prism-ml/Ternary-Bonsai-4B-unpacked), `ministral_3_8b_instruct`
  (mistralai/Ministral-3-8B-Instruct-2512 @ `5b26027e`, FP8), `qwen3_8b_non_thinking`
  (Qwen/Qwen3-8B @ `b968826d`). Host assignment is excluded from reviewer artifacts.

## Headline results

| | Qwen3-8B | Ministral-3-8B | 4B (control) |
|---|---|---|---|
| core-prose (frozen floor 0.50) | **0.857 ✅** | **0.714 ✅** | 0.286 ❌ |
| mechanical pass | 0.75 | 0.45 | 0.45 |
| modules_with_usable (≥7) | 7 ✅ | 5 ❌ | 7 |
| severe slop / token-cap | 0 / 0 | 0 / 0.03 | 0.05 / 0.15 |
| reasoning-trace leak | 0 | 0 | — |
| blind prose quality (2 calibrated reviewers) | 2.79 | 3.07 | 3.00 |
| blind instruction-compliance | 4.36 | 4.21 | 4.50 |
| official GGUF / 8GB path | mature / **viable** | exists / unverified | — |

## Packet family (6 arms × 3 tasks)

Real per-model tokenizer counts in [`packet-token-profile.json`](packet-token-profile.json).
Ministral bands (scene): bare 120, compact 843, **realistic 2001 (in band)**, long 4848,
long_noisy 5133, long_salience_repaired 5167. **Limitation:** the long family under-fills the
8–12K target because the authored project's full genuine context is ~5K tokens and padding is
prohibited — the 8–12K long-context stress was NOT exercised.

**Causal reading (tagged as observation, not proven cause):** all three models produced
mechanically-valid prose across every packet arm (candidate arms 1.0; 4B long_salience_repaired
0.67) → at the tested scale (≤~5K tokens) these models do **not** collapse on compiled LineWright
packets, and the `long_noisy → long_salience_repaired` salience benefit is **not observable**
because the noisy arm did not fail. Supplementary deterministic checks show weak protected-line
preservation across all models (0.5–0.67) and lower anachronism rates for Ministral (0.06) than
Qwen (0.22) / 4B (0.28) — a fine-tune signal, not a base disqualifier.

## Decision

Branch **`run_one_bounded_confirmation`**, presumptive foundation **Qwen3-8B** — see
[`../../../training/reports/dispatch-26-foundation-decision.md`](../../../training/reports/dispatch-26-foundation-decision.md).
Raw outputs, reviewer packets, and the identity key are git-ignored (blind separation preserved).
