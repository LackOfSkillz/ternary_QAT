---
id: dsa-canon-001
dataset: dataset-a
split: unassigned
review_status: draft
task_type: canon_extraction
subtype: interior_deduction_scene
operating_mode: source_bound
difficulty: easy
template_family: canon-interior-monologue
semantic_cluster: waiting-room-coat-count
style_profile: none
provenance: hand-written synthetic passage for Dataset A seed batch
source_type: synthetic_internal
license_status: synthetic_internal
teacher_model: none
teacher_terms_status: not_applicable
excluded_from_training: false
expected_properties:
  - output is valid JSON matching the {facts:[...], insufficient_evidence:[...]} schema
  - the coat count (four) is labeled certainty "established"
  - Nadia's expectation that the meeting will go badly is labeled "character_belief", not "established"
  - the deduction that no one new arrived is labeled "inferred"
  - no fact about who she is meeting or why her name is misspelled is invented
---

## Instruction

Read the passage and extract its factual content as a JSON object with the schema
`{"facts": [{"entity", "fact", "certainty", "evidence"}], "insufficient_evidence": [...]}`.
Use `certainty: "established"` for what the narration states as true, `"character_belief"`
for what the viewpoint character asserts or expects but the text does not confirm, and
`"inferred"` for conclusions the character reaches by reasoning. Quote a short span from the
passage as `evidence`. Do not add facts the passage does not contain.

## Context

Nadia counted the coats on the rack by the door: four. She had hung three when she arrived,
and her own made four, so no one new had come while she waited in the back office. The
radiator ticked. She told herself the meeting would go badly — they always did — but she had
no reason yet to think so. On the desk lay a single unopened envelope with her name misspelled.

## Gold Response

```json
{
  "facts": [
    {
      "entity": "coat rack",
      "fact": "There are four coats on the rack by the door.",
      "certainty": "established",
      "evidence": "counted the coats on the rack by the door: four"
    },
    {
      "entity": "Nadia",
      "fact": "She hung three coats on arrival, and her own coat is the fourth.",
      "certainty": "established",
      "evidence": "She had hung three when she arrived, and her own made four"
    },
    {
      "entity": "the back office",
      "fact": "No one new arrived while Nadia was waiting.",
      "certainty": "inferred",
      "evidence": "so no one new had come while she waited"
    },
    {
      "entity": "the meeting",
      "fact": "Nadia expects the meeting to go badly.",
      "certainty": "character_belief",
      "evidence": "the meeting would go badly — they always did — but she had no reason yet to think so"
    },
    {
      "entity": "envelope on the desk",
      "fact": "An unopened envelope on the desk has Nadia's name misspelled.",
      "certainty": "established",
      "evidence": "a single unopened envelope with her name misspelled"
    }
  ],
  "insufficient_evidence": [
    "Who Nadia is meeting or what the meeting concerns",
    "Why her name is misspelled on the envelope",
    "What the envelope contains"
  ]
}
```

## Evaluation

- The output parses as valid JSON and matches the required schema.
- The coat count and the misspelled envelope are labeled `established`.
- Nadia's expectation about the meeting is labeled `character_belief`; labeling it
  `established` is wrong because the text explicitly says she "had no reason yet to think so."
- "No one new arrived" is labeled `inferred` (a deduction from the coat count), not `established`.
- `insufficient_evidence` names the meeting's purpose and the misspelling; inventing either
  (e.g. asserting she is meeting a lawyer) is a failure.

## Reviewer Notes

Intended as the easy anchor for the family: the deduction is spelled out in-text and the
belief/truth split is signposted by "she had no reason yet to think so." Tier A / mechanical —
every label is verifiable against an explicit cue in the prose, so reviewer uncertainty is low.
