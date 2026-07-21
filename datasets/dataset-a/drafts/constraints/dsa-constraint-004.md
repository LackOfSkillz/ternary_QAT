---
id: dsa-constraint-004
dataset: dataset-a
split: unassigned
review_status: draft
task_type: constraint_check
subtype: object_state
operating_mode: constraint_bound
difficulty: medium
template_family: constraint-object-state-track
semantic_cluster: cellar-door-locked-latch
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
  - type equals "object_state"
  - constraint_id cites the object-state constraint
  - evidence quotes the action that contradicts the object's declared state
---

## Instruction

You are a continuity checker for a fiction manuscript. You are given declared constraints about the state of physical objects (locked/unlocked, open/closed, broken/whole) and a draft passage. Decide whether the passage places an object in two contradictory states without an event that changes it. Respond with one JSON object:
{"violation": bool, "type": "factual_contradiction"|"knowledge_state"|"chronology"|"object_state"|"none", "constraint_id": <string or null>, "explanation": <string>, "evidence": <string>}

## Context

Declared canon constraints:
- O1 (object state): The cellar door is locked from the inside with an iron bolt. No character in this scene has a way to reach the bolt from the stairwell side.
- O2 (object state): The only key to the cellar is on a ring in the kitchen, two floors up, and no one retrieves it during this scene.
- O3 (event rule): The bolt makes a loud grinding sound whenever it is drawn; any drawing of the bolt must be narrated.

Draft passage:
"Neave came down the stairwell with the candle guttering in her fist. She tested the cellar door and felt the iron bolt hold firm against her shoulder — locked, as it had been all week. She swore under her breath. Then she pushed the door open, stepped down onto the packed earth of the cellar floor, and lifted the candle to see what the dark had been hiding."

## Gold Response

```json
{
  "violation": true,
  "type": "object_state",
  "constraint_id": "O1",
  "explanation": "Constraint O1 sets the cellar door as bolted from the inside, and the draft confirms the bolt 'hold firm' and 'locked.' With no key retrieved (O2) and no bolt-drawing narrated (O3), the door must remain locked. Yet Neave pushes it open and steps through in the next sentence. The door is both locked and passable in the same moment, with no state-changing event.",
  "evidence": "Then she pushed the door open, stepped down onto the packed earth of the cellar floor"
}
```

## Evaluation

- Response is a single valid JSON object matching the schema.
- violation is exactly true.
- type is exactly "object_state".
- constraint_id is "O1" (the locked-door state); explanation shows O2 and O3 both fail to supply an unlocking event.
- evidence quotes the action (pushing the door open and entering) that contradicts the locked state.
- The checker requires a narrated state change and correctly notes its absence, rather than assuming an off-page unlock.

## Reviewer Notes

Teaches physical object-state consistency: the same object (cellar door) is asserted locked and then walked through with no intervening event. The event rule O3 makes the missing transition explicit, so the model can justify the violation instead of hand-waving. Distinct from factual_contradiction because the conflict is a state over time, not a fixed attribute.
