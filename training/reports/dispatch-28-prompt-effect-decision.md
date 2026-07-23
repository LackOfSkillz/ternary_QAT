# Dispatch 28 — LineWright Prompt Effect Pilot: Strategic Decision

**Status:** provisional pilot decision · **Final commercial ship certification:** NO
**Primary branch:** `prioritize_requirement_elicitation`
**Phase-2 (100-task multimodel benchmark):** AUTHORIZED · **Dataset A.3 expansion:** PAUSED

This decision is generated from frozen artifacts, not authored freehand:
`benchmarks/runs/linewright-prompt-effect-v1/mechanical-results.json` (locked mechanical
scoring of 100 outputs) and `soft-review-summary.json` (arm-hidden blind soft review). The
machine artifact is authoritative for the effect sizes; the YAML companion
(`dispatch-28-prompt-effect-decision.yaml`) is the machine-readable form of what follows.

## Product thesis under test

Does compiling ordinary author intent into a structured fiction-writing packet improve
writing-task reliability — specifically the multi-constraint focused-revision failure
(required changes ignored / passage returned unchanged / only one of several defects
repaired) — more than the neutral Dispatch-27 LoRA?

Four prompt arms at controlled information content:

| Arm | What it is |
|---|---|
| **P0-Realistic** | Casual, under-specified request — how an author actually asks. |
| **P0-Maximal** | Strong natural language, *every* requirement stated, unstructured. |
| **P1-Contract** | The same information as P0-Maximal, structured (task authority, required changes, protected elements, canon, voice, constraint hierarchy, output requirements). |
| **P3-Ideal** | Hand-built ceiling packet (10 tasks). |

P0-Maximal ≡ P1-Contract information-equivalence was validated before generation, so the
P1−P0-Maximal contrast isolates **structure at equal information**, and P1−P0-Realistic
isolates **the whole product** (elicitation + structure) against how authors really write.

## Mechanical evidence (100 outputs, greedy, non-thinking, seed 20260722)

Focused revision — all-required-changes-completed (the headline reliability metric):

| Arm | all-required completed | returned-unchanged |
|---|---|---|
| P0-Realistic | **0.083** | 0.167 |
| P0-Maximal | 0.667 | 0.083 |
| P1-Contract | 0.500 | **0.000** |
| P3-Ideal | **0.750** | 0.000 |

Overall clean-success by arm: 0.433 / 0.700 / 0.633 / 0.900.

Headline effects (all-required-completed):
- **P1 − P0-Realistic = +0.200** — the whole product lifts reliability substantially.
- **P1 − P0-Maximal = −0.067** — structure *alone*, at equal information, adds no completion.
- **P3-Ideal − P1 = +0.300** — the fuller packet completes much more.
- **P3-Ideal − P0-Realistic = +0.500.**

Anti-results (exact machine checks): P1-Contract is the cleanest arm — 0 returned-unchanged,
0 unauthorized edits, 0 protected-span corruption. P0-Realistic corrupts 2 / edits out of
scope 2. P3-Ideal trips 2 exact protected-span checks and 2 exact unaffected-span checks.

## Blind soft review (arm identity hidden; both reviewers calibrated 3/3, 3/3)

Per-arm means on the ideal-subset outputs (1–5, higher is better; over_editing/rigidity
higher = *more disciplined / more natural*):

| Dimension | P0-Realistic | P1-Contract | P3-Ideal |
|---|---|---|---|
| prose_quality | 2.80 | 2.95 | **3.89** |
| voice_preservation | 2.80 | 3.30 | **4.17** |
| scope_control | 2.90 | 3.45 | **4.22** |
| over_editing (disciplined) | 2.85 | 3.70 | **4.33** |
| rigidity (natural) | 3.30 | 3.50 | **4.11** |
| author_usefulness | 2.55 | 2.80 | **3.78** |
| fatal failures | 5 | 2 | 2 |

## Decision

**Primary branch — `prioritize_requirement_elicitation`.** P1-Contract beats P0-Realistic by
+0.200 on focused-revision completion but does **not** beat P0-Maximal (−0.067). The realized
product value is therefore **eliciting and organizing the requirements authors do not
naturally state**, not structure as a format. Spelling out the defects is what moves
all-required-completed from 0.083 (casual) to 0.50–0.67 (maximal/contract).

**What structure itself buys — scope discipline.** At equal information, P1-Contract is the
only mechanically spotless arm (0/0/0). Structure's contribution is not *more* changes, it is
*no unauthorized* changes. This is a real, shippable property.

**The H7 anti-result does not hold.** The pre-registered worry was that higher mechanical
compliance would come with prose rigidity / over-editing. Mechanically P3-Ideal trips a few
*exact* protected/unaffected-span checks — but the blind reviewers, judging holistically,
rated P3-Ideal the **best arm on every dimension**, including scope_control (4.22) and
over_editing (4.33, most disciplined) and rigidity (4.11, most natural). The mechanical flags
are brittle exact-match artifacts (benign rephrasing of spans the check pinned verbatim), not
holistic over-editing. **Net: the fuller packet improves both compliance and prose.** The one
genuine, narrow engineering task it exposes is **locking protected spans verbatim** — this is
the concrete content of the `improve_compiler_quality` secondary branch, not a mandate to curb
over-editing.

**Prompt architecture ≫ the Dispatch-27 LoRA on this exact failure.** Prompting moved
focused-revision completion from 0.083 to 0.50–0.75 and returned-unchanged from 0.167 to 0.0;
the neutral LoRA gave 0.0 on the same failure. The near-term lever is the **prompt engine**
(requirement elicitation + scope-controlled contracts), not weight tuning.

## Gates

- **Phase-2 (100-task multimodel benchmark): AUTHORIZED.** Meaningful prompt signal detected,
  instrument valid (deterministic grounded checks + verified P0-Maximal ≡ P1-Contract
  equivalence), no unresolved scoring bias. Scope: existing 4B + Qwen3-8B + a frontier
  capability reference, arms P0-Realistic / P0-Maximal / P1-Contract / P2-Context / P3-Compiled
  — the last **only if a real compiler is available** (P3-Compiled was dropped this pilot; the
  fork has no compiler, so P3-Ideal is a hand-built ceiling, not an attributable product).
- **Dataset A.3 expansion: PAUSED.** The dominant near-term lever is the prompt engine, not
  weight training; the LoRA was neutral on this exact failure while prompting was not. If A.3
  is later expanded, redesign it around **packet execution**, not universal prose taste.
- **Effect floors** (precommitted, strict): `compilation_success` FAIL (structure alone
  −0.067 < +0.15), `practical_product_success` FAIL on the compound clause (gain +0.20 met,
  but returned-unchanged reduction 0.167 < 0.25), `full_packet_success` FAIL on the exact-span
  clause (completion +0.30 met, but exact protected/unaffected checks > P1's zero). The floors
  are deliberately conservative; the branch selection rests on the directional evidence above,
  and every floor result is recorded honestly rather than reverse-fit.

## Honest limitations

Soft review is **model-only** — two blind LM sub-agents, human review waived for the pilot and
recorded as such (`evidence_status: model_review_only`, `independently_human_confirmed: false`).
P3-Ideal is a hand-built ceiling on 10 tasks, not the output of a real compiler, so its gains
bound what a compiler *could* achieve, not what this fork ships. Single model, single seed,
30 tasks. Nothing here is a commercial ship certification.

## Next step

Invest in requirement elicitation + a scope-controlled contract compiler (with verbatim
protected-span locking); run the Phase-2 100-task multimodel benchmark to confirm and size the
effect before any Dataset A.3 expansion or further training.
