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
| word_count | 58 | 37 | -21 | deterministic |
| sentence_count | 3 | 2 | -1 | heuristic |
| avg_sentence_len | 19.3 | 18.5 | -0.8000000000000007 | heuristic |
| sentence_len_variance | 6.24 | 7.5 | 1.2599999999999998 | heuristic |
| em_dash | 0 | 0 | 0 | deterministic |
| semicolon | 0 | 0 | 0 | deterministic |
| colon | 0 | 0 | 0 | deterministic |
| ellipsis | 0 | 0 | 0 | deterministic |
| filter_words | 1 | 1 | 0 | deterministic |
| adverbs_ly | 1 | 1 | 0 | heuristic |
| named_emotion_words | 3 | 1 | -2 | heuristic |
| max_repeated_opening | 1 | 1 | 0 | heuristic |
| quote_chars | 0 | 0 | 0 | heuristic |

- similarity ratio (heuristic): 0.8; changed sentence blocks: 1
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
