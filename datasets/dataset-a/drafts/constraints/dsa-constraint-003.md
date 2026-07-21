---
id: dsa-constraint-003
dataset: dataset-a
split: unassigned
review_status: draft
task_type: constraint_check
subtype: chronology
operating_mode: constraint_bound
difficulty: hard
template_family: constraint-travel-clock
semantic_cluster: ferry-crossing-market-dawn
style_profile: none
provenance: hand-written synthetic passage for Dataset A seed batch
source_type: synthetic_internal
license_status: synthetic_internal
teacher_model: none
teacher_terms_status: not_applicable
excluded_from_training: false
expected_properties:
  - output is valid JSON with a boolean 'violation' field
  - violation is true for this record
  - type equals "chronology"
  - constraint_id cites the travel-time or timeline constraint
  - evidence quotes the timing detail that cannot be reconciled
---

## Instruction

You are a continuity checker for a fiction manuscript. You are given declared canon constraints about distances, travel times, and clock times, plus a draft passage. Decide whether the sequence and timing of events is physically possible under the constraints. Respond with one JSON object:
{"violation": bool, "type": "factual_contradiction"|"knowledge_state"|"chronology"|"object_state"|"none", "constraint_id": <string or null>, "explanation": <string>, "evidence": <string>}

## Context

Declared canon constraints:
- D1 (distance/time): The only crossing from Halden to the mainland is the ferry, and the ferry passage takes a full four hours. There is no bridge and no other boat.
- D2 (schedule): The ferry departs Halden once daily, at first light (dawn).
- D3 (schedule): The mainland market opens at dawn and closes at noon.

Draft passage:
"Tomas woke on Halden to a grey, uncertain dawn and just caught the ferry as its ropes came loose. He spent the whole crossing at the rail, watching the island shrink. By the time the hull knocked against the mainland pier, the sun had barely climbed. He shouldered his empty sack and hurried up the hill to the market, arriving while the first stalls were still being unfolded, well before the morning crowd."

## Gold Response

```json
{
  "violation": true,
  "type": "chronology",
  "constraint_id": "D1",
  "explanation": "The ferry departs at dawn (D2) and the crossing takes four hours (D1), so Tomas cannot reach the mainland before roughly mid-morning. But the market opens at dawn and closes at noon (D3), and the draft has him arriving 'while the first stalls were still being unfolded, well before the morning crowd' — i.e., at market opening, which is dawn. Arriving at the dawn market after a four-hour post-dawn crossing is impossible.",
  "evidence": "arriving while the first stalls were still being unfolded, well before the morning crowd"
}
```

## Evaluation

- Response is a single valid JSON object matching the schema.
- violation is exactly true.
- type is exactly "chronology".
- constraint_id cites D1 (the four-hour crossing) as the binding constraint; explanation correctly combines D1+D2+D3 to show the impossibility.
- evidence quotes the arrival-timing phrase that cannot be reconciled, not the departure.
- The checker reasons about elapsed time, not merely keyword overlap; it does not accept "the sun had barely climbed" as sufficient cover for a four-hour gap.

## Reviewer Notes

Hard chronology case: no single sentence is wrong in isolation; the violation emerges only from composing three constraints (crossing duration, departure time, market hours). Teaches multi-constraint temporal reasoning and rewards citing the load-bearing distance/time constraint.
