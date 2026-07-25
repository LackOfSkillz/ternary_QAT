# Held-Out Evaluation Matrix - Plan (Dispatch 30G)

**Inference NOT started** (requires separate authorization). Metadata only.

| Model arm | atomic prompt | compositional prompt |
|---|---|---|
| frozen_base | 11 | 11 |
| atomic_packet_sft | 11 | 11 |
| compositional_packet_sft | 11 | 11 |

- 3 model arms x 2 prompt conditions x 11 held-out scenes x 1 generation = **66 primary generations**.
- Key interaction: model_arm x prompt_condition (every trained model evaluated under BOTH packet types).
- Decoding: greedy (do_sample=false, temp 0, top_p 1), seed 20260722, max_new_tokens 6144, thinking disabled.
- Prompt contract: no target text, no provenance, no source names, no training metadata - system + packet only.
- Retrieval-safety measures (at eval time): exact_target_overlap, longest_common_substring, target n-gram overlap n in 5/8/13, named_entity_reconstruction, distinctive_event_sequence_reconstruction, source_specific_world_rule_reproduction, human_recognizability. Separate lexical reproduction from structural reconstruction.
