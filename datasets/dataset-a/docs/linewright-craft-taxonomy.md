# LineWright Craft Taxonomy

> **AUTHORITATIVE SOURCE.** This is the authoritative LineWright Craft Taxonomy as
> supplied to the project (Dispatch 13). Preserve its wording and technical
> distinctions; do not silently rewrite its claims. Transport-encoding artifacts
> in the supplied text (mojibake em dashes / smart quotes / accented letters) have
> been normalized to their intended characters; no technique, tier, metric, or
> engineering claim has been changed. For the Dataset A working subset, see
> `craft-taxonomy-reference.md` (non-authoritative summary).

*An exhaustive register of literary techniques, organized by injectability and vote-separability.*

---

## Architectural Preface

Techniques are stratified into three tiers by **whether a candidate selection can constitute a vote for them.**

| Tier | Definition | Vote-learnable? | Confidence |
|------|-----------|-----------------|------------|
| **A — Measurable** | Deterministically countable in output text | Yes | `Certain` |
| **B — Estimable** | Detectable by classifier/heuristic with error | Yes, with noise | `Possible` |
| **C — Structural** | Operates above the candidate's span | **No** | N/A — author-declared |

**Tier C techniques must never enter the voting system.** They belong in the craft constitution as explicit author choices. A 300-word candidate cannot express ring composition; a vote for that candidate says nothing about the author's feelings on ring composition. Including them poisons the signal.

**Tier A is where the voice profile actually lives.** Voice is largely a syntactic and lexical fingerprint. Sentence rhythm, coordination strategy, verb density, diction stratum — these are countable, orthogonal, and vary independently across candidates.

---

# TIER A — MEASURABLE
*Countable in output. Deterministic. The core of the voice profile.*

## A1. Sentence Architecture

| Technique | Definition | Metric |
|-----------|-----------|--------|
| **Parataxis** | Clauses set side by side; little subordination | Ratio of independent to dependent clauses |
| **Hypotaxis** | Nested subordination | Mean subordination depth |
| **Asyndeton** | Conjunctions omitted between coordinate elements | Coordinate elements per conjunction |
| **Polysyndeton** | Conjunctions repeated in excess ("and…and…and") | Conjunctions per coordinate element |
| **Periodic sentence** | Main clause deferred to the end | Position of main verb (normalized) |
| **Cumulative / loose sentence** | Main clause first, modifiers accrete after (Christensen) | Post-head modifier count |
| **Balanced sentence** | Two symmetrical halves | Clause-length symmetry |
| **Fragment** | Sentence lacking subject or predicate | Fragment ratio |
| **Run-on / fused** | Independent clauses joined without punctuation | — |
| **Left-branching** | Modifiers precede the head | Pre-head token count |
| **Right-branching** | Modifiers follow the head | Post-head token count |
| **Mid-branching** | Interruption between subject and verb | Subject–verb distance |
| **Sentence-length variance** | Rhythm of long against short | Standard deviation of length |
| **Anastrophe / hyperbaton** | Inverted or scrambled word order | Deviation from canonical order |
| **Apposition** | Renaming noun phrase set adjacent | Appositive count |
| **Absolute phrase** | Noun + participle modifying the whole sentence | — |
| **Participial opener** | Sentence begins with a participial phrase | Opening-POS distribution |
| **Ellipsis (grammatical)** | Omission of recoverable elements | — |
| **Aposiopesis** | Sentence broken off mid-utterance | Terminal dash/ellipsis count |
| **Zeugma / syllepsis** | One verb governing incongruent objects | — |

## A2. Diction & Lexis

| Technique | Metric |
|-----------|--------|
| **Anglo-Saxon vs. Latinate stratum** | Etymological ratio |
| **Concrete vs. abstract nouns** | Concreteness-norm mean |
| **Verb density** | Finite verbs per 100 words |
| **Nominalization** | `-tion` / `-ment` / `-ness` rate |
| **Active vs. passive voice** | Passive construction rate |
| **Adverb density** | `-ly` adverbs per 100 words |
| **Adjective stacking** | Adjectives per noun phrase |
| **Filter words** | *saw, felt, heard, noticed, realized, watched, thought, knew* per 100 words |
| **Modal hedging** | *seemed, almost, somewhat, a little, rather* |
| **Type-token ratio** | Lexical variety |
| **Rare-word rate** | Frequency-band distribution |
| **Contraction rate** | Register signal |
| **Proper-noun density** | Specificity / authority |
| **Sensory lexicon by channel** | Visual / auditory / tactile / olfactory / gustatory shares |

