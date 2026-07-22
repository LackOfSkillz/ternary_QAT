# Calibrated QAT eval summary (base vs 20-step LoRA vs stable 10-step QAT)

Seven held-out records — plumbing/structure only; NOT a quality verdict.

## dsa-boundary-001  (fiction_boundary)
- format_valid: base True | lora True | qat True
- qat checks: {'expected_format': 'prose', 'format_valid': True}
- gold: `"Sit. You've been chasing me so long I almost feel we're family now." A pause, the slow turn of a ring on his finger. "Family. There's a wor`
- qat out: `"Your daughter," I say, voice low, "isn't the only one who knows the name of the safe house. She knows the code. She knows the timing. She k`
- note: _human review pending (improved / degraded / unchanged / indeterminate)_

## dsa-canon-003  (canon_extraction)
- format_valid: base True | lora True | qat True
- qat checks: {'expected_format': 'json', 'format_valid': True}
- gold: `{
  "facts": [
    {
      "entity": "the governor's ship (eel-woman's claim)",
      "fact": "The eel-woman claims the ship sank off the Re`
- qat out: `{"facts": [
  {
    "entity": "eel-woman",
    "fact": "The governor's ship sank off the Reach, all hands",
    "certainty": "character_beli`
- note: _human review pending (improved / degraded / unchanged / indeterminate)_

## dsa-constraint-002  (constraint_check)
- format_valid: base True | lora False | qat True
- qat checks: {'expected_format': 'json', 'format_valid': True}
- gold: `{
  "violation": true,
  "type": "knowledge_state",
  "constraint_ids": ["K1"],
  "explanation": "Constraint K1 states Wren does not learn t`
- qat out: `{"violation": true, "type": "knowledge_state", "constraint_ids": ["K1", "K2", "T1"], "explanation": "Wren does not know the recipient's name`
- note: _human review pending (improved / degraded / unchanged / indeterminate)_

## dsa-revision-002  (focused_revision)
- format_valid: base False | lora False | qat False
- qat checks: {'expected_format': 'json', 'format_valid': False, 'no_change_case': True, 'no_change_preserved': False}
- gold: `{
  "changed": false,
  "reason": "No genuine defect found.",
  "text": "The generator ran all night in the yard, coughing twice an hour lik`
- qat out: `The generator ran all night in the yard, coughing twice an hour like something that had learned the trick of breathing. By dawn the fuel was`
- note: _human review pending (improved / degraded / unchanged / indeterminate)_

## dsa-revision-007  (focused_revision)
- format_valid: base True | lora True | qat True
- qat checks: {'expected_format': 'prose', 'format_valid': True}
- gold: `She came down to the river the way the year comes down to winter — slowly, and
then all at once — and the water took her name and carried it`
- qat out: `She came down to the river the way the year comes down to winter — slowly, and then all at once — and the water took her name and carried it`
- note: _human review pending (improved / degraded / unchanged / indeterminate)_

## dsa-revision-018  (focused_revision)
- format_valid: base True | lora True | qat True
- qat checks: {'expected_format': 'prose', 'format_valid': True}
- gold: `He comes to the fence and sets both hands on the top rail, close enough that she
could step back and doesn't. She keeps pulling dead heads o`
- qat out: `Their eyes meet across the yard. She looks away. His gaze follows her. Her eyes widen as he steps closer, and their eyes lock again. She wat`
- note: _human review pending (improved / degraded / unchanged / indeterminate)_

## dsa-scene-002  (scene_contract)
- format_valid: base True | lora True | qat True
- qat checks: {'expected_format': 'yaml', 'format_valid': True}
- gold: `viewpoint_character: Odalys (the narration never leaves her).
narrative_perspective: Third person limited, close; locked tightly to her pers`
- qat out: `viewpoint: third person limited tight
location: covered night market under the river bridge, stalls closing down, lamps guttering
scene_obje`
- note: _human review pending (improved / degraded / unchanged / indeterminate)_
