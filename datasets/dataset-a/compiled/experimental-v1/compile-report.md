# Dataset A compile report — experimental-v1

- freeze_id: `dataset-a-experimental-v1`
- system prompt: `prompts/linewright-training-system-v1.txt`  sha256 `038d9ab8aac2aee9…`
- train rows: **28**  (train.jsonl sha256 `97778f2a334649c8…`)
- evaluation rows: **7**  (evaluation.jsonl sha256 `0f3ae4263c5a175b…`)
- preference-train rows: **18**  (preference-train.jsonl sha256 `72a455ba67c853bd…`)
- manifest.json sha256 `9d067c3242366647…`

## Approx token lengths (char/4 heuristic, whole example incl. system)

- system-prompt tokens (approx): 522
- min / median / max example: 656 / 727 / 1220
- total approx tokens (train): 23716

## Task distribution by split

- train: {'fiction_boundary': 1, 'canon_extraction': 4, 'constraint_check': 4, 'focused_revision': 17, 'scene_contract': 2}
- evaluation: {'fiction_boundary': 1, 'canon_extraction': 1, 'constraint_check': 1, 'focused_revision': 3, 'scene_contract': 1}

## Discipline

- Only `approved` train/evaluation records compiled; draft/unreviewed skipped.
- Rejected responses are NOT SFT targets (separate preference-train.jsonl only).
- Evaluation rows are held out (excluded_from_training: true on-record).
- No reviewer notes / rejection reasons / evaluation text leak into targets.
- Deterministic: sorted by id, sort_keys JSON, LF newlines.
