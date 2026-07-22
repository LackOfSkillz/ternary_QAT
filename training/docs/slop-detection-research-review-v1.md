# Slop-Detection Research Review (v1)

**Project:** LineWright Diagnostic Battery (LWDB)
**Dispatch:** 23
**Companion document:** [LWDB Architecture Spec](./linewright-diagnostic-battery-architecture-v1.md)
**Status:** Research review — guides implement-now vs. defer decisions. No code, no thresholds ratified.

---

## 1. Purpose and caveats

### Purpose

LWDB is a diagnostic evaluation battery for a small fiction-writing model. This document
surveys candidate methods for detecting **"slop"** — a bundle of undesirable writing
behaviors including verbatim and near-verbatim repetition, semantic redundancy,
stock-phrase concentration, voice flattening, generic explanatory endings ("And so, in
the end, ..."), and corpus-level sameness across many generations. The review exists to
decide, for Dispatch 23, which detection methods to **implement now**, which to stub as
**interfaces only**, which to hold for **calibration**, which need **more research**, and
which to **reject** outright.

### Caveats (read before using any method below)

- **Slop detection is not a solved problem.** Every method here is partial. None is a
  ground-truth oracle for writing quality.
- **This is NOT an AI-authorship detector.** LWDB must never claim to determine whether a
  text was written by a machine or a human. That is a different, unreliable task (see
  §5), and conflating the two will produce false and harmful verdicts.
- **A single scalar score is never sufficient.** Slop is multi-dimensional. Collapsing it
  to one number hides the evidence a reviewer needs and invites Goodharting. Every
  detector must surface **evidence spans**, not just a magnitude.
- **The following must NOT be flagged as slop:**
  - *Deliberate rhetorical repetition* (anaphora, refrains, incantatory structure).
  - *Concise, low-diversity prose* that is intentionally spare.
  - *Lyrical or unusual syntax* that departs from "clean expository" norms on purpose.
  - *Genre-appropriate motifs and recurring imagery* that carry a theme forward.

A detector that punishes these is worse than no detector: it pushes the model toward
flatter, safer, more generic prose — the exact failure mode LWDB is meant to catch.

---

## 2. Method-family survey

Each claim below is tagged with exactly one evidentiary status:

- `source_supported` — directly supported by a cited paper.
- `engineering_inference` — a reasonable design extrapolation, **not** claimed by any cited paper.
- `unvalidated_hypothesis` — plausible but untested by us and uncited.
- `rejected_approach` — surveyed and recommended against for LWDB's slop use.

The cited papers below are the **only** external sources for this review. No other
citations should be added, and none of the papers' claims should be overstated.

### 2.1 Repetition-aware evaluation (RAP)

RAP — *Repetition-Aware ... Performance* — argues that repetition should be folded
**into** the performance/quality evaluation itself rather than treated as an incidental
artifact measured on the side. `[source_supported]` The paper's contribution is the
framing that a metric which ignores repetition can reward degenerate but "fluent"
output. For LWDB, the transferable idea is that our repetition layer should be a
first-class axis of the diagnostic, weighted alongside other signals, not a footnote.
`[engineering_inference]` RAP does **not** supply thresholds calibrated for small
fiction models, and we should not pretend it does. `[engineering_inference]`
Source: aclanthology.org/2025.naacl-long.69

### 2.2 Local-coherence disruption detection (TEXT-CAKE)

TEXT-CAKE studies detection of **subtle local-coherence breaks** — small logical or
referential discontinuities between adjacent spans — and finds this task hard and
strongly **genre-sensitive**: what reads as a coherence break in one genre is normal in
another. `[source_supported]` The lesson for LWDB is cautionary: automated
local-coherence checks are unreliable enough that they belong in the *research-further*
bucket, not the deterministic layer. `[engineering_inference]` We hypothesize that some
slop endings (abrupt generic summaries) might correlate with detectable coherence
shifts, but that link is untested here. `[unvalidated_hypothesis]`
Source: aclanthology.org/2025.coling-main.296

### 2.3 Multi-dimensional linguistic diversity

*Benchmarking Linguistic Diversity of Large Language Models* measures diversity across
**lexical, syntactic, and semantic** dimensions and shows that these do not reduce to a
single statistic — a model can look diverse lexically while being syntactically or
semantically repetitive. `[source_supported]` This directly supports LWDB's design
principle that no one diversity number is a quality verdict. `[source_supported]` The
inference that low diversity on any single axis constitutes "slop" is **ours**, not the
paper's, and remains unvalidated for fiction. `[engineering_inference]`
Source: arxiv.org/abs/2412.10271

### 2.4 Checklist-based LLM evaluation (CheckEval)

CheckEval decomposes broad, subjective quality judgments into **specific binary checks**,
reporting improved interpretability and reliability versus asking a model for one holistic
score. `[source_supported]` This is the backbone for LWDB's reviewer checklist: instead of
"rate the slop 1–10," we ask discrete yes/no questions ("Does the ending restate the theme
in generic terms?"). `[source_supported]` Whether a *small* fiction model can itself serve
as a reliable checklist judge is not established by the paper and is treated as
open. `[engineering_inference]`
Source: arxiv.org/abs/2403.18771

### 2.5 Text-diversity standardization and cross-document templating

*Standardizing the Measurement of Text Diversity* argues for standardized diversity
measurement and highlights **cross-document sameness** — canned structures and templated
scaffolding reused across many outputs — as a distinct phenomenon from within-document
repetition. `[source_supported]` For LWDB this motivates a **corpus-level** slop axis:
comparing many generations to detect shared skeletons, not just repetition inside one
text. `[engineering_inference]` The specific templating signatures of our target model are
unknown until we run it. `[unvalidated_hypothesis]`
Source: arxiv.org/html/2403.00553v2

### 2.6 Deterministic lexical-diversity measures

Type-token ratio (TTR), MATTR (moving-average TTR), MTLD, HD-D, and hapax rate are
**established, well-understood NLP measures** of lexical diversity. `[source_supported]`
MATTR/MTLD/HD-D specifically exist because raw TTR is length-sensitive; these are the
standard corrections. `[source_supported]` Their use **as slop signals** — i.e., that a
particular MTLD value means "sloppy fiction" — is an engineering extrapolation with no
validated fiction thresholds. `[engineering_inference]` They are cheap, deterministic, and
offline, which is why they belong in the implement-now layer even while their thresholds
stay unvalidated. `[engineering_inference]`

### 2.7 Exact and approximate repetition

Duplicate-sentence detection, repeated n-gram counts, and compression ratio (e.g.,
gzip-based) are **standard, well-defined measures** of redundancy. `[source_supported]`
They are deterministic and reproducible. `[source_supported]` The choice of *which* n,
*what* compression-ratio cutoff, or *how many* duplicate sentences constitutes slop is an
engineering decision with no ratified threshold. `[engineering_inference]` These are strong
implement-now candidates precisely because the raw measurement is objective even when the
verdict is not. `[engineering_inference]`

### 2.8 Embedding-based semantic redundancy

Using sentence/passage embeddings to detect **semantic redundancy** (paraphrase loops
that say the same thing twice) and **cross-output template similarity** (many generations
clustering near one another) is a natural extension of the corpus-sameness idea.
`[engineering_inference]` For LWDB this is **interface-only**: we define the API, pin an
**offline** embedding model (fixed weights, versioned, no network call), and leave
thresholds unset. `[engineering_inference]` The hypothesis that embedding-cosine above some
cutoff reliably marks slop (as opposed to legitimate motif recurrence) is
untested. `[unvalidated_hypothesis]`

### 2.9 Binary AI-text detectors — rejected for slop

Binary "AI vs. human" classifiers are **unreliable from a single text**, are confounded by
genre and voice, and produce **false positives on simple, spare, or lyrical prose**.
`[rejected_approach]` They answer a question LWDB is not asking (authorship), and adopting
one would let an authorship signal masquerade as a quality signal. `[rejected_approach]`
Rejected as a slop detector.

### 2.10 Simple phrase blacklist as the sole detector

A fixed list of "slop phrases" used as the **only** detector is rejected. `[rejected_approach]`
A blacklist ignores **frequency** (once vs. ten times), **clustering** (spread out vs.
piled up), **cross-output repetition** (novel here but boilerplate across the corpus),
**context**, **genre**, and **voice**. `[rejected_approach]` A stock phrase used once in an
apt place is not slop. A blacklist may still contribute as *one weak feature* among many,
but never as the verdict. `[engineering_inference]`

---

## 3. Candidate-method matrix

`evidence_type`: deterministic | semantic | reviewer.
`recommended_status`: implement_now | interface_only | calibration_only | research_further | reject.

| method | detects | evidence_type | deterministic | model_dependency | offline_capable | genre_risk | voice_risk | short_text_limit | long_text_limit | false_positive_risk | implementation_cost | recommended_status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Repeated n-grams / duplicate sentences | verbatim + near-verbatim repetition | deterministic | yes | none | yes | low | med | unreliable <~200 tok | scales well | low–med | low | implement_now |
| Compression ratio (gzip) | gross redundancy / templating | deterministic | yes | none | yes | low | low | noisy on short text | scales well | low | low | implement_now |
| Lexical diversity (TTR/MATTR/MTLD/HD-D) | vocabulary flattening | deterministic | yes | none | yes | med | med | TTR unstable; use MATTR/MTLD | stable | med | low | implement_now |
| Hapax rate | vocabulary richness | deterministic | yes | none | yes | med | med | unstable when short | stable | med | low | implement_now |
| Rhythm / sentence-length variance | monotone cadence, voice flattening | deterministic | yes | none | yes | med | high | needs several sentences | stable | med | low | implement_now |
| Stock-phrase feature (frequency + clustering) | stock-phrase concentration | deterministic | yes | curated list | yes | high | med | limited | good | med–high | med | calibration_only |
| Embedding semantic redundancy (within-doc) | paraphrase loops | semantic | no | pinned offline embedder | yes (pinned) | med | high | weak on short text | good | high | med | interface_only |
| Embedding cross-output template similarity | corpus-level sameness | semantic | no | pinned offline embedder | yes (pinned) | med | med | n/a (corpus) | good | high | med–high | interface_only |
| Local-coherence break detection | subtle coherence disruption | semantic | no | classifier/model | depends | high | high | poor | uneven | high | high | research_further |
| Reviewer checklist (binary decomposed) | generic endings, redundancy, voice | reviewer | no | human or judge model | yes (human) | low | low | good | good | low–med | med | implement_now |
| Reviewer checklist via model judge | same, automated | reviewer | no | judge model | depends | low–med | med | good | good | med | med | calibration_only |
| Binary AI-text detector | (authorship — not slop) | semantic | no | proprietary/model | often no | high | high | very poor | poor | very high | med | reject |
| Phrase blacklist as sole verdict | listed phrases only | deterministic | yes | list | yes | high | high | poor | poor | very high | low | reject |

---

## 4. Rejected or constrained approaches

The following are explicitly rejected or constrained for LWDB:

1. **Claiming reliable AI authorship from a single text — rejected.** Single-text
   authorship classification is unreliable and confounded by voice, genre, and length.
   LWDB does not make authorship claims. (§2.9)

2. **Relying only on a blacklist — rejected as sole detector.** A phrase list without
   frequency, clustering, cross-output, context, genre, and voice awareness produces false
   positives on legitimate single uses. Permitted only as one weak feature. (§2.10)

3. **Using a single lexical-diversity statistic as a quality verdict — rejected.** No one
   number (TTR, MTLD, hapax, etc.) is a verdict; diversity is multi-axis and the axes
   diverge. (§2.3, §2.6)

4. **Treating all repetition as bad — rejected.** Deliberate rhetorical repetition and
   progressing motifs are craft, not slop. Repetition detectors must be read with intent
   and context. (§5)

5. **Ignoring genre and voice — rejected.** Genre norms and character/narrator voice
   change what counts as diversity, coherence, and "stock." Detectors that ignore them
   mislead. (§2.2, §5)

6. **Hiding evidence behind a scalar — rejected.** Every signal must expose the spans and
   counts that produced it. A bare number is not an acceptable output. (§1)

7. **Requiring proprietary online services for routine offline evaluation — rejected.**
   Routine LWDB runs must work fully offline with pinned, versioned models. Online
   proprietary detectors/embedders are not a dependency for the standard battery. (§2.8,
   §2.9)

---

## 5. False-positive risks

These patterns look superficially "sloppy" to naive detectors but are legitimate craft.
LWDB must not flag them, and any threshold work must treat them as protected cases:

- **Deliberate rhetorical repetition.** Anaphora, refrains, and incantatory repetition are
  intentional. High n-gram repeat counts here are a feature, not a fault.
- **Motif recurrence with progression.** A recurring image (a door, a color, a phrase) that
  gains new meaning on each return is thematic craft, not corpus sameness.
- **Concise, low-diversity prose.** Spare, plain writing may score low on lexical diversity
  by design. Low MTLD is not proof of slop.
- **Lyrical or unusual syntax.** Fragmented, inverted, or poetic syntax can trip
  coherence and cadence detectors while being exactly the intended voice.
- **Character-specific diction.** A narrator or character with a deliberately narrow,
  repetitive, or idiosyncratic vocabulary should not be penalized for staying in voice.
- **Intentional fragmentation.** Sentence fragments and clipped rhythm used for effect will
  inflate variance/cadence flags without being defects.
- **Genre-appropriate stock phrase used once.** A single, apt use of a conventional phrase
  ("once upon a time," a hardboiled cliché in noir) is idiom, not slop. Frequency and
  clustering — not mere presence — are what matter.

---

## 6. Recommendations for Dispatch 23

1. **Implement the deterministic layer now.** Ship repeated n-grams / duplicate sentences,
   compression ratio, lexical diversity (MATTR/MTLD/HD-D, hapax), and rhythm/sentence-length
   variance. These are cheap, reproducible, and fully offline. They emit **measurements**,
   not verdicts.

2. **Pin semantic interfaces without thresholds.** Define the embedding-based
   redundancy and cross-output template-similarity APIs and wire in a **pinned, versioned,
   offline** embedding model. Leave every cutoff unset. Mark these `interface_only`.

3. **Stand up the reviewer checklist now.** Adopt the CheckEval-style decomposition into
   binary checks for a human reviewer immediately. A model-judge variant is
   `calibration_only` until we test its reliability on our own outputs.

4. **All thresholds remain unvalidated until calibration.** No numeric cutoff in this
   review — repetition, diversity, cadence, or embedding cosine — is ratified. Thresholds
   are set only after a calibration pass against real generations and the protected cases
   in §5.

5. **Require evidence spans, never a bare scalar.** Every detector output must carry the
   underlying spans, counts, and context needed for a human to judge. LWDB reports evidence;
   it does not pronounce a single slop score, and it never claims AI authorship.

6. **Defer research-further items.** Local-coherence disruption detection stays out of the
   shipping battery pending more evidence (§2.2).

---

*End of Slop-Detection Research Review v1. See the [LWDB Architecture Spec](./linewright-diagnostic-battery-architecture-v1.md) for how these layers fit the battery.*