## A3. Sound & Prosody

| Technique | Definition |
|-----------|-----------|
| **Alliteration** | Repeated initial consonants |
| **Assonance** | Repeated vowel sounds |
| **Consonance** | Repeated internal/terminal consonants |
| **Sibilance** | Concentration of /s/, /ʃ/ |
| **Onomatopoeia** | Sound-imitative words |
| **Euphony / cacophony** | Phonetic smoothness or harshness |
| **Metrical intrusion** | Accidental iambic or trochaic drift in prose |
| **Clausula** | Rhythm of sentence endings (stress pattern of final syllables) |
| **Terminal stress** | Whether sentences end on stressed monosyllables |

## A4. Rhetorical Schemes (structural repetition)

| Scheme | Definition |
|--------|-----------|
| **Anaphora** | Repetition at the beginning of successive clauses |
| **Epistrophe** | Repetition at the end |
| **Symploce** | Both simultaneously |
| **Epizeuxis** | Immediate repetition of a word |
| **Anadiplosis** | Last word of a clause opens the next |
| **Chiasmus** | ABBA inversion of structure |
| **Antimetabole** | ABBA inversion of exact words |
| **Isocolon** | Parallel clauses of equal length |
| **Tricolon** | Three parallel members |
| **Tricolon crescens** | Three parallel members of increasing length |
| **Antithesis** | Contrasting ideas in parallel structure |
| **Polyptoton** | Repetition of a root in varied forms |
| **Diacope** | Repetition broken by intervening words |

## A5. Dialogue Mechanics

| Technique | Metric |
|-----------|--------|
| **Dialogue-to-narration ratio** | Quoted words / total |
| **Tag frequency** | Tags per exchange |
| **Said-bookisms** | Non-*said* speech verbs (*retorted, opined, hissed*) |
| **Action beats replacing tags** | Beats per exchange |
| **Adverbial tags** | *he said quietly* |
| **Stichomythia** | Rapid single-line alternation |
| **Turn length variance** | Long speeches against clipped answers |
| **Interruption / aposiopesis in speech** | Terminal dashes in dialogue |
| **Non-answer rate** | Questions answered with questions or silence |
| **Idiolect divergence** | Cross-character lexical distinctness |
| **Contraction rate by speaker** | Register per character |

---

# TIER B — ESTIMABLE
*Detectable with error. Vote-learnable with noise. Confidence: `Possible`.*

## B1. Narrative Perspective & Distance

