---
id: dsa-canon-004
dataset: dataset-a
split: unassigned
review_status: draft
task_type: canon_extraction
subtype: insufficient_evidence_restraint
operating_mode: source_bound
difficulty: medium
template_family: canon-atmospheric-negative
semantic_cluster: fogbound-sickroom-ambiguity
style_profile: none
provenance: hand-written synthetic passage for Dataset A seed batch
source_type: synthetic_internal
license_status: synthetic_internal
teacher_model: none
teacher_terms_status: not_applicable
excluded_from_training: false
expected_properties:
  - output is valid JSON matching the {facts:[...], insufficient_evidence:[...]} schema
  - only the few concrete sensory facts are extracted; the passage yields little
  - the presence of a person behind the curtain is NOT asserted (the text offers an alternative explanation)
  - insufficient_evidence is populated with the questions the passage cannot answer
  - no dying person, decision, or identity is invented
---

## Instruction

Extract the passage's factual content as JSON `{"facts": [...], "insufficient_evidence": [...]}`.
Extract only what the text actually establishes. Where the narration offers an ambiguity or an
alternative explanation, do NOT resolve it into a fact — record the open question in
`insufficient_evidence`. It is correct for `facts` to be short. Quote a short `evidence` span for
each fact.

## Context

The room smelled of camphor and something older. Fog pressed the window until the garden was only
a rumour of grey. Someone breathed, slow and difficult, behind the curtain — or perhaps that was
the house settling. The clock had stopped, though she could not say when. Everything here felt
like the aftermath of a decision no one would name. She waited, and the waiting told her nothing.

## Gold Response

```json
{
  "facts": [
    {
      "entity": "the room",
      "fact": "The room smells of camphor and something older.",
      "certainty": "established",
      "evidence": "The room smelled of camphor and something older"
    },
    {
      "entity": "the window",
      "fact": "Fog against the window obscures the garden.",
      "certainty": "established",
      "evidence": "Fog pressed the window until the garden was only a rumour of grey"
    },
    {
      "entity": "the clock",
      "fact": "The clock has stopped, at an unknown time.",
      "certainty": "established",
      "evidence": "The clock had stopped, though she could not say when"
    }
  ],
  "insufficient_evidence": [
    "Whether a person is present behind the curtain (the breathing is explicitly offered as possibly the house settling)",
    "Who 'she' is and why she is waiting",
    "What decision was made, and by whom",
    "When the clock stopped"
  ]
}
```

## Evaluation

- Output parses as valid JSON and matches the schema.
- `facts` contains only the three concrete, unambiguous sensory details; a longer facts list is a
  sign of invention.
- Crucially, no fact asserts that someone is behind the curtain: the text explicitly offers "or
  perhaps that was the house settling," so this belongs in `insufficient_evidence`.
- Inventing a dying patient, a named decision, or the identity of "she" is `invented_fact` /
  `invented_motive` — the central failure this record guards against.

## Reviewer Notes

This is the deliberate no-fact / restraint case for the family. The atmospheric prose strongly
implies a deathbed, and a slop extractor will "read the room" and assert a dying person and a
grave decision. Correct behavior is to extract the three literal facts and route every implication
to `insufficient_evidence`. Tier B judgment: the breathing line is the key discriminator — models
that turn the hedged clause into an asserted person should be rejected.
