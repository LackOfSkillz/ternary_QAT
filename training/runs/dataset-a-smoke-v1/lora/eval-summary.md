# lora eval summary (7 held-out records)

Smoke comparison of base vs trained vs gold. **Seven records prove nothing
about general quality**; structural validity and restraint are the only
mechanical signals. Outputs are truncated for readability.

## dsa-boundary-001  (fiction_boundary)
- base format_valid: True | lora format_valid: True
- deterministic_checks (lora): {'expected_format': 'prose', 'format_valid': True}
- gold: `"Sit. You've been chasing me so long I almost feel we're family now." A pause, the slow turn of a ring on his finger. "Family. There's a word. I hear yours is s`
- base out: `Vane leans back in his chair, fingers tracing the edge of a chipped porcelain cup. The steam from it curls into the air like a ghost.  

“You’ve been chasing sh`
- lora out: `You're not going to find her in the house. She's not in the house. She's not in the house. She's not in the house.`
- note: _human review pending; mark improved/degraded/unchanged at Gate_

## dsa-canon-003  (canon_extraction)
- base format_valid: True | lora format_valid: True
- deterministic_checks (lora): {'expected_format': 'json', 'format_valid': True}
- gold: `{
  "facts": [
    {
      "entity": "the governor's ship (eel-woman's claim)",
      "fact": "The eel-woman claims the ship sank off the Reach with all hands; `
- base out: `{"facts": [
  {
    "entity": "eel-woman",
    "fact": "The governor's ship sank off the Reach, all hands.",
    "certainty": "character_belief",
    "evidence"`
- lora out: `{
  "facts": [
    {
      "entity": "the governor's ship",
      "fact": "sank off the Reach",
      "certainty": "character_belief",
      "evidence": "the go`
- note: _human review pending; mark improved/degraded/unchanged at Gate_

## dsa-constraint-002  (constraint_check)
- base format_valid: True | lora format_valid: False
- deterministic_checks (lora): {'expected_format': 'json', 'format_valid': False}
- gold: `{
  "violation": true,
  "type": "knowledge_state",
  "constraint_ids": ["K1"],
  "explanation": "Constraint K1 states Wren does not learn the recipient's name,`
- base out: `{"violation": true, "type": "knowledge_state", "constraint_ids": ["K1", "K2", "T1"], "explanation": "Wren is in Scene 2, before the seal is broken, and thus doe`
- lora out: `{
  "violation": true,
  "type": "knowledge_state",
  "constraint_ids": ["K1", "K2"],
  "explanation": "Wren has not yet broken the seal, so she has not yet lea`
- note: _human review pending; mark improved/degraded/unchanged at Gate_

## dsa-revision-002  (focused_revision)
- base format_valid: False | lora format_valid: False
- deterministic_checks (lora): {'expected_format': 'json', 'format_valid': False, 'no_change_case': True, 'no_change_preserved': False}
- gold: `{
  "changed": false,
  "reason": "No genuine defect found.",
  "text": "The generator ran all night in the yard, coughing twice an hour like something that had`
- base out: `The generator ran all night in the yard, coughing twice an hour like something that had learned the trick of breathing. By dawn the fuel was gone. Petra counted`
- lora out: `The generator ran all night in the yard, coughing twice an hour like something
that had learned the trick of breathing. By dawn the fuel was gone. Petra counted`
- note: _human review pending; mark improved/degraded/unchanged at Gate_

## dsa-revision-007  (focused_revision)
- base format_valid: True | lora format_valid: True
- deterministic_checks (lora): {'expected_format': 'prose', 'format_valid': True}
- gold: `She came down to the river the way the year comes down to winter — slowly, and
then all at once — and the water took her name and carried it, syllable by
syllab`
- base out: `She came down to the river the way the year comes down to winter — slowly, and then all at once — and the water took her name and carried it, syllable by syllab`
- lora out: `She came down to the river the way the year comes down to winter — slowly, and
then all at once — and the water took her name and carried it, syllable by
syllab`
- note: _human review pending; mark improved/degraded/unchanged at Gate_

## dsa-revision-018  (focused_revision)
- base format_valid: True | lora format_valid: True
- deterministic_checks (lora): {'expected_format': 'prose', 'format_valid': True}
- gold: `He comes to the fence and sets both hands on the top rail, close enough that she
could step back and doesn't. She keeps pulling dead heads off the geraniums, on`
- base out: `Their eyes meet across the yard. She looks away. His gaze follows her. Her eyes widen as he steps closer, and their eyes lock again. She watches him, and he wat`
- lora out: `Their eyes meet across the yard. She looks away. His gaze follows her. She watches
him, and he watches her, neither willing to look away first.`
- note: _human review pending; mark improved/degraded/unchanged at Gate_

## dsa-scene-002  (scene_contract)
- base format_valid: True | lora format_valid: True
- deterministic_checks (lora): {'expected_format': 'yaml', 'format_valid': True}
- gold: `viewpoint_character: Odalys (the narration never leaves her).
narrative_perspective: Third person limited, close; locked tightly to her perspective.
location: T`
- base out: `viewpoint: third person limited tight to Odalys  
location: the covered night market under the river bridge, stalls closing down, lamps guttering  
scene_object`
- lora out: `viewpoint: Odalys
location: the covered night market under the river bridge
scene_objective: Odalys has to talk the fence, a wary old man called Bram, into acce`
- note: _human review pending; mark improved/degraded/unchanged at Gate_
