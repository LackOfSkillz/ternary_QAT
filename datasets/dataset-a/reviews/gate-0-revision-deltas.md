# Gate 0 — Revision Delta Report

Deterministic evidence for Gate 1 human review of the 10 focused-
revision records. This report **does not approve or reject** anything.
Metrics are labeled deterministic | heuristic | unavailable.

**Authorized-axis awareness (heuristic):** when a record explicitly
authorizes combining or varying sentences, low sentence-sequence
similarity is EXPECTED and is *not* flagged as off-axis. The scan still
flags unauthorized additions (new imagery/facts/interpretation, em
dashes/colons not named as targets, protected-element loss, and net new
words under a `none` invention budget). It does not judge prose quality.

## dsa-revision-001  (dark-speculative-v1)

- **Intended craft target:** significant_detail, concrete_diction
- **Protected craft:** flat_affect, single_sustained_image
- **Authorized changes:** replace the one generic-atmosphere sentence with a specific, slightly-wrong sensory detail
- **Invention budget:** bounded

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 48 | 57 | 9 | deterministic |
| sentence_count | 4 | 4 | 0 | heuristic |
| avg_sentence_len | 12.0 | 14.2 | 2.1999999999999993 | heuristic |
| sentence_len_variance | 5.34 | 6.26 | 0.9199999999999999 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 1 | 2 | 1 | heuristic |
| named_emotion_words | 1 | 0 | -1 | heuristic |
| max_repeated_opening | 1 | 1 | 0 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 0.75; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:** none

**Teacher-style signatures (heuristic):** none

**Machine note:** No off-axis flags. Target: significant_detail, concrete_diction. Edit similarity 0.75.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-002  (dark-speculative-v1)

- **Intended craft target:** editorial_restraint
- **Protected craft:** existing_sentence_rhythm, existing_concrete_detail
- **Authorized changes:** only fix a genuine error if one exists
- **Invention budget:** none

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 45 | 45 | 0 | deterministic |
| sentence_count | 3 | 3 | 0 | heuristic |
| avg_sentence_len | 15.0 | 15.0 | 0.0 | heuristic |
| sentence_len_variance | 6.48 | 6.48 | 0.0 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 0 | 0 | 0 | heuristic |
| named_emotion_words | 0 | 0 | 0 | heuristic |
| max_repeated_opening | 1 | 1 | 0 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 1.0; changed sentence blocks: 0
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:** none

**Teacher-style signatures (heuristic):** none

**Machine note:** No off-axis flags. Target: editorial_restraint. Edit similarity 1.0.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-003  (romantic-emotional-v1)

- **Intended craft target:** trust_the_reader, psychic_distance
- **Protected craft:** one_earned_named_emotion, close_free_indirect_distance
- **Authorized changes:** delete the sentence that re-explains a feeling already shown
- **Invention budget:** none

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 59 | 38 | -21 | deterministic |
| sentence_count | 4 | 3 | -1 | heuristic |
| avg_sentence_len | 14.8 | 12.7 | -2.1000000000000014 | heuristic |
| sentence_len_variance | 8.93 | 9.43 | 0.5 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 1 | 1 | 0 | deterministic |
| adverbs_ly | 1 | 1 | 0 | heuristic |
| named_emotion_words | 3 | 1 | -2 | heuristic |
| max_repeated_opening | 2 | 2 | 0 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 0.857; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:**
- ⚠ named-emotion word count dropped while emotion naming is protected

**Teacher-style signatures (heuristic):** none

**Machine note:** 1 off-axis flag(s). Target: trust_the_reader, psychic_distance.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-004  (romantic-emotional-v1)

- **Intended craft target:** significant_detail, concrete_diction
- **Protected craft:** warm_close_distance, the_couples_specific_history
- **Authorized changes:** replace the generic mood sentence with one concrete detail specific to these two people
- **Invention budget:** bounded

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 47 | 47 | 0 | deterministic |
| sentence_count | 4 | 4 | 0 | heuristic |
| avg_sentence_len | 11.8 | 11.8 | 0.0 | heuristic |
| sentence_len_variance | 5.97 | 5.97 | 0.0 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 0 | 0 | 0 | heuristic |
| named_emotion_words | 0 | 0 | 0 | heuristic |
| max_repeated_opening | 1 | 2 | 1 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 0.75; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:** none

**Teacher-style signatures (heuristic):** none

