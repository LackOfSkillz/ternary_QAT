# LineWright Prompt-Execution v1 (Dispatch 28A)

A frozen, machine-checkable pilot instrument that tests LineWright's product thesis:

> Can a structured LineWright-style writing contract make a small local model execute
> fiction-writing instructions **more reliably** than strong natural-language prompting —
> without degrading manuscript quality?

This directory is **construction + freeze only** (Dispatch 28A). It contains **no model outputs,
no scoring, no review, and no decision.** Generation is deferred to a later, separately-authorized
dispatch. It is a distinct, more rigorous instrument from the Dispatch-28 `linewright-prompt-effect-v1`
pilot (which was built and executed end-to-end); that pilot is preserved unchanged as provisional
evidence-of-record.

## What is here

| Path | Contents |
|---|---|
| `schemas/task-manifest.schema.json` | formal task schema (Draft-07) |
| `validators/checks.py` | deterministic, typed check evaluator — the single source of truth for check semantics; **no LLM grader is used for primary correctness** |
| `validators/validate_tasks.py` | task-layer validator + reports + dataset/Dispatch-28 overlap scan |
| `validators/validate_equivalence.py` | P0-Maximal ≡ P1-Contract information-equivalence validator |
| `build_tasks.py` | authors the 30 fresh tasks; emits `task-manifest.jsonl/.yaml` + `tasks/<family>/` |
| `render_prompts.py` | renders the prompt arms; emits `prompts/<arm>/`, `prompt-arm-manifest.json`, `prompt-plan.json`, `p3-ideal-subset.json` |
| `freeze_tasks.py` / `freeze_prompts.py` | hash + freeze each layer |
| `freeze/`, `reports/` | freeze records and validation reports |

## Task design

30 tasks, frozen distribution: 12 multi-constraint focused revision · 5 protected-text revision ·
4 no-change judgment · 3 canon continuation · 3 voice-preserving revision · 2 constraint-bound
scene · 1 structured protocol. The 12 focused-revision tasks carry instruction positions **4 early /
4 middle / 4 late** with the critical-instruction type rotated across required-correction,
protected-text-rule, unauthorized-rewrite-prohibition, and output-shape-requirement.

Every required change, protected element, and unaffected span keys on an **exact substring** so
correctness is machine-decidable. All content is **original to this instrument** — validated to
have zero overlap with Dataset A/A.2/A.3 or the Dispatch-28 benchmark.

## Leakage separation (critical for a future P3-Compiled arm)

Each task splits its fields into:

- `compiler_inputs` — the **only** block a future LineWright application compiler may receive.
- `evaluation_ground_truth` + `machine_checks` — held out of `compiler_inputs` by construction and
  asserted so by the validator, so a later compiled arm cannot see the answers.

## Prompt arms

`P0-Realistic` (how an author naturally asks, may omit requirements) · `P0-Maximal` (exhaustive
natural language, all requirements, unstructured) · `P1-Contract` (the same information as
P0-Maximal in a canonical research-contract format) · `P3-Ideal` (a hand-built theoretical ceiling
on a frozen 10-task subset; **not** product-generated). **P3-Compiled is deferred** — the real
compiler lives in the application project, not this research repository; no re-implementation or
hand simulation is permitted.

Expected future generation: 30 × 3 main arms (90) + 10 × P3-Ideal = **100 outputs**. Not generated
in this dispatch.
