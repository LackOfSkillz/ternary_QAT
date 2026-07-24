# Held-Out c01 — Evaluation Plan (Dispatch 30F)

Metadata-only design plan for the future evaluation of the compact fiction model + diagnostic
instrument, using the 11 `c01` held-out records (`set_id: heldout-c01`, `split: heldout_eval`,
`training_eligible: false`). No inference is run here; this documents the intended comparisons.

## Comparison arms
- `frozen_base` — the untrained base model.
- `atomic_packet_sft` — model trained on the atomic arm of the 54 production pairs.
- `compositional_packet_sft` — model trained on the compositional arm.
- `optional_replay_arm` — optional arm with replay/mixture, if run.

## Prompt conditions
- `atomic_packet`
- `compositional_packet`

**Key interaction:** `model_arm × prompt_condition`. The strongest analysis evaluates **every trained
model under BOTH packet types** — not merely each model with the packet type it trained on — so the
compositional-vs-atomic effect is separated from the prompt-format effect.

## Primary measurements
- packet_instruction_adherence
- scene_causality
- prose_quality
- narrative_coherence
- constraint_satisfaction
- source_structure_reconstruction
- suspicious_phrase_overlap

## Retrieval-safety measurements (per generated output, at eval time)
Separate **lexical reproduction** from **structural reconstruction** — a model can be lexically clean
while still recreating an identifying scene structure.
- exact_target_overlap
- longest_common_substring
- target_ngram_overlap at n ∈ {5, 8, 13}
- named_entity_reconstruction
- distinctive_event_sequence_reconstruction
- source_specific_world_rule_reproduction
- human_recognizability_rating

The `heldout_retrieval_sensitive` cohort (structural rating high) is the primary stress set for the
structural-reconstruction measurements.

## Evaluation cohorts (analysis-only, from final post-revision structural rating)
- `heldout_low`, `heldout_medium`, `heldout_retrieval_sensitive`.
These stratify the analysis; they do NOT gate inclusion — all 11 records are evaluated.

## Limitations
- **c01 opening/early-scene bias:** the set is drawn from each source's earliest harvested chapter and
  may overrepresent setup / introduction / orientation / inciting-event structures relative to the
  c02–c06 training distribution. Describe results as performance on **held-out early-book scenes from
  the same source distribution**, not as a complete measure of every scene type.
- **Caveat to the caveat:** several `c01` records were found NOT to be literal chapter-one openings
  (some are mid/late-book harvested scenes — e.g. dense action/climax passages), which partially
  diversifies scene type and softens the opening-bias concern. Do not "correct" the bias by adding
  later c02–c06 scenes into the held-out set — that would contaminate the split.
