# LWDB Slop Report (v1) — Module J

How to read a slop report and what each field means. Module J is **slop detection and
stylistic degradation** — it is **not** an AI-authorship detector. Implemented in
[`linewright/evaluation/slop/`](../../linewright/evaluation/slop/); schema
`benchmarks/schemas/slop-report-schema.yaml`; research basis
[`slop-detection-research-review-v1.md`](slop-detection-research-review-v1.md).

## Core principle

A slop report **never collapses into one opaque score**. It reports four kinds of evidence
separately — deterministic, semantic (interface-only in this build), lexical/style, and
reviewer — each with **evidence spans** and its own confidence. A scalar without the
implicated passages is insufficient. **All numeric thresholds are unvalidated** until
calibration; the only escalation threshold used now is the already-justified Dispatch-21
repetition gate, and the report says so in `summary.limitations`.

## Sections

### `identity`
`slop_report_id`, `output_id`, `item_id`, `detector_manifest_id` (pins the exact detector
suite/versions), `reference_profile_id` (the baseline compared against; profiles are **not**
universally interchangeable — a lyrical passage is not judged against a terse-noir profile),
`created_at`.

### `input_characteristics`
`task_type`, `requested_voice`, `genre`, `target_length`, `actual_length`, `prompt_surface`,
and `short_output_metric_limitations` (true when the output is too short for stable
diversity metrics — the metrics are then reported, not judged).

### `deterministic` (Layer 1 — implemented, versioned)
- **Repetition**: `exact_duplicate_sentences`, `exact_duplicate_clauses`,
  `repeated_ngram_rates` (n → max repeat), `repeated_sentence_openings`,
  `repeated_paragraph_openings`, `compression_ratio`.
- **Lexical diversity**: `unique_token_ratio`, `mattr` (moving-average TTR), `mtld`, `hdd`,
  `hapax_rate`. These are standard measures; their use as slop signals is engineering
  inference, not a validated verdict.
- **Sentence rhythm**: `mean`, `variance`, `entropy` (uniform length is a collapse *signal* —
  but low variance is legitimate in terse styles).
- `paragraph_shape`, `output_to_source_ratio`, `hit_token_cap`.
- `source_overlap` is reported **separately** — it is a fidelity signal, not slop.
- `evidence_spans`: verbatim spans backing each flag.

### `semantic` (Layer 2 — interface-only in this build)
`redundant_span_pairs`, `paraphrase_loops`, `explanation_after_demonstration`,
`repeated_paragraph_functions`, `local_coherence_flags`, `scene_progression_flags`,
`voice_profile_distance`, `character_voice_similarity`, `cross_output_template_similarity`.
`detector_confidence` is **`unvalidated`** until frozen embeddings are pinned and calibrated;
the block is structurally present but empty (the `NullSemanticDetector`), never a fabricated
number. Every future semantic finding must carry evidence spans.

### `lexical_style`
`stock_phrase_hits`, `clustered_stock_phrases`, vague/abstraction/specificity/weak-verb
signals. A phrase inventory is **one signal only, never a sole detector**: a phrase matters
by frequency, clustering, cross-output repetition, context, genre, and requested voice — a
single occurrence never auto-fails.

### `reviewer` (Layer 3 — checklist)
Decomposed binary checks (`slop-reviewer-checklist-v1`, 12 questions) instead of one vague
rating. Each positive finding must carry evidence spans, an explanation, a severity, and a
confidence. Reviewers answer blind; calibration status is recorded.

### `corpus_level`
Per-run sameness (see `slop-corpus-summary-schema` / `corpus.py`): repeated opening/ending
patterns, template similarity clusters, and — once semantic detectors exist — image-family
and voice convergence. Every cluster cites the evidence outputs. Corpus comparison across
model roles happens only **after** blind per-output scoring is locked.

### `summary`
- `severity`: `none | low | moderate | high | severe | inconclusive`.
- `dominant_failure_types`, `fatal_slop_failure`.
- **Separate confidences**: `mechanical_confidence`, `semantic_confidence`,
  `reviewer_confidence`, `overall_confidence`.
- `limitations` (always includes the unvalidated-threshold + interface-only caveats).
- `likely_bottlenecks` and separated recommendations: `recommended_dataset_actions`,
  `recommended_training_actions`, `recommended_context_actions`, `recommended_decoding_actions`.

## Likely tuning levers (hypotheses, not verdicts)

A causal cause still requires matched evidence (a controlled pair / surface comparison).
Examples: exact repetition late in output → decoding / training duration / repetition
negative examples; semantic restatement without exact duplication → dataset coverage /
contrastive revision examples; voice convergence → dataset voice balance / overtraining /
base capacity; bare clean but compiled sloppy → context compilation / packet length; short
clean but long sloppy → long-horizon generation / decoding / length balance; midpoint clean
but final sloppy → training duration / checkpoint selection / overfitting.

## Calibration

The detector is validated against known-good and known-bad examples
(`benchmarks/calibration/slop-calibration-set-v1.jsonl`). Known-good deliberate repetition,
concise prose, and lyrical/unusual syntax must **not** be flagged severe/high; deterministic
known-bad (exact/structural repetition loops) must be flagged. Semantic known-bad
(paraphrase loops, voice homogenization) are recorded but not asserted yet — the semantic
layer is interface-only.
