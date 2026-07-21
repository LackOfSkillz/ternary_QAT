# Dataset A — Specification

Dataset A is a **methods-comparison instrument**, not a shipping corpus. It exists
to drive the matched conventional-LoRA vs ternary-QAT comparison and to test
fiction-craft instruction-following without style collapse. See
[`../../ROADMAP.md`](../../ROADMAP.md) for its place in the track.

## Governing principle

> Teach a specific fiction-writing operation, preserve everything the author did
> not authorize the model to change, and produce an output that can be evaluated.

Every record isolates **one** operation, declares what is protected, and provides
an output whose correctness can be checked (deterministically where possible).

## Anti-slop doctrine (strict)

Anti-slop removes **genericness, redundancy, unearned explanation, and
unauthorized rewriting** — while preserving the author's intended voice and craft
constitution. Dataset A must teach both what to do and the tempting-but-damaging
behavior to avoid.

**Anti-slop is not minimalism.** Dataset A must NOT teach any universal rule such
as: adjectives are bad · adverbs are bad · metaphors are bad · fragments are good
· short sentences are always stronger · named emotion is always weak · exposition
is always wrong · em dashes are forbidden · ornate prose is inherently
overwritten · dialogue must always remain indirect.

The correct standard is **contextual**:

> Remove habits that are generic, redundant, unearned, or unauthorized in this
> passage while preserving the author's intended voice and craft constitution.

To enforce this, Dataset A deliberately includes counter-cases: intentional
named-emotion, intentional repetition, and ornate/metaphor-rich passages that must
**remain** ornate. A revision that "cleans up" these into a flatter house style is
a **failure**, labeled (e.g.) `imposed_minimalism`, `voice_flattening`, or
`converted_voice_to_house_style`.

### Required content of every focused-revision record

- the primary requested operation (one issue)
- authorized changes
- protected elements
- unauthorized changes
- a **preferred minimal correction** (the gold response)
- checkable evaluation criteria
- at least one tempting failure mode (usually shown as the rejected response),
  and where useful a plausible **overcorrected** response with a precise
  explanation of why it fails

## Style diversity and anti-SIREP collapse

**SIREP is Gary's personal craft constitution. It must never become the model's
universal house style.** Dataset A conditions examples across five broad, editable
starter craft profiles (see [`profiles/`](profiles/)): Dark Speculative,
Romantic and Emotional, Suspense and Mystery, Lyrical and Mythic, Contemporary
Commercial. The same defect must be shown to require **different** repairs under
different profiles (see the style-matched concept pair in the seed batch).

### Precedence when guidance conflicts (highest first)

1. Hard canon and scene constraints
2. Author's established craft constitution
3. Project-specific genre profile
4. Generic starter craft profile
5. Model defaults

A generic starter profile must **never** override an established author voice.

## Craft Taxonomy usage

Labels and evaluation draw on the LineWright Craft Taxonomy's three-tier
distinction — Tier A measurable, Tier B estimable (with review uncertainty), Tier
C structural (declared constraints only). Dataset A does **not** try to train the
whole taxonomy. See [`docs/craft-taxonomy-reference.md`](docs/craft-taxonomy-reference.md).
Tier B labels must be treated as estimates, and Tier C techniques must appear only
as declared author/scene-contract constraints — never as candidate-vote-learned
preferences.

## Section semantics by task family

The `## Context` section means different things per family (enforced meaning in
`schema/record-schema.yaml → context_semantics`):

- **canon_extraction** — the source passage / supplied evidence.
- **constraint_check** — the declared constraints/canon plus the passage checked.
- **focused_revision** — the prose to revise.
- **scene_contract** — the writer's scene request and available project constraints.
- **fiction_boundary** — only the framing needed to classify the task. The
  meta-rationale lives in a required `## Classification Rationale` section, not in
  Context.

### Scene-contract output fields

A scene-contract `## Gold Response` is a structured contract with these fields.
Viewpoint is split so the anchoring character and the narration mode are never
conflated:

- `viewpoint_character` — whose experience anchors the scene (a character).
- `narrative_perspective` — narration person/distance (first person, third
  limited/close, omniscient, objective, etc.).
- `location`, `scene_objective`, `required_outcome`, `prohibited_outcome`,
  `knowledge_boundary`, `protected_craft_or_tone`.
- `problems` — for incomplete/contradictory requests, list what is missing or
  contradictory and null the affected fields; never invent a resolution. A known
  focal character with an unstated narration mode fills `viewpoint_character` and
  nulls `narrative_perspective` (do not mark the character missing).

## Provenance and licensing

**Provenance records origin; review status records adjudication.** Human review,
editing, or approval does **not** convert model-authored source material into
human-authored provenance — a `model_authored` record stays `model_authored`
forever. The `origin` field (`human_authored | model_authored | mixed_origin |
unknown`) and `teacher_model` must truthfully name any model that authored or
materially generated the record; never write `teacher_model: none` for
`model_authored` content.


- Seed records use **newly generated internal synthetic passages** only, unless
  Gary explicitly supplied prose for a record.
- **No copyrighted published fiction is ingested. No living author is imitated by
  name.** No teacher-generated record is marked commercially cleared unless the
  applicable provider terms have actually been reviewed
  (`teacher_terms_status: cleared`); otherwise use `pending_review` and
  `excluded_from_training: true`.
- Records may exist for review while excluded from training.

## Review and promotion

`draft → mechanically validated → Gate 1 adversarial review → Gate 2 independent
model review → Gary author review (where required) → approved → frozen →
compiled`. **No script promotes a record to approved**, and
`mechanically_validated` is never a substitute for literary approval.
Approved/frozen records are never placed in `drafts/`. Compilation to JSONL
happens only after freeze.

## Split policy

Seed records are `split: unassigned`. Final train/eval assignment is a later,
deliberate step made by template family, semantic cluster, source-passage family,
contradiction pattern, revision target, and style profile where necessary. The
eval set must not contain cosmetic rewrites of training templates.
