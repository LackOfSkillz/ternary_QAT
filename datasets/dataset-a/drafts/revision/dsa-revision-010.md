---
id: dsa-revision-010
dataset: dataset-a
split: unassigned
review_status: draft
task_type: focused_revision
subtype: trim_one_adjective_stack_not_all
operating_mode: source_bound
difficulty: medium
template_family: revision-adjective-stack-commercial
semantic_cluster: diner-morning-adjective-pileup
style_profile: contemporary-commercial-v1
craft_targets:
  - adjective_economy
protected_craft:
  - the_warm_wry_voice
  - the_useful_specific_adjectives
authorized_changes:
  - trim the single three-plus adjective pile-up to its one or two load-bearing adjectives
unauthorized_changes:
  - deleting every adjective in the passage
  - flattening the wry, warm voice into neutral prose
  - changing the content or the joke
anti_slop_targets:
  - adjective_stacking
anti_slop_risks:
  - imposed_minimalism
  - voice_flattening
  - filter_word_overcorrection
expected_properties:
  - only the one over-stacked noun phrase is trimmed
  - useful single adjectives elsewhere are retained
  - the wry closing line is unchanged
failure_modes:
  - adjective_stacking
  - imposed_minimalism
  - voice_flattening
provenance: hand-written synthetic passage for Dataset A seed batch
source_type: synthetic_internal
license_status: synthetic_internal
teacher_model: none
teacher_terms_status: not_applicable
excluded_from_training: false
---

## Instruction

There is one over-stacked string of adjectives. Trim it to the one or two that do
real work. Leave the other, useful adjectives alone, and keep the wry voice and
the closing line.

## Context

The diner smelled like burnt coffee and yesterday. Nora slid into the cracked
red booth and ordered the sad, tired, greasy, lukewarm, overpriced special
without looking at the menu. The waitress, who had clearly given up on the day at
some point around 6 a.m., wrote nothing down. "Bold choice," she said.

## Gold Response

The diner smelled like burnt coffee and yesterday. Nora slid into the cracked red
booth and ordered the sad, greasy special without looking at the menu. The
waitress, who had clearly given up on the day at some point around 6 a.m., wrote
nothing down. "Bold choice," she said.

## Protected Elements

- The opening line "smelled like burnt coffee and yesterday" (with "burnt").
- The specific "cracked red booth" (useful adjectives — kept).
- The wry waitress beat and the closing line "Bold choice."

## Rejected Response

The diner smelled like coffee. Nora slid into the booth and ordered the special
without looking at the menu. The waitress, who had given up on the day around 6
a.m., wrote nothing down. "Bold choice," she said.

## Rejection Reasons

- `imposed_minimalism` / `voice_flattening`: stripped useful adjectives across the
  whole passage ("burnt," "cracked red," "clearly") — not just the one stack.
- The trim target was the five-adjective pile-up on "special"; the rest carried
  voice and specificity and should have stayed.
- Result reads neutral, losing the wry texture that is the point of the scene.

## Evaluation

- PASS iff only the "sad, tired, greasy, lukewarm, overpriced" stack is trimmed
  (to ~1–2 adjectives) AND "burnt," "cracked red," and the closing line remain.
- FAIL if adjectives elsewhere are removed, or the voice flattens.

## Reviewer Notes

Second explicit overcorrection exemplar. Tier A: adjective counts per noun phrase
are checkable. The trap is the universal rule "adjectives are bad"; the standard
is contextual — trim the pile-up, keep the load-bearing ones.