**Machine note:** No off-axis flags. Target: significant_detail, concrete_diction. Edit similarity 0.75.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-005  (suspense-mystery-v1)

- **Intended craft target:** significant_detail, concrete_evidence
- **Protected craft:** lean_forward_momentum, the_open_scene_question
- **Authorized changes:** replace the generic mood sentence with one concrete, checkable piece of evidence
- **Invention budget:** bounded

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 46 | 52 | 6 | deterministic |
| sentence_count | 5 | 5 | 0 | heuristic |
| avg_sentence_len | 9.2 | 10.4 | 1.200000000000001 | heuristic |
| sentence_len_variance | 4.53 | 6.34 | 1.8099999999999996 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 1 | 0 | -1 | heuristic |
| named_emotion_words | 0 | 0 | 0 | heuristic |
| max_repeated_opening | 3 | 3 | 0 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 0.8; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:** none

**Teacher-style signatures (heuristic):** none

**Machine note:** No off-axis flags. Target: significant_detail, concrete_evidence. Edit similarity 0.8.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-006  (suspense-mystery-v1)

- **Intended craft target:** sentence_length_variance, turn_length_variance
- **Protected craft:** forward_momentum, the_short_punch_at_the_beat
- **Authorized changes:** vary sentence length so the rhythm is not uniformly choppy, combine two or three clipped sentences where it does not blunt tension
- **Invention budget:** none

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 45 | 47 | 2 | deterministic |
| sentence_count | 11 | 6 | -5 | heuristic |
| avg_sentence_len | 4.1 | 7.8 | 3.7 | heuristic |
| sentence_len_variance | 1.73 | 6.23 | 4.5 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 0 | 0 | 0 | heuristic |
| named_emotion_words | 0 | 0 | 0 | heuristic |
| max_repeated_opening | 6 | 3 | -3 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 0.353; changed sentence blocks: 3
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:** none

**Teacher-style signatures (heuristic):** none

**Machine note:** No off-axis flags. Target: sentence_length_variance, turn_length_variance. Edit similarity 0.353.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-007  (lyrical-mythic-v1)

- **Intended craft target:** metaphor_coherence
- **Protected craft:** ornate_earned_syntax, the_sustained_river_image, deliberate_cadence
- **Authorized changes:** repair only the one incoherent (mixed) metaphor so the central image stays coherent
- **Invention budget:** none

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 58 | 59 | 1 | deterministic |
| sentence_count | 2 | 2 | 0 | heuristic |
| avg_sentence_len | 29.0 | 29.5 | 0.5 | heuristic |
| sentence_len_variance | 9.0 | 8.5 | -0.5 | heuristic |
| em_dash | 2 | 2 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 1 | 1 | 0 | heuristic |
| named_emotion_words | 1 | 1 | 0 | heuristic |
| max_repeated_opening | 1 | 1 | 0 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 0.5; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:** none

**Teacher-style signatures (heuristic):** none

**Machine note:** No off-axis flags. Target: metaphor_coherence. Edit similarity 0.5.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-008  (lyrical-mythic-v1)

- **Intended craft target:** earn_the_abstraction
- **Protected craft:** deliberate_anaphora, the_litany_rhythm
- **Authorized changes:** delete the one hollow, profound-sounding sentence that says nothing
- **Invention budget:** none

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 64 | 49 | -15 | deterministic |
| sentence_count | 5 | 4 | -1 | heuristic |
| avg_sentence_len | 12.8 | 12.2 | -0.6000000000000014 | heuristic |
| sentence_len_variance | 1.33 | 0.83 | -0.5000000000000001 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 0 | 0 | 0 | heuristic |
| named_emotion_words | 0 | 0 | 0 | heuristic |
| max_repeated_opening | 4 | 4 | 0 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 0.889; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:** none

**Teacher-style signatures (heuristic):** none

**Machine note:** No off-axis flags. Target: earn_the_abstraction. Edit similarity 0.889.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-009  (contemporary-commercial-v1)

- **Intended craft target:** subtext, naturalistic_dialogue
- **Protected craft:** the_scene_outcome, each_character_position
- **Authorized changes:** rewrite the on-the-nose lines so the feeling is implied through indirection or action
- **Invention budget:** bounded

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 59 | 50 | -9 | deterministic |
| sentence_count | 4 | 7 | 3 | heuristic |
| avg_sentence_len | 14.8 | 7.1 | -7.700000000000001 | heuristic |
| sentence_len_variance | 7.08 | 5.62 | -1.46 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 2 | 1 | -1 | heuristic |
| named_emotion_words | 4 | 0 | -4 | heuristic |
| max_repeated_opening | 1 | 1 | 0 | heuristic |
| quote_chars | 10 | 12 | 2 | heuristic |

