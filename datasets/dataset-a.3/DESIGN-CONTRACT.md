# Dataset A.3 — Design Contract (Dispatch 27 Phase B, Deliverable 4)

**Status: design contract + pilot build. Provisional. `training_only`. Not production-approved.
Gary Gate-3 review PENDING. No record enters training automatically.** Dataset A and Dataset A.2
are **not modified** by this work.

Dataset A.3 is the first *properly scaled* LineWright training corpus, built to test whether a
**conservative Qwen3-8B LoRA** can improve prose/voice/restraint **without** damaging instruction
compliance, structured protocol, canon fidelity, stability, or packet handling. It is a feasibility
pilot dataset, not a production corpus.

Frozen thresholds referenced (reused unchanged): research `2be4fddb…`, starter `98a57af3…`.

## Purpose (what A.3 teaches)

Preserve author voice · improve natural prose · improve tense/viewpoint fidelity · reduce purple
similes and generic embellishment · reduce repeated emotional explanation · obey focused-revision
scope · preserve protected text · produce correct no-change responses · maintain canon · maintain
structured-output reliability · avoid reasoning traces · avoid runaway generation. It does **not**
reteach general assistant behaviour.

## Task mix (records AND token mass; no family dominates by length)

| task_family | record share | notes |
|---|---|---|
| scene_drafting | 0.25 | quiet / dialogue / action / interior / comic / restrained / tense / descriptive |
| focused_revision | 0.20 | alter one sentence/paragraph only; repetition; concrete detail; protected text; tense/viewpoint repair; de-purple; shorten w/o flattening |
| voice_preservation | 0.15 | terse/lyrical/plainspoken/literary/genre/dialogue-led/close-3rd/distant-3rd/1st/dry — **no single house voice** |
| no_change_and_restraint | 0.10 | **both** `changed:true` and `changed:false`; already-correct, almost-correct, would-damage-voice |
| canon_application | 0.10 | maintain canon under continuation/extraction |
| structured_protocol | 0.10 | JSON-only / YAML-only / revision wrappers / constraint-verdict / canon-fact; malformed→correct |
| multi_turn_revision | 0.05 | iterative authorized edits across turns |
| anti_repetition_and_slop | 0.05 | controlled bad→good contrasts on the same source |

Report `examples_by_task`, `tokens_by_task`, `average_output_tokens_by_task`,
`maximum_output_tokens_by_task`. Use token-balanced sampling: no family may dominate token mass
solely because its outputs are longer. `changed:true` and `changed:false` both required (the prior
audit found `changed:false` without adequate `changed:true` contrast).

## Record schema (extends Dataset A's, adds A.3 fields)

Each record carries, at minimum:
`record_id, task_family, operating_mode, difficulty, style_register, genre, template_family,
semantic_cluster, prompt, source, gold_output, output_length_tokens, protected_text (opt),
authorized_changes (opt), unauthorized_changes (opt), changed (no-change tasks), constraint_ids
(constraint tasks), craft_targets, anti_slop_targets`, plus **provenance** (below), plus
`pool` (holdout assignment), `training_only: true`, `benchmark_overlap_checked: true`,
`excluded_from_training: false` (train pool) / `true` (calibration/permanent-trend).

`(template_family, semantic_cluster)` must be unique across the corpus (anti-template discipline).

## Provenance (immutable; review ≠ provenance)

Per record: `record_id, task_family, author_origin, source_origin, writer_or_model,
model_revision, human_editor, human_edit_extent, style_register, genre, output_length,
training_only:true, benchmark_overlap_checked:true`. Provenance classes:
`human_authored | model_authored | human_model_collaborative | public_domain_transformed |
licensed | unknown` (unknown is never guessed). **A model-authored record stays model-authored
forever**; human review/edit does not convert provenance.

**Teacher-concentration safeguard.** No single teacher model should dominate the *complete*
dataset unless explicitly justified. Report `records_by_teacher, tokens_by_teacher,
records_by_human_editor, style_clusters, template_clusters`. **Pilot justification:** this pilot
build is single-teacher (`claude-opus-4-8`, `human_edit_extent: none`, `review_status: draft`) —
justified for a *feasibility pilot* and explicitly flagged; the path to the full 200–500 record set
requires teacher diversification + human curation + Gary Gate-3 review before any production use.

## Holdout and contamination

Pools: `training | development | rotating_diagnostic | permanent_trend_only | calibration | burned`.
Rules: permanent-trend items never drive targeted dataset changes; rotating-diagnostic items may
drive changes but are burned afterward; **benchmark items (Dispatch 24–26 battery, Fast Battery v1,
packet-family) and paraphrases never enter training**; calibration items stay outside training.
Automated overlap checks: exact text · normalized text · n-gram (shingle) similarity · source
metadata · prompt-family similarity (embedding similarity is interface-provided; a deterministic
shingle-Jaccard proxy is used where no embedder is available, and that substitution is logged).

## Coverage requirements (summarized; full matrix enforced by the audit)

- **scene_drafting:** ≥6 of {quiet, dialogue, action, interior, comic, restrained, tense,
  descriptive}; vary narrative distance, sentence architecture, paragraph length, dialogue density,
  genre, tone, pacing.
- **focused_revision:** each of {one-sentence, one-paragraph, de-repeat, concrete-detail,
  protect-text, voice-preserving pacing change, tense/viewpoint repair, de-purple, shorten,
  authorized-beat expansion} represented.
- **voice_preservation:** ≥8 distinct registers; the corpus must not define one universal voice.
- **no_change_and_restraint:** both `changed` values; already-correct / almost-correct /
  would-damage-voice / structured-no-change / exact-preservation.
- **structured_protocol:** JSON-only, YAML-only, revision wrapper, constraint-verdict, canon-fact,
  malformed→correct; structured tasks must not vanish beneath long-prose token mass.
- **anti_slop:** controlled `bad_output`/`good_output` contrasts on the SAME source, one specific
  behaviour each; **never copy benchmark failures into training examples**.

## Freeze

Before training: commit `train_sha256, development_sha256, diagnostic_sha256, manifest_sha256,
record_count, token_count`. A.3 is immutable during a run; any correction ⇒ new dataset version +
new run ID. Audit artifacts live in `training/reports/dataset-a3-audit-v1/`.

## Build status and the 200-record criterion (completion #14)

This dispatch **prepares** A.3 and **holds training** pending Gary's human foundation confirmation.
The pilot build authors a genuinely diverse corpus under this contract (single-teacher, draft,
review-pending) and audits/freezes it. Where the pilot lands below the 300–500 *production* target,
that is the **documented justified exception** the criterion allows: the remaining records require
human authorship/curation, teacher diversification, and Gate-3 review — the project's standing bar
for training data — which autonomous single-teacher generation must not silently substitute.
