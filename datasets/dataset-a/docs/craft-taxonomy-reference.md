# Craft Taxonomy — Reference for Dataset A

> **Status / provenance note.** The authoritative **LineWright Craft Taxonomy**
> document was **not** supplied to this repository. This file records the
> three-tier structure and the specific technique lists **as given in the Dataset A
> dispatch**, so records have a stable labeling framework. It is a *reference for
> labeling*, not a replacement taxonomy. When the authoritative taxonomy document
> is provided, it should be added here verbatim and this file reconciled to it
> (technique wording must not be silently rewritten). **This is an open item for
> Gary's review** (see the dataset README, Open questions).

Dataset A uses the taxonomy as a labeling and evaluation framework and does **not**
attempt to train the complete taxonomy. The three-tier distinction is preserved.

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
