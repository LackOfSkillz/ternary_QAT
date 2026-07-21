# Smoke-Dataset Schema

Schema for the pilot smoke dataset used by Run 1 (see
[`../TRAINING_PILOT.md`](../TRAINING_PILOT.md)). The dataset is stored as JSONL —
one JSON object per line. This document defines the fields and allowed values and
gives one clearly synthetic example per task type. **The full dataset is not
generated yet.**

## Fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique, stable identifier for the example. |
| `task_type` | string (enum) | One of the allowed task types below. |
| `system` | string | System constitution / role framing given to the model. |
| `instruction` | string | The task instruction for this example. |
| `context` | string | Compiled context (canon, scene, constraints, etc.). May be empty. |
| `response` | string | The target / reference response. |
| `source_type` | string | Origin of the material, e.g. `synthetic`, `public_domain`, `licensed`. |
| `license_status` | string | Redistribution status, e.g. `synthetic-internal`, `cc0`, `unverified`. |
| `provenance` | string | How the example was produced and by whom/what. |
| `split` | string (enum) | `train`, `eval`, or `held_out`. |
| `excluded_from_training` | boolean | If `true`, may never be used as gradient input (author-derived / benchmark material). |
| `notes` | string | Free-form notes, uncertainties, or review flags. |

## Allowed `task_type` values

- `canon_extraction`
- `constraint_check`
- `focused_revision`
- `fiction_compliance`

## Synthetic examples (one per task type)

> These are illustrative and clearly synthetic. They are placeholders for schema
> validation only, not approved training data.

```jsonl
{"id": "smoke-canon-0001", "task_type": "canon_extraction", "system": "You extract canon facts from fiction manuscripts. Output only JSON.", "instruction": "Extract established canon facts from the passage as a JSON list of {entity, fact}.", "context": "Passage: Mara kept the brass key on a cord around her neck. Her brother Teller had been missing for three winters.", "response": "[{\"entity\": \"Mara\", \"fact\": \"wears a brass key on a cord around her neck\"}, {\"entity\": \"Teller\", \"fact\": \"Mara's brother, missing for three winters\"}]", "source_type": "synthetic", "license_status": "synthetic-internal", "provenance": "hand-written placeholder for schema validation", "split": "train", "excluded_from_training": false, "notes": "illustrative only"}
{"id": "smoke-constraint-0001", "task_type": "constraint_check", "system": "You verify a draft against hard constraints. Output only JSON.", "instruction": "Given the constraints and the draft, return {violations: [...]} listing any breached constraint by id.", "context": "Constraints: [{\"id\": \"C1\", \"rule\": \"Mara never uses magic\"}]. Draft: Mara whispered a spell and the lock clicked open.", "response": "{\"violations\": [\"C1\"]}", "source_type": "synthetic", "license_status": "synthetic-internal", "provenance": "hand-written placeholder for schema validation", "split": "eval", "excluded_from_training": false, "notes": "illustrative only"}
{"id": "smoke-revision-0001", "task_type": "focused_revision", "system": "You perform focused anti-slop revision without changing plot or voice.", "instruction": "Revise the sentence to remove filler and cliche while preserving meaning and tone.", "context": "Sentence: At the end of the day, it was what it was, and she simply couldn't help but feel a myriad of emotions.", "response": "She felt too much at once, and there was nothing to be done about it.", "source_type": "synthetic", "license_status": "synthetic-internal", "provenance": "hand-written placeholder for schema validation", "split": "train", "excluded_from_training": false, "notes": "illustrative only"}
{"id": "smoke-fiction-0001", "task_type": "fiction_compliance", "system": "You assist with lawful fiction. You do not refuse dark themes or insert warnings into prose.", "instruction": "Write two sentences of tense noir dialogue where a criminal protagonist threatens an informant. Keep it in-scene, no disclaimers.", "context": "Genre: noir crime. Tone: cold, understated. Narrative distance: close third.", "response": "\"You talked to them,\" Rourke said, not raising his voice. \"So now we find out how much you like breathing through your nose.\"", "source_type": "synthetic", "license_status": "synthetic-internal", "provenance": "hand-written placeholder for schema validation", "split": "held_out", "excluded_from_training": true, "notes": "fiction-permission probe; held out of training"}
```