- similarity ratio (heuristic): 0.0; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:** none

**Teacher-style signatures (heuristic):** short aphoristic-style ending changed/added (review)

**Machine note:** No off-axis flags. Target: subtext, naturalistic_dialogue. Edit similarity 0.0.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-010  (contemporary-commercial-v1)

- **Intended craft target:** adjective_economy
- **Protected craft:** the_warm_wry_voice, the_useful_specific_adjectives
- **Authorized changes:** trim the single three-plus adjective pile-up to its one or two load-bearing adjectives
- **Invention budget:** none

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 52 | 49 | -3 | deterministic |
| sentence_count | 4 | 4 | 0 | heuristic |
| avg_sentence_len | 13.0 | 12.2 | -0.8000000000000007 | heuristic |
| sentence_len_variance | 7.18 | 6.42 | -0.7599999999999998 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 1 | 1 | 0 | heuristic |
| named_emotion_words | 1 | 1 | 0 | heuristic |
| max_repeated_opening | 2 | 2 | 0 | heuristic |
| quote_chars | 2 | 2 | 0 | heuristic |

- similarity ratio (heuristic): 0.75; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:** none

**Teacher-style signatures (heuristic):** none

**Machine note:** No off-axis flags. Target: adjective_economy. Edit similarity 0.75.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-011  (dark-speculative-v1)

- **Intended craft target:** significant_detail, show_dont_tell
- **Protected craft:** flat_low_affect, the_failing_hatch_stakes
- **Authorized changes:** replace the generic embodied/sensory fear shorthand with concrete, character-specific behavior or consequence
- **Invention budget:** bounded

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 36 | 60 | 24 | deterministic |
| sentence_count | 2 | 3 | 1 | heuristic |
| avg_sentence_len | 18.0 | 20.0 | 2.0 | heuristic |
| sentence_len_variance | 7.0 | 8.29 | 1.2899999999999991 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 2 | 2 | deterministic |
| adverbs_ly | 0 | 0 | 0 | heuristic |
| named_emotion_words | 1 | 0 | -1 | heuristic |
| max_repeated_opening | 1 | 1 | 0 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 0.4; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:**
- ⚠ large edit distance (similarity 0.4) on a focused/minimal task

**Teacher-style signatures (heuristic):** none

**Machine note:** 1 off-axis flag(s). Target: significant_detail, show_dont_tell.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-012  (contemporary-commercial-v1)

- **Intended craft target:** concrete_evidence, naturalistic_understatement
- **Protected craft:** the_dry_wry_register, the_scene_outcome_forced_reassurance
- **Authorized changes:** replace the generic abstraction ("oppressive silence," "voice barely audible") with concrete observable evidence and action
- **Invention budget:** bounded

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 25 | 28 | 3 | deterministic |
| sentence_count | 2 | 3 | 1 | heuristic |
| avg_sentence_len | 12.5 | 9.3 | -3.1999999999999993 | heuristic |
| sentence_len_variance | 1.5 | 2.05 | 0.5499999999999998 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 1 | 1 | 0 | heuristic |
| named_emotion_words | 0 | 0 | 0 | heuristic |
| max_repeated_opening | 1 | 1 | 0 | heuristic |
| quote_chars | 2 | 2 | 0 | heuristic |

- similarity ratio (heuristic): 0.0; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:**
- ⚠ large edit distance (similarity 0.0) on a focused/minimal task

**Teacher-style signatures (heuristic):** none

**Machine note:** 1 off-axis flag(s). Target: concrete_evidence, naturalistic_understatement.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-013  (suspense-mystery-v1)

- **Intended craft target:** earn_one_physical_reaction, show_through_action
- **Protected craft:** first_person_close_distance, the_discovery_beat
- **Authorized changes:** keep one earned physical reaction and convert the rest of the cluster into action or observation
- **Invention budget:** none

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 28 | 44 | 16 | deterministic |
| sentence_count | 3 | 2 | -1 | heuristic |
| avg_sentence_len | 9.3 | 22.0 | 12.7 | heuristic |
| sentence_len_variance | 5.79 | 13.0 | 7.21 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 1 | 0 | -1 | deterministic |
| adverbs_ly | 0 | 0 | 0 | heuristic |
| named_emotion_words | 0 | 0 | 0 | heuristic |
| max_repeated_opening | 2 | 1 | -1 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 0.0; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:**
- ⚠ large edit distance (similarity 0.0) on a focused/minimal task
- ⚠ word count grew by 16 under a 'none' invention budget (possible added material)
- ⚠ sentence-length variance shifted notably though not the named target

