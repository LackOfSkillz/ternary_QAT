# Craft Taxonomy — Dataset A working subset (NON-AUTHORITATIVE)

> **Not authoritative.** The authoritative source is
> [`linewright-craft-taxonomy.md`](linewright-craft-taxonomy.md) (installed in
> Dispatch 13). This file is only a **short working subset** of the tiers/examples
> most used by the Dataset A seed batch; it does not add, remove, or reinterpret
> any technique. On any discrepancy, the authoritative file governs.

Dataset A uses the taxonomy as a labeling and evaluation framework and does **not**
attempt to train the complete taxonomy. The three-tier distinction is preserved
exactly as in the authoritative source.

## Tier A — Measurable

Deterministic or near-deterministic text properties. Suitable for checkable
`expected_properties` and evaluation criteria.

- sentence-length variance
- fragments
- parataxis and hypotaxis
- verb density
- active and passive voice
- adverb density
- adjective stacking
- filter-word density
- modal hedging
- concrete and abstract diction
- dialogue-tag frequency
- action beats
- turn-length variance
- contraction rate

## Tier B — Estimable

Use **sparingly** and with **explicit review uncertainty**. Tier B labels are
**not** perfectly objective and must be flagged as estimates in Reviewer Notes.

- psychic distance
- free indirect discourse
- subtext
- emotional naming
- show versus tell
- significant detail
- perceptual bias
- register
- tonal mode
- sentimentality

## Tier C — Structural

Represented **only** as declared author or scene-contract constraints. Tier C
techniques must **not** be treated as candidate-vote-learned preferences.

- viewpoint
- late entry or early exit
- required value shift
- prohibited scene outcome
- scene objective
- chronology structure

## Usage rules in Dataset A

- Prefer Tier A properties for `expected_properties` and evaluation (checkable).
- Tier B concepts may appear but must be labeled as estimates with reviewer
  uncertainty; never gate correctness solely on a Tier B judgment.
- Tier C appears only inside declared constraints (scene contracts, canon), never
  as a learned stylistic preference.
