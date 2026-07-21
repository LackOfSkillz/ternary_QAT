# Gate 0 v2 — Corpus Signature Report

Scanned **35** records (source + gold). These scans
expose **monoculture risk** across the corpus. Thresholds emit **REVIEW**,
never FAIL — they do not adjudicate literary quality. Metrics are labeled
deterministic | heuristic.

### Pattern: `the way ...`  (deterministic)
- Count (records): **5**  | Threshold: 3  | Status: **REVIEW**
- Profiles affected: dark-speculative-v1, lyrical-mythic-v1, romantic-emotional-v1
- Records: dsa-revision-001 (source+gold); dsa-revision-004 (source+gold); dsa-revision-007 (source+gold); dsa-revision-008 (source+gold); dsa-revision-020 (source+gold)

### Pattern: `not X, but Y`  (deterministic)
- Count (records): **0**  | Threshold: 2  | Status: **OK**
- Profiles affected: n/a
- Records: none

### Pattern: `tricolon (X, Y, and Z)`  (deterministic)
- Count (records): **1**  | Threshold: 3  | Status: **OK**
- Records: dsa-revision-016 (source=0 gold=1)

### Em-dash frequency  (deterministic)
- Total em dashes — source: **18**, gold: **2**
- By family (gold): {'canon_extraction': 0, 'constraint_check': 0, 'fiction_boundary': 0, 'focused_revision': 2, 'scene_contract': 0}
- By family (source): {'canon_extraction': 7, 'constraint_check': 1, 'fiction_boundary': 0, 'focused_revision': 2, 'scene_contract': 8}
- By profile (gold): {'none': 0, 'dark-speculative-v1': 0, 'romantic-emotional-v1': 0, 'suspense-mystery-v1': 0, 'lyrical-mythic-v1': 2, 'contemporary-commercial-v1': 0}
- Status: **REVIEW** — confirm em dashes are earned per profile, not a teacher tic imported into golds.

### Poised final-image endings  (heuristic proxy)
- **Source** passages ending on a short (<=12-word) non-dialogue image: **6**  | Threshold: 4  | Status: **REVIEW**
- Source records: dsa-canon-001, dsa-canon-002, dsa-canon-004, dsa-revision-005, dsa-revision-006, dsa-revision-020
    - dsa-canon-001: “On the desk lay a single unopened envelope with her name misspelled.”
    - dsa-canon-002: “Yours, Edith.”
    - dsa-canon-004: “She waited, and the waiting told her nothing.”
    - dsa-revision-005: “She hadn't touched the door.”
    - dsa-revision-006: “The light moved.”
    - dsa-revision-020: “A crushing weight of silence filled the temple.”
- **Gold** responses with the same pattern: **2** (dsa-revision-005, dsa-revision-006)
- Explanation: the poised-closing-image habit is concentrated in the **source** passages and largely carries into the golds; a high source concentration is a monoculture signal for Gary's Gate review.

### Repeated sentence openings  (heuristic)
- “the…” opens 11 gold sentences across 7 records: dsa-revision-001, dsa-revision-002, dsa-revision-005, dsa-revision-006, dsa-revision-010, dsa-revision-013, dsa-revision-017
- “she…” opens 9 gold sentences across 8 records: dsa-revision-003, dsa-revision-005, dsa-revision-007, dsa-revision-011, dsa-revision-014, dsa-revision-016, dsa-revision-018, dsa-revision-019
- “i…” opens 6 gold sentences across 5 records: dsa-boundary-001, dsa-boundary-002, dsa-revision-009, dsa-revision-013, dsa-revision-016
- “he…” opens 5 gold sentences across 3 records: dsa-revision-004, dsa-revision-006, dsa-revision-018
- “her…” opens 3 gold sentences across 3 records: dsa-boundary-002, dsa-revision-001, dsa-revision-011

### Cross-record shared 4-grams (gold)  (deterministic)
- Distinct shared 4-grams across different records: **1**  | Status: **REVIEW**
    - “she looked at the” — dsa-revision-014, dsa-revision-016

### Cross-profile gold similarity  (heuristic)
- Pairs of DIFFERENT-profile golds above 0.55 similarity: **0**  | Status: **OK**
- Explanation: high similarity between golds meant to differ by profile signals the same repair leaking across voices (SIREP-collapse risk).

---

**Discipline:** REVIEW flags are prompts for the Gate 1/2/3 human and
model reviewers. They surface repetition to be judged, not defects to be
auto-fixed. Deterministic counts are exact; heuristic proxies approximate
patterns a tool cannot fully understand.