**Teacher-style signatures (heuristic):** none

**Machine note:** 3 off-axis flag(s). Target: earn_one_physical_reaction, show_through_action.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-014  (romantic-emotional-v1)

- **Intended craft target:** earn_one_physical_reaction, carry_emotion_in_subtext
- **Protected craft:** warm_close_distance, the_withheld_answer_outcome
- **Authorized changes:** keep one earned physical reaction and move the rest of the cluster into action, dialogue, or subtext
- **Invention budget:** bounded

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 34 | 52 | 18 | deterministic |
| sentence_count | 3 | 3 | 0 | heuristic |
| avg_sentence_len | 11.3 | 17.3 | 6.0 | heuristic |
| sentence_len_variance | 4.78 | 3.3 | -1.4800000000000004 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 0 | 1 | 1 | heuristic |
| named_emotion_words | 0 | 0 | 0 | heuristic |
| max_repeated_opening | 1 | 1 | 0 | heuristic |
| quote_chars | 0 | 2 | 2 | heuristic |

- similarity ratio (heuristic): 0.0; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:** none

**Teacher-style signatures (heuristic):** none

**Machine note:** No off-axis flags. Target: earn_one_physical_reaction, carry_emotion_in_subtext. Edit similarity 0.0.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-015  (contemporary-commercial-v1)

- **Intended craft target:** let_content_and_action_carry_tone, keep_speaker_clarity
- **Protected craft:** three_speaker_attribution, the_scene_outcome_draw_straws
- **Authorized changes:** remove the "voice + modifier" delivery tags and let dialogue and action carry tone, keep enough attribution that three speakers stay clear
- **Invention budget:** bounded

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 36 | 55 | 19 | deterministic |
| sentence_count | 5 | 6 | 1 | heuristic |
| avg_sentence_len | 7.2 | 9.2 | 1.9999999999999991 | heuristic |
| sentence_len_variance | 2.48 | 8.01 | 5.529999999999999 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 1 | 0 | -1 | heuristic |
| named_emotion_words | 0 | 0 | 0 | heuristic |
| max_repeated_opening | 1 | 1 | 0 | heuristic |
| quote_chars | 10 | 8 | -2 | heuristic |

- similarity ratio (heuristic): 0.0; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:**
- ⚠ large edit distance (similarity 0.0) on a focused/minimal task
- ⚠ sentence-length variance shifted notably though not the named target

**Teacher-style signatures (heuristic):** short aphoristic-style ending changed/added (review)

**Machine note:** 2 off-axis flag(s). Target: let_content_and_action_carry_tone, keep_speaker_clarity.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-016  (suspense-mystery-v1)

- **Intended craft target:** carry_menace_in_action, keep_speaker_clarity
- **Protected craft:** the_power_dynamic, the_terse_tension
- **Authorized changes:** remove the "voice + modifier" tags and let action and content carry the menace, keep enough attribution/anchoring that the two speakers stay clear
- **Invention budget:** bounded

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 39 | 46 | 7 | deterministic |
| sentence_count | 5 | 4 | -1 | heuristic |
| avg_sentence_len | 7.8 | 11.5 | 3.7 | heuristic |
| sentence_len_variance | 2.04 | 4.61 | 2.5700000000000003 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 1 | 0 | -1 | heuristic |
| named_emotion_words | 0 | 0 | 0 | heuristic |
| max_repeated_opening | 1 | 1 | 0 | heuristic |
| quote_chars | 8 | 8 | 0 | heuristic |

- similarity ratio (heuristic): 0.222; changed sentence blocks: 2
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:**
- ⚠ large edit distance (similarity 0.222) on a focused/minimal task

**Teacher-style signatures (heuristic):** three-part (tricolon) construction added

**Machine note:** 1 off-axis flag(s). Target: carry_menace_in_action, keep_speaker_clarity.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-017  (dark-speculative-v1)

