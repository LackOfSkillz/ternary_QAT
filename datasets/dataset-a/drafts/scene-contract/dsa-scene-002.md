---
id: dsa-scene-002
dataset: dataset-a
split: unassigned
review_status: draft
task_type: scene_contract
subtype: complete_request
operating_mode: constraint_bound
difficulty: medium
template_family: scene-thirdlimited-heist-negotiation
semantic_cluster: night-market-forged-ledger-standoff
style_profile: none
provenance: hand-written synthetic scenario for Dataset A seed batch
source_type: synthetic_internal
license_status: synthetic_internal
teacher_model: none
teacher_terms_status: not_applicable
excluded_from_training: false
expected_properties:
  - output is valid YAML with fields viewpoint, location, scene_objective, required_outcome, prohibited_outcome, knowledge_boundary, protected_craft_or_tone
  - every field is filled from the writer's request; nothing is invented
  - prohibited_outcome names a scene outcome the writer explicitly barred
  - knowledge_boundary reflects the third-limited POV's specific blind spots
  - no 'problems' field is present because the request is complete
---

## Instruction

You are a scene-contract builder for a fiction writer. Given the writer's scene request in the Context, produce a STRUCTURED scene contract as a single YAML object with exactly these fields: viewpoint, location, scene_objective, required_outcome, prohibited_outcome, knowledge_boundary, protected_craft_or_tone. Fill each field only from what the writer stated or clearly implied. Do not invent constraints. If the request is complete, do not include a 'problems' field.

## Context

Writer's request:
"Scene contract, please. Third person but limited tight to Odalys — we never leave her head. Setting is the covered night market under the river bridge, stalls closing down, lamps guttering. The job of the scene: Odalys has to talk the fence, a wary old man called Bram, into accepting the forged shipping ledger as genuine so he'll release the sealed crate. Required result — Bram hands over the crate before the market watch makes its midnight round. Hard rule: Bram must NOT figure out the ledger is forged in this scene; if he twigs it, the later betrayal beat is ruined, so he stays fooled here. Odalys does not read river-cant, so she can't understand the traders' slang muttered around her, and she doesn't know the watch has been paid to arrive early tonight. Voice-wise keep it wry and tense, lots of dry interiority, short hard sentences when the pressure spikes — no ornate description."

## Gold Response

```yaml
viewpoint: Third person limited, locked tightly to Odalys; the narration never leaves her perspective.
location: The covered night market under the river bridge, at closing time, lamps guttering as stalls shut down.
scene_objective: Odalys must persuade the wary old fence, Bram, to accept the forged shipping ledger as genuine so he releases the sealed crate.
required_outcome: Bram hands over the sealed crate before the market watch makes its midnight round.
prohibited_outcome: Bram must NOT realize the ledger is forged during this scene; he remains fooled so the later betrayal beat is preserved.
knowledge_boundary: Odalys cannot read or understand river-cant, so the traders' muttered slang is opaque to her. She also does not know that the watch has been paid to arrive early tonight.
protected_craft_or_tone: Wry, tense register with dry interiority; short, hard sentences when pressure spikes; no ornate or ornamental description.
```

## Protected Elements

The wry, tense tone; the tight interior third-limited voice; the prose rhythm that clips to short hard sentences under pressure; the avoidance of ornate description. The writer wants these craft signatures carried into the finished scene.

## Evaluation

- Response parses as a single valid YAML object.
- All seven required fields are present and correctly named.
- required_outcome (crate handed over before the midnight round) and prohibited_outcome (Bram not detecting the forgery) are distinct and both traceable to the request.
- knowledge_boundary captures both stated blind spots: no river-cant, and no knowledge of the bribed early watch.
- viewpoint records the tight third-limited lock to Odalys, not a loose or head-hopping third.
- No field is invented; no 'problems' field appears because the request is complete.

## Reviewer Notes

A medium case with a tighter POV mechanic (third limited, two explicit knowledge blind spots) and an outcome constraint tied to plot timing. Tests that the builder distinguishes required vs prohibited outcomes and encodes multiple knowledge limits without merging or dropping one.
