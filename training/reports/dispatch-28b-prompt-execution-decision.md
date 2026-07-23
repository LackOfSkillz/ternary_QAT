# Dispatch 28B — LineWright Prompt-Execution Pilot: Strategic Decision

**Status:** provisional pilot decision · **Final commercial ship certification:** NO
**Primary branch:** `model_capability_is_primary_bottleneck`
**Product thesis:** `partially_supported` (elicitation yes, contract structure no)
**Full 100-task multimodel benchmark:** AUTHORIZED · **Dataset A.3 expansion:** DEFERRED (model ceiling) · **Training/QAT:** none

Generated from frozen artifacts: `benchmarks/runs/linewright-prompt-execution-v1/mechanical-results.json`
(locked), `soft-review-summary.json`, `comprehension-execution-analysis.json`,
`generation-integrity.json`. The machine artifact is authoritative for effect sizes; the YAML
companion is the machine-readable form of what follows.

## The question

Can LineWright make a capable local model **more reliable** by translating author intent into a
structured writing contract — improving completion, unchanged-return resistance, protected-text
preservation, scope discipline, canon/voice/shape compliance — **without** over-editing, corruption,
invention, drift, rigidity, or new critical failures?

Four information-controlled arms on Qwen3-8B (non-thinking, greedy, seed 20260723, 100 outputs,
generation integrity **valid** — 0 missing/duplicate/hash-mismatch/token-cap/reasoning-trace/failure):
**P0-Realistic** (casual), **P0-Maximal** (exhaustive NL, every requirement), **P1-Contract** (the
same information, structured), **P3-Ideal** (hand-built ceiling on 10 tasks; P3-Compiled deferred —
no real compiler in this repo).

## Mechanical evidence (primary: clean_execution)

| arm | n | clean_exec | all_required | invalid_unchanged | protected_acc | unauth_edit | no_change_acc | critical |
|---|---|---|---|---|---|---|---|---|
| P0-Realistic | 30 | 0.400 | 0.346 | 0.150 | 0.889 | 0.05 | 0.75 | 7 |
| P0-Maximal | 30 | **0.633** | 0.615 | 0.000 | 1.000 | 0.00 | 1.00 | 1 |
| P1-Contract | 30 | 0.567 | 0.615 | 0.000 | 0.963 | 0.05 | 1.00 | 2 |
| P3-Ideal | 10 | 0.600 | 0.556 | 0.000 | 1.000 | 0.00 | 1.00 | 0 |

Focused revision (headline family) — all-required completed / mean changes completed:
P0-Realistic 0.083 / 1.00 · P0-Maximal 0.25 / 2.25 · P1-Contract 0.25 / 2.08 · P3-Ideal 0.00 / 1.25.

Precommitted comparisons (clean_execution): **P1 − P0-Maximal = −0.066** (structure alone),
**P1 − P0-Realistic = +0.167** (elicitation+structure), **P3-Ideal − P1 = 0.000** (richer packet).
**All three precommitted floors FAIL** (structure_success, practical_product_success,
ideal_packet_signal).

## Blind review (arm-hidden; both reviewers caught 4/4 broken calibration controls, 0 false
positives; prose-quality agreement 0.30 mean abs diff)

Paired soft anti-results: **P1 vs P0-Maximal** prose +0.03 / voice +0.04 / rigidity +0.05 /
over-editing −0.07 (all within noise — structure is prose-neutral). **P3-Ideal vs P1** (same 10
tasks) prose −0.16 / voice −0.15 / **rigidity −0.30** / over-editing −0.20 — the richer packet is
softly worse and more rigid (a soft anti-result).

## Comprehension vs execution (6 probes)

**6/6 comprehension pass, 4/6 execution fail (all `pass_fail`; 0 `fail_fail`).** The model correctly
enumerates the required changes, protected elements, forbidden operations, and output format for
every probe — then fails to execute four of them. The failure is **execution discipline, not
comprehension**.

## Decision

**Primary — `model_capability_is_primary_bottleneck`.** On the headline multi-constraint
focused-revision failure every structured arm plateaus (all-required ≤ 0.25) even though the model
comprehends the contracts perfectly. No prompt representation — exhaustive natural language, a
structured contract, or a hand-built ideal packet — cracks the ceiling; contract structure is a
mechanical *and* soft wash, and the richer packet regresses. The residual is an execution-discipline
ceiling bound by model capability, not a comprehension/representation gap that a better prompt could
close.

**Secondary findings.**
1. **Requirement elicitation — not contract structure — is the real cross-family lever.**
   P0-Realistic → P0-Maximal lifts clean execution 0.40 → 0.63, focused-revision mean changes
   1.0 → 2.25, canon clean 0.0 → 1.0, no-change accuracy 0.75 → 1.0. This is achievable in plain
   prose and does not require the LineWright contract format.
2. **Contract structure adds no reliability and mildly hurts scope** (P1 − P0-Maximal clean −0.066;
   P1 introduces 1 protected corruption + 2 forbidden violations and drops canon clean 1.0 → 0.667;
   prose-neutral softly).
3. **The richer ideal packet is a net negative** — under-executes focused revision (mean 1.25) and
   is softly worse/more rigid on the same tasks (rigidity −0.30). Richer compiled context did not
   help; it hurt.
4. **The comprehension/execution split is a trainable signal** — comprehension is saturated while
   execution fails. If a stronger model still shows the gap, the lever is training a reliable packet
   **executor**, not prompt engineering (`shift_training_to_packet_executor`, conditional).

## Product-thesis classification: `partially_supported`

The thesis as stated — that LineWright **contract structure** makes the model more reliable — is
**not supported**: all floors fail, P1 does not beat equal-information natural language mechanically
or softly, and the ideal packet regresses. The weaker claim that **clear requirement specification
helps** *is* supported — but that is requirement elicitation, achievable in plain prose, and the
headline focused-revision failure is capability-bound.

## Gates

- **Full 100-task multimodel benchmark: AUTHORIZED.** Run this instrument across the existing 4B +
  Qwen3-8B + a stronger capability reference to test whether the focused-revision execution ceiling
  is model-specific (capability) or universal (representation). This resolves the primary question
  before any build investment.
- **Dataset A.3 expansion: DEFERRED (model ceiling).** Not authorized; composition status
  `deferred_due_to_model_ceiling`. Weight-training the 8B is not indicated while the ceiling is
  unexplained.
- **Training / QAT: none.** Hold. The comprehension/execution split hints a packet-executor LoRA
  could help, but only after the multimodel benchmark shows the ceiling is model-specific and the
  failure is trainable without collapsing prose.
- **Real product compiler test: not required now (lower priority).** The hand-built ideal ceiling
  regressed, so richer compiled context is unlikely to fix focused revision on this model; revisit
  only if a more capable model shows the ceiling is representation-bound.

## Honest limitations

Soft review is model-only — two blind LM sub-agents, human review waived for the pilot and recorded
as such (`evidence_status: model_review_only`, `independently_human_confirmed: false`). Blind-review
units were selected by criteria (all P3-Ideal + paired P1, all critical/invalid/over-edit cases, plus
a balanced fill), so cross-arm soft means are confounded by selection — only the paired P3-vs-P1 and
P1-vs-P0-Maximal deltas are clean. Single model, single seed, 30 tasks; the structured-output family
is genuinely hard (the model invents its own JSON keys and collapses lists) but is only 1–3 tasks.
Nothing here is a commercial ship certification.

## Next step

Run the 100-task multimodel benchmark on this frozen instrument to resolve capability vs
representation before investing in a contract compiler, Dataset A.3 expansion, or any training.