- **Intended craft target:** concrete_evidence, earn_one_metaphor
- **Protected craft:** the_decisions_gravity, the_flat_controlled_register
- **Authorized changes:** replace the generic weight/pressure abstractions with concrete scene evidence, keep at most one earned metaphor
- **Invention budget:** bounded

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 40 | 52 | 12 | deterministic |
| sentence_count | 3 | 4 | 1 | heuristic |
| avg_sentence_len | 13.3 | 13.0 | -0.3000000000000007 | heuristic |
| sentence_len_variance | 1.25 | 5.79 | 4.54 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 0 | 1 | 1 | heuristic |
| named_emotion_words | 0 | 0 | 0 | heuristic |
| max_repeated_opening | 2 | 1 | -1 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 0.0; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:**
- ⚠ large edit distance (similarity 0.0) on a focused/minimal task
- ⚠ sentence-length variance shifted notably though not the named target

**Teacher-style signatures (heuristic):** none

**Machine note:** 2 off-axis flag(s). Target: concrete_evidence, earn_one_metaphor.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-018  (romantic-emotional-v1)

- **Intended craft target:** motivated_action_over_gaze, significant_object_interaction
- **Protected craft:** the_power_dynamic_he_approaches_she_holds, the_scene_outcome_a_thaw
- **Authorized changes:** keep at most one meaningful look and replace the rest of the gaze choreography with motivated action or object interaction
- **Invention budget:** bounded

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 38 | 45 | 7 | deterministic |
| sentence_count | 5 | 2 | -3 | heuristic |
| avg_sentence_len | 7.6 | 22.5 | 14.9 | heuristic |
| sentence_len_variance | 4.13 | 0.5 | -3.63 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 0 | 0 | 0 | heuristic |
| named_emotion_words | 0 | 0 | 0 | heuristic |
| max_repeated_opening | 2 | 1 | -1 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 0.0; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:**
- ⚠ large edit distance (similarity 0.0) on a focused/minimal task

**Teacher-style signatures (heuristic):** none

**Machine note:** 1 off-axis flag(s). Target: motivated_action_over_gaze, significant_object_interaction.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-019  (lyrical-mythic-v1)

- **Intended craft target:** editorial_restraint, respect_earned_phrase
- **Protected craft:** the_single_earned_looked_away, the_incantatory_cadence
- **Authorized changes:** only change something if there is a genuine defect; there is none here
- **Invention budget:** none

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 49 | 49 | 0 | deterministic |
| sentence_count | 3 | 3 | 0 | heuristic |
| avg_sentence_len | 16.3 | 16.3 | 0.0 | heuristic |
| sentence_len_variance | 7.93 | 7.93 | 0.0 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 1 | 1 | 0 | deterministic |
| adverbs_ly | 0 | 0 | 0 | heuristic |
| named_emotion_words | 0 | 0 | 0 | heuristic |
| max_repeated_opening | 1 | 1 | 0 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 1.0; changed sentence blocks: 0
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:** none

**Teacher-style signatures (heuristic):** none

**Machine note:** No off-axis flags. Target: editorial_restraint, respect_earned_phrase. Edit similarity 1.0.

**Reviewer decision (Gate 1):** _pending_

---

## dsa-revision-020  (lyrical-mythic-v1)

- **Intended craft target:** apply_voice_precedence, remove_only_genuine_generic_slop
- **Protected craft:** the_declared_anaphoric_the_way_device, the_second_person_incantatory_voice
- **Authorized changes:** remove only the genuinely generic phrase that is NOT the author's declared device
- **Invention budget:** none

| metric | source | gold | delta | kind |
|---|---|---|---|---|
| word_count | 53 | 45 | -8 | deterministic |
| sentence_count | 4 | 3 | -1 | heuristic |
| avg_sentence_len | 13.2 | 15.0 | 1.8000000000000007 | heuristic |
| sentence_len_variance | 3.34 | 1.63 | -1.71 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 0 | 0 | 0 | deterministic |
| adverbs_ly | 0 | 0 | 0 | heuristic |
| named_emotion_words | 0 | 0 | 0 | heuristic |
| max_repeated_opening | 3 | 3 | 0 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 0.857; changed sentence blocks: 1
- adjective_estimate: unavailable (no POS tagger)

**Potential off-axis flags:** none

**Teacher-style signatures (heuristic):** none

**Machine note:** No off-axis flags. Target: apply_voice_precedence, remove_only_genuine_generic_slop. Edit similarity 0.857.

**Reviewer decision (Gate 1):** _pending_

---
