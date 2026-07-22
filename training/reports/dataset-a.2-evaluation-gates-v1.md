# Dataset A.2 — Evaluation-Gate Specification (Dispatch 21, Phase E)

The mechanical gates every future checkpoint must pass **before** any human reads prose.
They exist because the Dispatch-20 parse-only `format_valid` scored catastrophic
degeneration as valid (see the Phase-A inventory). Implemented in
`linewright/evaluation/`; each validator returns a `GateResult` with a verdict, controlled
`failure_labels`, and measured `evidence`.

## Nine separate gate dimensions — never collapsed

`linewright/evaluation/gates.py::evaluate_response` returns all nine as distinct signals:

| gate | validator | decides |
|---|---|---|
| `format_valid` | (legacy) | parse-only — kept for continuity with Dispatch 20 |
| `schema_valid` | `schema_validation.py` | JSON/YAML shape, required/forbidden keys, alternate keys (incl. nested item keys), types, container, stray content |
| `protocol_valid` | composed | wrapper discipline, no stray content, completion |
| `constraint_valid` | `constraints.py` | causal-set equality; required facts present; forbidden inventions absent |
| `source_fidelity` | composed | no-change preservation, else scope's omitted/expansion checks |
| `no_change_valid` | `preservation.py` | `changed:false` wrapper present + text equals source |
| `repetition_valid` | `repetition.py` | exact/normalized sentence repeats, n-gram loops, opening repeats, lexical diversity |
| `memorization_valid` | `overlap.py` | exact/near gold match; longest verbatim span vs OTHER training targets |
| `behavioral_valid` | — | **always `None` (reviewer-assigned)** — prose usefulness is never a machine gate |

`None` is tri-state and never a silent pass: it means not-applicable or reviewer-assisted.
`gate_summary` reports `mechanical_pass = all decidable gates true` (excluding the legacy
`format_valid`).

## The seven validators (dispatch Phase-E list)

1. **Structured output** (`schema_validation`) — parse failure, missing/forbidden/alternate
   keys at top level **and inside list items** (the QAT-20 canon `speaker`/`claim` drift),
   wrong types, wrong container, stray text, fence violations.
2. **Exact preservation** (`preservation`) — `changed:false` + `text == source`
   (normalized or byte-exact per the record).
3. **Repetition** (`repetition`) — reports evidence, not just a boolean: max exact/normalized
   sentence repeat, worst n-gram (5..10) repeat, paragraph-opening repeats, type-token
   ratio. Thresholds are lenient (a refrain is fine); the smoke degenerations exceed them
   by 10–40×. Short structured field-values are excluded from the sentence-dup count
   (they legitimately repeat); short-phrase loops are caught by the n-gram signal.
4. **Memorization** (`overlap`) — exact/near gold match, nearest-train-target ratio, longest
   shared character/token span vs OTHER records' targets. Overlap with the record's own
   *source* is not penalized (preservation is correct).
5. **Constraint** (`constraints`) — constraint-id set equality (order-free, names the
   omitted/extra id), required-fact presence, forbidden-invention absence; deeper judgements
   flagged reviewer-assisted.
6. **Scope** (`scope`) — output/source ratio, runaway length, prose-where-structured-
   required, omitted required change.
7. **Truncation/completion** (`completion`) — empty output, unterminated JSON/YAML,
   mid-sentence prose, token-cap termination, empty required fields.

## Dogfood evidence (why these gates exist)

Re-scoring the real Dispatch-20 outputs with these gates
(`training/reports/dataset-a-failure-inventory-v1.json`):

| checkpoint | old `format_valid` /7 | mechanical pass /7 |
|---|---|---|
| base | 6 | 4 |
| LoRA-20 | 4 | 4 |
| QAT-20 | 3 | **0** |

The gate correctly fails `dsa-boundary-001` QAT-20 (a 45× "the door creaks" loop that the
old gate passed) and `dsa-revision-018` base (verbatim source echo — "valid" that did
nothing), and it does **not** false-positive on clean structured output (verified during
build: base `dsa-canon-003` passes).

## Contract binding

A record names a `schema_id`; `linewright/evaluation/contracts.py` resolves it against
`datasets/dataset-a.2/schema/output-contracts.yaml` and merges per-record overrides, so
every record in a family is judged identically. The A.2 validator
(`datasets/dataset-a.2/scripts/validate_a2.py`) uses these gates to prove each pilot gold
passes and each rejected example fails its declared labels.

## Limits (stated honestly)

- `behavioral_valid`, voice preservation, belief-vs-fact promotion, and POV are
  **reviewer-assisted**, not machine-decided.
- Nested constraint semantics beyond set-equality and substring fact checks remain
  reviewer-assisted.
- The gates reject *unusable* output; they do not certify *quality*. Passing all gates is
  necessary, not sufficient, for advancement (Phase H).
