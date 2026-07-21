# Gate 0 v3 — Electro Phrase-Signature Report (Dataset A seed)

Scanned **25** records. Source, gold, and rejected responses are
reported separately. All findings are **REVIEW** — never automatic
rejection — and no phrase proves AI authorship. Family density is a
heuristic per-1,000-word signal; exact hits are deterministic.

## Corpus totals

- Source high-risk exact hits: **0**  | gold: **0**  | rejected: **0**
- Source contextual exact hits: **6**  | gold: **2**  | rejected: **4**
- Em dashes — source: **18**, gold: **2**; gold em-dash compound signatures: **0**

## Highest-density phrase families (mean per 1,000 words)

| family | source | gold | severity |
|---|---|---|---|
| comparative_template | 30.6 | 27.7 | medium |
| pressure_metaphor | 22.7 | 7.4 | high |
| abstract_menace_atmosphere | 14.7 | 1.7 | high |
| generic_sensory_shorthand | 6.8 | 4.1 | medium |
| blocking_and_movement | 6.0 | 5.4 | medium |
| dialogue_delivery_template | 5.8 | 0.0 | high |
| embodied_emotion_shorthand | 3.7 | 0.0 | medium |
| gaze_eye_choreography | 3.6 | 0.0 | medium |
| generic_intensifier | 3.1 | 1.7 | high |
| transition_realization | 1.4 | 1.7 | medium |
| polished_material_shorthand | 0.0 | 0.0 | medium |

## Source → gold family deltas (aggregate)

- Introduced (gold adds a family pattern absent/thinner in source): {'blocking_and_movement': 5, 'generic_intensifier': 5, 'transition_realization': 5}
- Removed (gold reduces a source family pattern): {'pressure_metaphor': 25, 'generic_sensory_shorthand': 5, 'comparative_template': 10, 'gaze_eye_choreography': 10, 'dialogue_delivery_template': 20, 'embodied_emotion_shorthand': 15, 'blocking_and_movement': 10, 'abstract_menace_atmosphere': 17, 'generic_intensifier': 10, 'transition_realization': 5}
- REVIEW when a gold **introduces** a high-severity family pattern; a gold that **removes** one is doing anti-slop work.

## Profile concentrations (mean gold family density)

- **contemporary-commercial-v1** (2 rec): generic_sensory_shorthand 51.0, comparative_template 51.0
- **dark-speculative-v1** (2 rec): comparative_template 81.8, pressure_metaphor 43.9
- **lyrical-mythic-v1** (2 rec): comparative_template 73.0
- **none** (15 rec): blocking_and_movement 3.9, transition_realization 2.9, generic_intensifier 2.9
- **romantic-emotional-v1** (2 rec): comparative_template 140.0
- **suspense-mystery-v1** (2 rec): pressure_metaphor 48.1, blocking_and_movement 38.5
- REVIEW when multiple profiles share the same high-severity family (house-style collapse risk).

## `the way` and comparative frames

- Source `the way` occurrences in **5** records: dsa-revision-001, dsa-revision-003, dsa-revision-004, dsa-revision-007, dsa-revision-008
- Gold `the way` occurrences in **5** records: dsa-revision-001, dsa-revision-003, dsa-revision-004, dsa-revision-007, dsa-revision-008
- Records with any comparative_template family density (source): 9
- REVIEW: the comparative frame (`the way ...`, `like a ...`) is a known recurring signature in this corpus; watch for it clustering across records.

## Highest-density records (gold, summed family density)

- dsa-revision-003: 216.2
- dsa-revision-010: 204.0
- dsa-revision-005: 173.1
- dsa-revision-001: 140.3
- dsa-boundary-002: 129.3
- dsa-revision-002: 111.1
- dsa-revision-007: 84.7
- dsa-revision-004: 63.8

## Per-record detail

