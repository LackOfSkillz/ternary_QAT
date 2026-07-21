# Methodology — normalization, families, and tiers

Everything here is **deterministic** and **auditable**. Nothing is silently
discarded; every excluded entry is preserved in
[`normalized/excluded-artifacts.yaml`](normalized/excluded-artifacts.yaml) with a
reason.

## 1. Normalization (`normalize_phrase_lists.py`)

1. Read all three `raw/` files.
2. Lowercase; collapse internal whitespace; strip surrounding whitespace.
3. Drop blank lines.
4. Remove exact duplicates **within** and **across** files, preserving the set of
   source files each surviving phrase came from (`source_files`).
5. Record `n` (token count: 2 for bigrams, 3 for trigrams).
6. Classify each phrase into a **tier** (Part 4) and, where applicable, a
   **phrase family** (Part 3), using only the authored `phrase-families.yaml`
   keyword rules plus the proper-name / malformed heuristics below.
7. Route obvious corpus artifacts to `excluded-artifacts.yaml`; everything else
   to `candidate-phrases.yaml` with `status: candidate`.

### Proper-name detection (→ `corpus_specific_proper_name`)

A phrase is a corpus artifact if it contains any token in the curated
character/setting name set (e.g. `elara`, `kael`, `elias`, `valerius`, `lyra`,
`kaelen`, `isolde`, `theron`, `aris`, `thorne`, `vance`, `silas`, `alistair`,
`finch`, `blackwood`, `aes`, `sedai`), or a title+name pattern (`lord`, `lady`,
`king`, `commander`, `sir`, `named` + name), or a setting identifier containing a
digit (`unit 734`, `unit 7`) or a known setting token (`sector gamma`).

These names are corpus-specific; they must **never** be treated as generic AI
markers. (`sector gamma`, `unit 734`, `aes sedai`, `blackwood manor`, etc.)

### Malformed / truncated detection (→ `malformed_or_truncated`)

A phrase is malformed if it contains an orphaned extraction fragment — chiefly the
mangled remains of "façade": the lone tokens `fa` or `ade` (as in `fa ade`,
`constructed fa`) — or any single-character token.

## 2. Phrase families (`phrase-families.yaml`, authored)

Ten structural families group phrases by the **craft failure** they risk when they
**cluster or repeat** (embodied-emotion shorthand, dialogue-delivery templates,
pressure metaphors, intensifiers, gaze choreography, sensory shorthand,
comparative templates, transition language, abstract menace, polished-material
shorthand). Each family carries `risk_when`, `acceptable_when`, `do_not_flag_when`,
and a `severity`. A phrase can belong to more than one family.

Family assignment is deterministic keyword/token matching against each family's
`match_tokens`. This is a research grouping, not a verdict on any single phrase.

## 3. Classification tiers (Part 4)

- `corpus_artifact` — proper names, malformed entries, setting identifiers,
  extraction noise. (Excluded from generic signature detection.)
- `high_risk_signature` — strongly associated with repetitive model prose in
  context (e.g. `profound silence`, `crushing weight`, `utterly devoid`,
  `voice dropping to`, `a physical weight`).
- `contextual_risk` — ordinary English that becomes suspicious through repetition
  or clustering (e.g. `voice low`, `leaned forward`, `jaw tightened`,
  `metallic tang`, `gaze fixed`).
- `ordinary_phrase` — normal language, weak diagnostic value (e.g. `cold air`,
  `wooden table`, `years ago`).

Tiering rule (deterministic): proper-name/malformed → `corpus_artifact`; else if
the phrase is in a family's curated `high_risk` list → `high_risk_signature`; else
if it matches any family → `contextual_risk`; else → `ordinary_phrase`.

> **No phrase is ever labeled "AI-only."** A tier is a research prior about
> repetition risk, not a claim about the origin of any individual sentence.

## 4. What the scanner actually flags (`scan_phrase_signatures.py`)

The risk is **not** "phrase appears once." The scanner emits `REVIEW` (never
`FAIL`) when patterns **cluster**: family density per 1,000 words, multiple
related phrases within a sliding window, gold **introducing** a family pattern
absent from source, and the same family shared across multiple voices/profiles. It
also reports em-dash **compound** signatures (an em dash co-occurring with an
abstract-interpretation clause and a generic intensifier). Author-supplied
punctuation and single earned phrases are not penalized.
