# Dataset A — Methods Comparison Instrument

Dataset A is a **narrow, fiction-only research instrument**, not a shipping
dataset. It drives the matched conventional-LoRA vs ternary-QAT comparison and
tests whether a small model can follow fiction-craft instructions **without
collapsing every passage into one house style**. Full rationale:
[`../../ROADMAP.md`](../../ROADMAP.md) and [`specification.md`](specification.md).

## What it must demonstrate

1. A strong, concentrated behavioral delta at BF16.
2. Whether ternary QAT preserves more of that behavior through the actual Prism
   Q2_0 deployment grid.
3. Fiction-craft instruction-following without style collapse.

## Layout

```text
datasets/dataset-a/
  README.md            # this file
  specification.md     # anti-slop doctrine, precedence, principles
  schema/              # record-schema.yaml + enums.yaml (the contract)
  profiles/            # 5 generic starter craft profiles (v1)
  docs/                # craft-taxonomy-reference.md
  drafts/              # human-readable source records, by family (NOT training data)
    canon/ constraints/ revision/ scene-contract/ fiction-boundary/
  approved/            # records that passed review (never unreviewed data)
  rejected/            # records rejected in review
  compiled/            # JSONL compiled ONLY after freeze
  reviews/             # one review file per reviewed record
  scripts/             # validate_dataset_a.py
```

## Record format

One **Markdown** file per record: YAML front matter (machine-readable) + human
sections (`Instruction`, `Context`, `Gold Response`, and, per family,
`Protected Elements` / `Rejected Response` / `Rejection Reasons`, plus
`Evaluation`, `Reviewer Notes`). Fields and required-by-family rules are in
[`schema/record-schema.yaml`](schema/record-schema.yaml); controlled values in
[`schema/enums.yaml`](schema/enums.yaml).

## Workflow

`draft → mechanically_validated → substantive review → Gary review (where
required) → approved → frozen → compiled`. **No script promotes a record.**
Compilation to JSONL happens only after freeze. Every record carries provenance
and licensing; **no generated record automatically enters training.**

## Validate

```bash
python datasets/dataset-a/scripts/validate_dataset_a.py --root datasets/dataset-a
```

Checks IDs, required fields/sections by family, enum validity, draft-vs-approved
placement, duplicate (template_family, semantic_cluster) pairs, duplicate source
context / gold response, provenance/exclusion fields, and prints counts by family.

## Governing + anti-collapse principles

> Teach a specific fiction-writing operation, preserve everything the author did
> not authorize the model to change, and produce an output that can be evaluated.

> Anti-slop training must remove genericness, redundancy, unearned explanation,
> and unauthorized rewriting without imposing a universal house style.

## Current state (seed batch)

- **25 draft records** live under `drafts/` (5 canon, 5 constraint, 10 revision,
  3 scene-contract, 2 boundary). All are `review_status: draft`, `split:
  unassigned`, and **ready for inspection only — not approved**.
- `approved/`, `rejected/`, `compiled/` are empty (placeholder `.gitkeep`).

## Provenance discipline

Provenance records **origin**; review status records **adjudication**. All 25 seed
records are **`origin: model_authored`** by `claude-opus-4-8` (teacher terms
`pending_review`, `excluded_from_training: true`). Human review never converts
model-authored content into human-authored provenance. See
`reviews/dispatch-12-correction.md`.

## Open questions (for Gary)

- Authoritative Craft Taxonomy is installed at
  [`docs/linewright-craft-taxonomy.md`](docs/linewright-craft-taxonomy.md);
  `docs/craft-taxonomy-reference.md` is now a non-authoritative working subset.
- The 360-record target distribution is **provisional** pending compiled-packet
  feasibility results.
- **Teacher-output licensing is unresolved.** All 25 records stay
  `excluded_from_training: true` until a licensing memo clears the commercial
  teacher-output case.