| Technique | Notes |
|-----------|-------|
| **First person central** | Protagonist narrates |
| **First person peripheral** | Observer narrates another's story (Nick Carraway) |
| **First person retrospective** | Older self narrating past self; ironic gap |
| **First person immediate** | Present-tense, no retrospective knowledge |
| **First person plural** | *The Virgin Suicides*, *Then We Came to the End* |
| **Second person** | Direct address |
| **Third limited (close third)** | Single reflector consciousness |
| **Third objective / dramatic / camera-eye** | No interiority (*Hills Like White Elephants*) |
| **Third omniscient (editorial)** | Narrator comments and judges |
| **Third omniscient (roving)** | Access shifts without commentary |
| **Head-hopping** | Uncontrolled POV migration within scene — usually a defect |
| **Focalization** (Genette) | Zero / internal (fixed, variable, multiple) / external |
| **Psychic distance** (Gardner's ladder) | Five degrees from long shot to deep interior |
| **Narrative irony gap** | Distance between narrator's knowledge and character's |
| **Unreliable narrator** | Types: the *picaro* (exaggerator), the *madman*, the *clown*, the *naïf*, the *liar* |
| **Fallible narrator** | Sincere but mistaken, as distinct from unreliable |
| **Implied author** | The authorial persona inferred from the text |
| **Narratee** | The addressed listener within the fiction |
| **Epistolary** | Told in documents |
| **Frame narrative** | Story within story |

## B2. Consciousness Representation

| Technique | Notes |
|-----------|-------|
| **Psycho-narration** (Cohn) | Narrator reports consciousness in narrator's idiom |
| **Narrated monologue / free indirect discourse** | Narration inflected by character idiom, untagged |
| **Quoted monologue** | Direct thought, present tense, first person |
| **Stream of consciousness** | Associative, unpunctuated flow |
| **Interior monologue** | Sustained silent speech |
| **Subtext** | Meaning below the stated |
| **Suppression / withholding** | The unspoken as pressure |
| **Iceberg theory** (Hemingway) | Omission of the known, felt as weight |
| **Objective correlative** (Eliot) | External object standing for internal state |
| **Show vs. tell** | Dramatization against summary |
| **Emotional naming** | *She felt grief* — the tell-line failure mode |
| **Physiological displacement** | Emotion rendered as bodily sensation |

## B3. Description & Detail Economy

| Technique | Notes |
|-----------|-------|
| **Significant / telling detail** | One particular standing for a whole |
| **Sensory hierarchy** | Which channel leads |
| **Detail rationing** | Density and placement of specificity |
| **Negative description** | What is absent, unsaid, missing |
| **Description through action** | Setting revealed by movement through it |
| **Perceptual bias** | What the POV notices *is* characterization |
| **Defamiliarization / ostranenie** (Shklovsky) | Rendering the familiar strange |
| **Delayed decoding** (Conrad) | Reader perceives the effect before the cause |
| **Setting as mood** | Environment carrying emotional register |
| **Pathetic fallacy** | Nature mirroring feeling |
| **Establishing shot** | Wide orientation before close focus |
| **Selective omission** | Deliberate blank space |

## B4. Figuration

| Trope | Notes |
|-------|-------|
| **Simile** | Explicit comparison |
| **Metaphor** | Implicit; *dead*, *mixed*, *extended (conceit)*, *controlling* |
| **Metonymy** | Substitution by association |
| **Synecdoche** | Part for whole |
| **Personification** | Agency granted to the inanimate |
| **Apostrophe** | Address to the absent |
| **Hyperbole** | Overstatement |
| **Litotes** | Affirmation by negated opposite |
| **Meiosis** | Deliberate understatement |
| **Paradox** | Apparent self-contradiction that resolves |
| **Oxymoron** | Compressed contradiction |
| **Verbal irony** | Saying the opposite |
| **Situational irony** | Outcome inverts expectation |
| **Dramatic irony** | Reader knows what the character does not |
| **Cosmic irony** | The universe as indifferent antagonist |
| **Synesthesia** | Cross-channel sensory blend |
| **Catachresis** | Deliberate misuse of a term |
| **Allusion** | Reference to another text |
| **Symbol** | Object carrying accreted meaning |
| **Motif** | Recurring image, phrase, or figure |
| **Image system** | Coordinated pattern of related images |

## B5. Tone & Register

| Technique | Notes |
|-----------|-------|
| **Register** | Formal / colloquial / vernacular / technical / archaic |
| **Tonal mode** | Elegiac, comic, deadpan, hardboiled, lyrical, ironic |
| **Deadpan** | Affect withheld from charged content |
| **Bathos** | Descent from elevated to trivial |
| **Comic undercutting** | Gravity punctured by register break |
| **Tonal modulation** | Controlled shift across a scene |
| **Sentimentality** | Emotion unearned by the material — a defect |
| **Authorial intrusion** | Narrator addressing the reader directly |
| **Metafiction** | The text acknowledging itself |

---

# TIER C — STRUCTURAL
*Operates above the candidate's span. **Not vote-learnable.** Author-declared in the craft constitution.*

## C1. Time (after Genette)

**Order**
- Chronological
- Analepsis (flashback): internal / external / mixed
- Prolepsis (flash-forward)
- Achrony (unorderable)
- In medias res
- Reverse chronology
- Braided / parallel timelines
- Ring composition (circular return)

**Duration**
- Scene (story time ≈ discourse time)
- Summary (story time > discourse time)
- Ellipsis (story time elided)
- Pause (discourse time, no story time — description)
- Stretch (discourse time > story time — slow motion)

**Frequency**
- Singulative (once, told once)
- Repeating (once, told several times — *Rashomon*)
- Iterative (many times, told once — *"Every Sunday we would…"*)

## C2. Scene Architecture

- **Cold open** — begin inside the action, orientation deferred
- **Late entry / early exit** — "come in late, leave early"
- **Scene / sequel** (Swain) — scene: *goal, conflict, disaster*; sequel: *reaction, dilemma, decision*
- **Value shift** (McKee) — a scene must turn a value from positive to negative or the reverse
- **Turn / reversal** — the moment the scene's charge inverts
- **Beat** — the smallest unit of action and reaction
- **Button / curtain line** — the final line that lands the scene
- **Set piece** — extended, choreographed sequence
- **Crosscutting / intercutting** — interleaved simultaneous action
- **Deferred entry** — scene opens after the inciting act
- **Obligatory scene** — the confrontation the premise promises

## C3. Plot Architecture

- Freytag's pyramid
- Three-act, four-act, five-act
- Fichtean curve
- Hero's journey / monomyth
- Story circle (Harmon)
- *Kishōtenketsu* (four-movement, conflictless)
- Episodic / picaresque
- Bildungsroman
- Mosaic / fragmentary
- Rashomon structure (contested accounts)
- Frame / nested narrative

**Causal grammar**
- *Therefore / but* causality against *and then* sequence
- Try-fail cycles
- Rising complication
- **Peripeteia** (reversal) and **anagnorisis** (recognition)
- **Hamartia** — the flaw that becomes fate
- **Catharsis**
- Denouement / falling action
- Deliberate anticlimax
- *Deus ex machina* — a defect

**Planted apparatus**
- **Chekhov's gun** — the shown object that must fire
- **Plant and payoff**
- **Foreshadowing**
- **Red herring**
- **MacGuffin**
- **Ticking clock**
- **Cliffhanger**
- **Dramatic irony as structure** — the reader's knowledge held across chapters

## C4. Character Architecture

- Direct vs. indirect characterization
- **STEAL**: Speech, Thoughts, Effect on others, Actions, Looks
- Characterization through **choice under pressure**
- Characterization through **perceptual bias** (what they notice)
- Characterization through **object** (the buttoned coat)
- Want vs. need
- Flaw / wound / lie
- Arc: positive, negative, flat
- Round vs. flat (Forster)
- Static vs. dynamic
- **Ficelle** (James) — a character existing to draw the protagonist out
- Foil
- Confidant
- Chorus character
- Antagonist as mirror
- Entrance technique; reputation preceding arrival

## C5. Genre Craft

- **Heist**: the plan / the crew / the complication / the reveal of the real plan
- **Mystery**: fair-play clueing / the false solution / the least likely suspect
- **Horror**: dread against terror against horror; the unseen
- **Romance**: the meet / the barrier / the dark moment
- **Thriller**: the ticking clock / the chase
- **Noir**: the fall / moral compromise / the compromised investigator
- **Epic fantasy**: prophecy / found family / the cost of power

---

# Engineering Notes

## The vote signal

Do not record *"this candidate was generated with polysyndeton injected."* Record *"this candidate measured 0.71 on the polysyndeton index and was selected; its siblings measured 0.12, 0.09, 0.31, 0.15 and were discarded."*

The first is a claim about the prompt. The second is evidence about the output. **The differentiation gate already proved these diverge.**

## Confounding

Certain Tier B techniques co-occur by necessity:
- Free indirect discourse **entails** close third or first person.
- Deep psychic distance **entails** low filter-word density.
- Stichomythia **entails** low turn length.

Confounded pairs cannot be separated by selection votes. Either treat them as a single composite dimension, or ensure the candidate generator varies them independently — which for entailed pairs is impossible. **Mark confounded clusters in the schema.**

## Dimensionality

Tier A alone is roughly sixty measurable dimensions. With five candidates per batch and one selection, each batch yields one preference observation over sixty dimensions. This is a severely underdetermined system. Two consequences:

1. **The voice profile cannot be learned quickly.** Hundreds of selections, minimum, before any dimension separates from noise.
2. **Report confidence honestly per dimension.** A dimension with eleven observations has not converged. Surface that. Never present an unconverged dimension as a learned preference.

This is the `Certain / Matched / Possible` discipline applied to the voice engine. A voice profile that asserts a preference it has not earned is the same failure as a stance label that was applied post-hoc.

## Hard dependency

**The voice engine cannot be built before selection data exists.** Zero selections have been recorded. The correct order is:

1. Ship generation.
2. Record selections with measured technique vectors attached.
3. Write nothing to a voice profile.
4. Accumulate for months of real authoring.
5. *Then* examine whether any dimension has separated.

Building the learner before the corpus exists is building an acceptance gate with nothing to accept.
