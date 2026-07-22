# lora eval summary (7 held-out records)

Structure only; NOT a quality verdict from 7 records.

## dsa-boundary-001  (fiction_boundary)
- format_valid: True | checks: {'expected_format': 'prose', 'format_valid': True}
- gold: `"Sit. You've been chasing me so long I almost feel we're family now." A pause, the slow turn of a ring on his finger. "Family. The`
- lora out: `You're not going to find her in the back room. She's in the front. She's in the front room. She's in the front room.`
- note: _human review pending_

## dsa-canon-003  (canon_extraction)
- format_valid: False | checks: {'expected_format': 'json', 'format_valid': False}
- gold: `{
  "facts": [
    {
      "entity": "the governor's ship (eel-woman's claim)",
      "fact": "The eel-woman claims the ship sank `
- lora out: `{
  "facts": [
    {
      "entity": "governor's ship",
      "fact": "sank off the Reach",
      "certainty": "character_belief",`
- note: _human review pending_

## dsa-constraint-002  (constraint_check)
- format_valid: False | checks: {'expected_format': 'json', 'format_valid': False}
- gold: `{
  "violation": true,
  "type": "knowledge_state",
  "constraint_ids": ["K1"],
  "explanation": "Constraint K1 states Wren does n`
- lora out: `{
  "violation": true,
  "type": "knowledge_state",
  "constraint_ids": ["K1", "K2"],
  "explanation": "Wren has not yet broken th`
- note: _human review pending_

## dsa-revision-002  (focused_revision)
- format_valid: False | checks: {'expected_format': 'json', 'format_valid': False, 'no_change_case': True, 'no_change_preserved': False}
- gold: `{
  "changed": false,
  "reason": "No genuine defect found.",
  "text": "The generator ran all night in the yard, coughing twice a`
- lora out: `The generator ran all night in the yard, coughing twice an hour like something
that had learned the trick of breathing. By dawn th`
- note: _human review pending_

## dsa-revision-007  (focused_revision)
- format_valid: True | checks: {'expected_format': 'prose', 'format_valid': True}
- gold: `She came down to the river the way the year comes down to winter — slowly, and
then all at once — and the water took her name and `
- lora out: `She came down to the river the way the year comes down to winter — slowly, and
then all at once — and the water took her name and `
- note: _human review pending_

## dsa-revision-018  (focused_revision)
- format_valid: True | checks: {'expected_format': 'prose', 'format_valid': True}
- gold: `He comes to the fence and sets both hands on the top rail, close enough that she
could step back and doesn't. She keeps pulling de`
- lora out: `Their eyes meet across the yard. She looks away. His gaze follows her. She watches
him, and he watches her, neither willing to loo`
- note: _human review pending_

## dsa-scene-002  (scene_contract)
- format_valid: True | checks: {'expected_format': 'yaml', 'format_valid': True}
- gold: `viewpoint_character: Odalys (the narration never leaves her).
narrative_perspective: Third person limited, close; locked tightly t`
- lora out: `viewpoint: third person
location: the covered night market under the river bridge
scene_objective: Odalys has to talk the fence, a`
- note: _human review pending_
