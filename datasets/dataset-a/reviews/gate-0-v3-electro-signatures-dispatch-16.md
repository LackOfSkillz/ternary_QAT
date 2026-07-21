# Gate 0 v3 — Electro Phrase-Signature Report (Dispatch 16)

Segmented scan. The Dispatch 15 baseline report
(`gate-0-v3-electro-signatures.md`) is left untouched. Findings are
**REVIEW** only; no phrase proves AI authorship. Short records inflate
per-1,000-word density, so **raw counts and density are both reported** and
records are not ranked by normalized density alone.

## Corrected seed (25)

- **source**: words 2162 | high-risk exact 0 | contextual exact 6 | comparative raw 39 (density 18.0/1k) | em-dash 18 (compound 2) | cluster-windows 0
- **gold**: words 695 | high-risk exact 0 | contextual exact 2 | comparative raw 29 (density 41.7/1k) | em-dash 2 (compound 0) | cluster-windows 0
- **rejected**: words 492 | high-risk exact 0 | contextual exact 4 | comparative raw 20 (density 40.7/1k) | em-dash 0 (compound 0) | cluster-windows 0
- `the way` — source 4, gold 4

## New batch (10)

- **source**: words 378 | high-risk exact 11 | contextual exact 40 | comparative raw 9 (density 23.8/1k) | em-dash 0 (compound 0) | cluster-windows 0
- **gold**: words 476 | high-risk exact 0 | contextual exact 2 | comparative raw 14 (density 29.4/1k) | em-dash 0 (compound 0) | cluster-windows 0
- **rejected**: words 308 | high-risk exact 0 | contextual exact 1 | comparative raw 0 (density 0.0/1k) | em-dash 0 (compound 0) | cluster-windows 0
- `the way` — source 3, gold 3

## Combined draft corpus (35)

- **source**: words 2540 | high-risk exact 11 | contextual exact 46 | comparative raw 48 (density 18.9/1k) | em-dash 18 (compound 2) | cluster-windows 0
- **gold**: words 1171 | high-risk exact 0 | contextual exact 4 | comparative raw 43 (density 36.7/1k) | em-dash 2 (compound 0) | cluster-windows 0
- **rejected**: words 800 | high-risk exact 0 | contextual exact 5 | comparative raw 20 (density 25.0/1k) | em-dash 0 (compound 0) | cluster-windows 0
- `the way` — source 7, gold 7

## Family density — gold (aggregate per 1,000 words)

| family | seed gold | new gold |
|---|---|---|
| comparative_template | 41.7 | 29.4 |
| pressure_metaphor | 14.4 | 10.5 |
| blocking_and_movement | 12.9 | 0.0 |
| gaze_eye_choreography | 0.0 | 12.6 |
| generic_intensifier | 7.2 | 10.5 |
| transition_realization | 7.2 | 10.5 |
| generic_sensory_shorthand | 7.2 | 0.0 |
| abstract_menace_atmosphere | 7.2 | 0.0 |
| embodied_emotion_shorthand | 0.0 | 0.0 |
| dialogue_delivery_template | 0.0 | 0.0 |
| polished_material_shorthand | 0.0 | 0.0 |

## New-batch concentration

- style profiles: {'dark-speculative-v1': 2, 'contemporary-commercial-v1': 2, 'suspense-mystery-v1': 2, 'romantic-emotional-v1': 2, 'lyrical-mythic-v1': 2}
- task families: {'focused_revision': 10}

## New-batch source → gold family deltas

- introduced: {'comparative_template': 5, 'generic_intensifier': 5, 'transition_realization': 5}
- removed: {'embodied_emotion_shorthand': 41, 'generic_sensory_shorthand': 7, 'dialogue_delivery_template': 45, 'pressure_metaphor': 34, 'abstract_menace_atmosphere': 6, 'gaze_eye_choreography': 19}
- The golds should chiefly **remove** families; introductions are small (a single earned reaction, an action beat).

## Highest raw-hit records (gold exact)

- dsa-revision-010: 2
- dsa-revision-019: 1
- dsa-revision-017: 1
- dsa-scene-003: 0
- dsa-scene-002: 0
- dsa-scene-001: 0

## Highest gold density records (with word counts)

- dsa-revision-017: density 288.6 (words 52)
- dsa-revision-010: density 204.0 (words 49)
- dsa-revision-020: density 200.0 (words 45)
- dsa-revision-005: density 173.1 (words 52)
- dsa-revision-001: density 140.3 (words 57)
- dsa-revision-003: density 131.6 (words 38)

## Control checks

- **No-change restraint** (dsa-revision-019): structured no-change gold = True; the earned `looked away` is preserved (source == gold).
- **Author-voice override** (dsa-revision-020): declared `the way...` anaphora preserved in gold (3 occurrences kept intentionally); the generic pressure metaphor was removed.
- **Ordinary-phrase false-positive control**: single ordinary phrases never register as high-risk (see tests); the new golds add 0 high-risk exact hits.

---

**Discipline:** warnings only; no record altered by this report. Corpus artifacts (proper names, setting IDs) are excluded from generic detection. The seed `the way` cluster was reduced 5→4 (Part B); the new batch's 3 `the way` are the author-declared device in dsa-revision-020, not house style.
