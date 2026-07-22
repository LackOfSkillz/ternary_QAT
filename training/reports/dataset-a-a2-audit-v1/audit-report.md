# Dataset A + A.2 Audit (Dispatch 25, D9)

Read-only audit of the current training data. **No dataset file was modified.** Token counts
use the real model tokenizer (revision `4485fae…`), not whitespace. Findings separate what is
**observed**, what is a **hypothesized risk**, and what is **not yet known**.

## Task balance — examples vs tokens (the mandatory distinction)

**Dataset A** (35 records):

| task | examples | response tokens |
|---|---|---|
| focused_revision | 20 | 1295 |
| canon_extraction | 5 | **1666** |
| constraint_check | 5 | 824 |
| scene_contract | 3 | 733 |
| fiction_boundary | 2 | 254 |

**Observed:** example counts and token mass disagree. `canon_extraction` has only 5 examples
but the **most** response tokens (1666 > focused_revision's 1295 from 20 examples), because
canon golds are long JSON. `fiction_boundary` and `scene_contract` are thin on both axes.

**Dataset A.2 pilot** (33 records): focused_revision 19 ex, canon 6, constraint 4, scene 3,
boundary 1 — more balanced by examples; token mass in `task-distribution.json`.

## No-change / changed protocol coverage

**Observed:** Dataset A teaches `changed:false` **2** times and `changed:true` **0** times —
the model never sees the "a genuine defect exists → emit `changed:true`" half of the wrapper.
Dataset A.2 pilot fixes this: `changed:false` 8, `changed:true` 4. This matches the
Dispatch-24 live finding that **both** models fail the structured no-change/revision wrapper.

## Structured-protocol coverage

**Observed:** Dataset A golds are prose 23 / JSON 12 (no YAML in the compiled shape count);
A.2 pilot JSON 22 / prose 11. Structured protocol is a minority of Dataset A by example.

## Repetition / template concentration

**Observed:** exact duplicate responses **0**, approximate duplicates (≥0.85 shingle
similarity) **0**, and cross-response surface similarity ≥0.5 is **0** for both datasets.
Repeated sentence openings / endings clusters: none at the ≥3 threshold.

**Not called contamination.** There is no evidence of template concentration in the golds.
(This is a *dataset* property; it does not contradict the *model* degeneration seen at
inference — that is a training-dynamics/overfitting effect, not copied dataset templates.)

## Voice / register distribution

**Observed:** Dataset A style profiles — `none` 15, and 4 each of `dark-speculative`,
`romantic-emotional`, `suspense-mystery`, `lyrical-mythic`, `contemporary-commercial` (20
voice-conditioned). Reasonable register spread; `none` (unstyled) is the plurality.

## Provenance

**Observed (as recorded, not inferred):** all 35 Dataset A records and all A.2 pilot records
are `model_authored` by **`claude-opus-4-8`**. No human-authored, licensed, or public-domain
records. No provenance is guessed; nothing is marked unknown because the records record it.

## Audit conclusions

```yaml
observed:
  - example-count balance != token-mass balance (canon dominates tokens with few examples)
  - Dataset A: 2 changed:false, 0 changed:true (no-change protocol half-taught)
  - structured protocol is a minority of Dataset A by example
  - zero exact/approx duplicate responses; zero template concentration (>=0.5) 
  - single teacher model (claude-opus-4-8) across 100% of records
hypothesized_risk:
  - single-teacher style concentration could narrow the taught voice range (RISK, not proven;
    template similarity is 0, so no direct evidence of copied structure)
  - token-mass imbalance may over-weight canon-JSON in the loss relative to prose craft
  - thin boundary/scene coverage may under-teach those capabilities
not_yet_known:
  - whether the token imbalance materially shaped the LoRA-20 degeneration (needs a
    token-balanced controlled run to test)
  - whether a second teacher / human editing would broaden voice (untested)
```

Dataset A and A.2 were **not modified** in this dispatch. Any dataset change is a future,
separately-authorized experiment.
