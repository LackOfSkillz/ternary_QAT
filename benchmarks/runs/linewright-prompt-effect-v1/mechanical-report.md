# LineWright Prompt-Effect v1 — Mechanical Results (primary)

100 outputs (30 P0-Realistic + 30 P0-Maximal + 30 P1-Contract + 10 P3-Ideal), Qwen3-8B
non-thinking greedy, identical per-task output cap. Zero reasoning traces, zero token-cap hits.
Rules are the frozen deterministic ground-truth checks. Machine-readable: `mechanical-results.json`.

## All-required-changes-completed rate (headline)

| arm | overall | focused-revision (12) | returned-unchanged (rev) | mean completion (rev) | protected acc | unauthorized | clean success |
|---|---|---|---|---|---|---|---|
| P0-Realistic | 0.433 | **0.083** | 0.167 | 0.403 | 0.913 | 0.067 | 0.400 |
| P0-Maximal | 0.700 | **0.667** | 0.083 | 0.792 | 1.00 | 0.033 | 0.700 |
| P1-Contract | 0.633 | **0.500** | **0.000** | 0.792 | 1.00 | **0.000** | 0.633 |
| P3-Ideal (10) | 0.900 | 0.750 | 0.000 | 0.917 | 0.75 | 0.200 | 0.700 |

## Headline effects (over shared tasks)

- **P1 − P0-Maximal (structure alone): −0.067** all-required. Structure with identical information
  does NOT raise raw completion. **But** P1 is the cleanest arm: 0 returned-unchanged, 0 unauthorized
  edits, 0 protected corruption. Structure's value is **scope discipline**, not completion.
- **P1 − P0-Realistic (practical): +0.20** all-required. The casual under-specified prompt (0.433) is
  massively lifted by spelling out the requirements. On the focused-revision family the gap is
  0.083 → 0.500 (+0.417). The dominant lever is **requirement elicitation**.
- **P3-Ideal − P1: +0.30** all-required — the hand-built packet adds real value **but** brings
  anti-results (2 protected corruptions, 2 unauthorized edits): more compliance at the cost of scope.
- **P3-Ideal − P0-Realistic: +0.50** — the full practical LineWright effect vs a casual prompt.

## Instruction position (focused-revision, all-required-completed)

| arm | early | middle | late |
|---|---|---|---|
| P0-Realistic | 0.00 | 0.00 | 0.25 |
| P0-Maximal | 0.50 | 1.00 | 0.50 |
| P1-Contract | 0.25 | 0.75 | 0.50 |
| P3-Ideal | — | 0.67 | 1.00 |

Both P0-Maximal and P1 remain position-sensitive; **structure does not clearly reduce position
sensitivity** (H6 mixed). P0-Realistic is weak everywhere (it never learns the specific defects).

## Anti-results (over-compliance)

P1-Contract has the **fewest** anti-results (0/0). P3-Ideal has the **most** (protected corruption 2,
unauthorized 2) — its aggressive completeness increases over-editing. This is the H7 warning: greater
diligence must be paired with authority/scope control, or the packet over-edits.

## Versus Dispatch 27 LoRA

The neutral LoRA produced 0.0 gain on this exact focused-revision failure. Prompt architecture
(elicitation + structure) lifts all-required-completed on focused revision from 0.083 to 0.50–0.75
and drives returned-unchanged to 0.0 — a **far larger, real behavioural gain than weight tuning
achieved.** This supports shifting near-term effort to the prompt engine (H8).
