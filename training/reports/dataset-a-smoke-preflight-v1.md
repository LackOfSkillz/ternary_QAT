# Dataset A smoke-training preflight v1

Pre-training baseline for the first LoRA + ternary-QAT smoke test on the
`dataset-a-experimental-v1` freeze. **This run tests pipeline viability, not
production quality.** No training was run to produce this report.

## Corpus and split

- approved / frozen records: **35** (freeze_id `dataset-a-experimental-v1`)
- train: **28** · evaluation: **7** · (no validation split for the first run)
- all records `review_status: approved`, `experimental_use_only: true`,
  `production_approved: false`

## Task distribution by split

| task_type | train | evaluation |
|---|---|---|
| canon_extraction | 4 | 1 |
| constraint_check | 4 | 1 |
| focused_revision | 17 | 3 |
| scene_contract | 2 | 1 |
| fiction_boundary | 1 | 1 |
| **total** | **28** | **7** |

## Style-profile distribution by split

| profile | train | evaluation |
|---|---|---|
| none | 11 | 4 |
| dark-speculative-v1 | 3 | 1 |
| romantic-emotional-v1 | 3 | 1 |
| suspense-mystery-v1 | 4 | 0 |
| lyrical-mythic-v1 | 3 | 1 |
| contemporary-commercial-v1 | 4 | 0 |

Evaluation spans 4 distinct profiles (dark-speculative, romantic-emotional,
lyrical-mythic, none), meeting the ≥3-profile requirement.

## Invention-budget distribution (focused_revision rows)

| level | train | evaluation |
|---|---|---|
| none | 7 | 2 |
| bounded | 10 | 1 |
| open | 0 | 0 |
| n/a (non-revision) | 11 | 4 |

## Special-record placement

- **no-change restraint:** `dsa-revision-002` → **evaluation** (tests no-change
  generalization); `dsa-revision-019` → **train** (learns the lesson). Both are
  structured `changed:false` with `text == source`.
- **author-voice override:** `dsa-revision-020` → **train** (the precedence lesson
  is trained, not only tested).
- **safety boundary:** `dsa-boundary-002` (actionable-harm decline) → **train**;
  `dsa-boundary-001` (in-scene depiction) → **evaluation**. Not every safety record
  is in evaluation.

## Leakage-group decisions

All related-record groups are placed **entirely in train** so no evaluation record
is a near-duplicate of a training example:

- lexical_substitution_pair: 011, 012 → train
- body_reaction_pair: 013, 014 → train
- delivery_tag_pair: 015, 016 → train
- restraint_override_paired_lesson: 019, 020 → train
- generic_atmosphere_matched_pair: revision-004, revision-005 → train

## Compiled artifacts

| file | bytes | sha256 (16) |
|---|---|---|
| train.jsonl | 108,809 | 97778f2a334649c8 |
| evaluation.jsonl | 28,327 | 0f3ae4263c5a175b |
| preference-train.jsonl | 61,603 | (see manifest) |
| manifest.json | 7,701 | 9d067c3242366647 |
| system prompt | — | 038d9ab8aac2aee9 |

`preference-train.jsonl` (18 rows) is a **separate** preference artifact from the
records that carry a rejected response; it is NOT mixed into SFT.

## Token estimates (deterministic char/4 heuristic, whole example incl. system)

| | min | median | max | total |
|---|---|---|---|---|
| train (28) | 656 | 724 | 1220 | 23,716 |
| evaluation (7) | 697 | 906 | 1116 | 6,218 |

- system-prompt tokens (approx): **522**
- longest example (~1220 tokens) is comfortably below `max_sequence_length: 2048`,
  so no truncation is expected.

## Projected optimizer steps

- effective batch size 8 (micro 1 × grad-accum 8); 28 train rows ⇒ ~4 steps/epoch.
- `max_steps: 20` ⇒ ~5 epochs. Overfitting is expected and irrelevant — this is a
  pipeline smoke test. Checkpoints at steps 10 and 20; eval before (step 0), at 10,
  and after.

## LoRA config summary

base `prism-ml/Ternary-Bonsai-4B-unpacked`; rank 16 / alpha 32 / dropout 0.05;
targets q,k,v,o,gate,up,down; lr 2e-4; bf16; adamw_torch/cosine; completion-only
loss; no packing; seed 20260721.
(`training/configs/dataset-a-lora-smoke-v1.yaml`)

## Ternary-QAT config summary

Identical base / train / eval / seed / sequence length / effective batch size /
eval prompts. Differences only: lr 4e-3 (~20×), and the `ternary_qat` block
(STE, swap_linear via `ternary/`, group_size 128, half-even rounding, fp16 scale,
embed_tokens/lm_head kept full precision, base checkpoint preserved).
(`training/configs/dataset-a-ternary-qat-smoke-v1.yaml`)

## Known limitations of a 35-record experiment

- Far too small to show meaningful quality change; **success = the pipeline runs
  end to end** (load → train → save → reload → evaluate) for both methods.
- 5-epoch overfit on 28 examples; eval scores are diagnostic, not indicative.
- Behavioral checks are rubric/deterministic graders, not a production benchmark.
- Serving-stack determinism is not guaranteed bit-exact (recorded in the harness).

## Confirmation

This run tests **pipeline viability, not production quality.** It is authorized as
an experimental rehearsal only; no production training, release, or quality claim
follows from it.
