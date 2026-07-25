# Held-Out Eval - Retrieval Safety (Dispatch 30H)

Lexical and structural retrieval are separated. **human_recognizability_rating pending Gary's review.**

## Lexical (deterministic)
- exact target overlaps: 0 / 66
- max 8-gram overlap: 0 ; max 13-gram overlap: 0
- No lexical reproduction of target prose by any arm.

## Provisional structural reconstruction (automated, human-gated)
- overall: {'medium': 27, 'low': 13, 'high': 23, 'none': 3}
- by prompt condition: {'atomic_packet': {'medium': 18, 'low': 9, 'none': 3, 'high': 3}, 'compositional_packet': {'medium': 9, 'low': 4, 'high': 20}}
- by cohort: {'heldout_low': {'none': 3, 'low': 5, 'medium': 4}, 'heldout_medium': {'medium': 17, 'low': 5, 'high': 14}, 'heldout_retrieval_sensitive': {'low': 3, 'high': 9, 'medium': 6}}

**Provisional key finding:** compositional prompts drive substantially more structural reconstruction than atomic prompts (no lexical reproduction in any arm). The pre-labeled retrieval-sensitive cohort produced the most provisional reconstruction. Final structural/recognizability judgments await the human blind review.
