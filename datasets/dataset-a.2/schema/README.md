# Dataset A.2 — schema (Dispatch 21, Phase C)

Dataset A.2 is the failure-driven successor to Dataset A. It is **JSONL-native** (one
record per line) and carries everything needed for training, static validation, split
isolation, and behavioral evaluation. It builds on — does not replace — the Dataset A
Markdown record schema and its `failure_label` / `profiles` enums.

## Files

| file | purpose |
|---|---|
| `record-schema.json` | JSON-Schema (draft-07) for one A.2 record |
| `output-contracts.yaml` | registry mapping `schema_id` → machine-checkable output contract |
| `behavior-tags.yaml` | the behaviors a record can teach + pilot-priority behaviors |

The output contracts are consumed by the Phase-E validators via
`linewright/evaluation/contracts.py` (`resolve`, `spec_from_record`). A record names a
`schema_id`; the gate for its whole family comes from the registry, so every record in a
family is judged identically unless it deliberately overrides a field.

## What A.2 adds over Dataset A

- **JSONL records** with `preferred_response` + explicit `rejected_responses` (each
  carrying the `failure_labels` it demonstrates and an explanation).
- **Explicit split grouping** — `split_restrictions.group_key` plus `source_family` and
  `story_world` — automated by `scripts/validate_a2.py` so no source cluster crosses
  train↔evaluation (Phase D policy).
- **Machine-checkable output contracts** with a stable `schema_id`, resolving the
  Dataset A scene-contract field ambiguity (A.2 commits to the instruction's field names).
- **Per-record `validation_expectations`** (changed flag, expected facts, forbidden
  inventions, constraint ids) that the constraint / preservation validators consume.
- **Content self-check**: the validator runs each `preferred_response` through the gates
  (it must pass) and each `rejected_response` through the gates (it must fail its declared
  labels), so golds are provably clean and rejected examples are provably bad.

## Validation

```
python -m validate_a2 --pilot-dir datasets/dataset-a.2/pilot
```

(run from `datasets/dataset-a.2/scripts/`, or `python datasets/dataset-a.2/scripts/validate_a2.py --pilot-dir ...`).

## Not production

Dataset A.2 is experimental. `review_status` fields (`static_validated`,
`aedan_approved`, `claude_approved`, `chatgpt_approved`) gate advancement; none of this is
production approval, and no training may start until the Phase-J readiness gate is met.