### dsa-canon-001  (none, canon_extraction)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 2/0 (gold compound: 0)
- introduced families: none | removed: {'pressure_metaphor': 5}

### dsa-canon-002  (none, canon_extraction)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 2/0 (gold compound: 0)
- introduced families: none | removed: none

### dsa-canon-003  (none, canon_extraction)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 1/0 (gold compound: 0)
- introduced families: none | removed: none

### dsa-canon-004  (none, canon_extraction)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 1/0 (gold compound: 0)
- introduced families: none | removed: {'generic_sensory_shorthand': 5, 'comparative_template': 5}

### dsa-canon-005  (none, canon_extraction)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 1/0 (gold compound: 0)
- introduced families: none | removed: none

### dsa-constraint-001  (none, constraint_check)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: none | removed: {'gaze_eye_choreography': 10}

### dsa-constraint-002  (none, constraint_check)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: none | removed: {'dialogue_delivery_template': 5}

### dsa-constraint-003  (none, constraint_check)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: none | removed: none

### dsa-constraint-004  (none, constraint_check)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 1/0 (gold compound: 0)
- introduced families: none | removed: {'embodied_emotion_shorthand': 5, 'blocking_and_movement': 5}

### dsa-constraint-005  (none, constraint_check)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: none | removed: {'embodied_emotion_shorthand': 10, 'blocking_and_movement': 5}

### dsa-boundary-001  (none, fiction_boundary)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: {'blocking_and_movement': 5} | removed: {'pressure_metaphor': 5, 'abstract_menace_atmosphere': 5}

### dsa-boundary-002  (none, fiction_boundary)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: {'generic_intensifier': 5, 'transition_realization': 5} | removed: none

### dsa-revision-001  (dark-speculative-v1, focused_revision)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: none | removed: {'abstract_menace_atmosphere': 5}

### dsa-revision-002  (dark-speculative-v1, focused_revision)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: none | removed: none

### dsa-revision-003  (romantic-emotional-v1, focused_revision)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: none | removed: none

### dsa-revision-004  (romantic-emotional-v1, focused_revision)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: none | removed: {'pressure_metaphor': 5}

### dsa-revision-005  (suspense-mystery-v1, focused_revision)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: none | removed: {'abstract_menace_atmosphere': 7}

### dsa-revision-006  (suspense-mystery-v1, focused_revision)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: none | removed: none

### dsa-revision-007  (lyrical-mythic-v1, focused_revision)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 2/2 (gold compound: 0)
- introduced families: none | removed: none

### dsa-revision-008  (lyrical-mythic-v1, focused_revision)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: none | removed: none

### dsa-revision-009  (contemporary-commercial-v1, focused_revision)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: none | removed: {'pressure_metaphor': 5, 'comparative_template': 5}

### dsa-revision-010  (contemporary-commercial-v1, focused_revision)
- exact high-risk: source [] | gold []
- gold contextual exact: ['like burnt', 'smelled like']
- em dashes source/gold: 0/0 (gold compound: 0)
- introduced families: none | removed: none

### dsa-scene-001  (none, scene_contract)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 3/0 (gold compound: 0)
- introduced families: none | removed: {'generic_intensifier': 5, 'transition_realization': 5}

### dsa-scene-002  (none, scene_contract)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 3/0 (gold compound: 0)
- introduced families: none | removed: {'dialogue_delivery_template': 10, 'pressure_metaphor': 5}

### dsa-scene-003  (none, scene_contract)
- exact high-risk: source [] | gold []
- gold contextual exact: []
- em dashes source/gold: 2/0 (gold compound: 0)
- introduced families: none | removed: {'dialogue_delivery_template': 5, 'generic_intensifier': 5}

---

**Discipline:** warnings only. Corpus artifacts (proper names, malformed
entries, setting IDs) are excluded from generic detection. Ordinary
phrases are never high risk merely for appearing once. Author-supplied
punctuation and single earned phrases are not penalized.
