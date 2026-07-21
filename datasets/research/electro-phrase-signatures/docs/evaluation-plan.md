# Evaluation plan — AI-style risk reduction

## Goal (stated honestly)

> Reduce the textual patterns that human readers and automated classifiers commonly
> associate with generated prose, so LineWright-assisted books read as naturally
> authored, stylistically varied fiction.

The practical target is that, on **blinded** evaluation, independent readers and
automated classifiers do not identify LineWright-assisted prose as AI-authored with
materially better-than-chance reliability. Treat "50/50" as an **aspiration**, not
a product guarantee. **No claim is made that LineWright defeats AI detectors.**

The evaluation must not rely on any single commercial detector. It uses three
layers.

## Layer 1 — Blind human evaluation

Prepare matched samples, same length/genre/prompt:

- human-authored prose,
- unedited model prose,
- LineWright-assisted prose,
- LineWright-assisted prose **after** phrase-risk correction.

Reviewers answer one question per sample — `Human-authored` / `AI-assisted` /
`Unsure` — and record a confidence rating. Samples are shuffled and unlabeled.

**Primary target:** reviewers do not identify LineWright-assisted prose as
AI-assisted substantially above chance; `Unsure` is a *good* outcome, not a
failure.

## Layer 2 — Multi-detector panel

Run several detectors, never one. For each detector record: name and version;
probability/label; false-positive rate on **known human** prose; false-negative
rate on **known model** prose; and result variance across detectors.

**Do not optimize directly against any one detector's output.** A result is only
meaningful if it holds across the panel and does not inflate false positives on
genuine human writing.

## Layer 3 — Internal style metrics (deterministic)

From the Gate 0 v3 scanner (`scan_phrase_signatures.py`) and the Gate 0 v2 corpus
scanner:

- high-risk phrase-family density (per 1,000 words),
- repeated-construction density,
- em-dash introduction rate and em-dash **compound** signatures,
- intensifier density,
- sentence-opening repetition,
- cross-character bodily-reaction overlap,
- cross-profile syntactic similarity,
- source-to-gold phrase-family deltas (introduced vs removed).

## Success criteria (not "detector says human")

Success requires **all** of:

- reduced signature density (Layer 3),
- preserved author voice (no `converted_voice_to_house_style`),
- no generic flattening and no obvious thesaurus substitution,
- blind readers frequently choosing `Unsure` (Layer 1),
- classifier results clustering near chance across a **mixed** test set (Layer 2),
  **without** raising false positives on known-human prose.

A drop in detector score that comes with voice flattening or thesaurus swapping is
a **failure**, not a success.

## Detector-resistance guardrails (binding principles)

1. LineWright improves prose **quality**; it does not perform adversarial detector
   obfuscation.
2. Do **not** add deliberate errors to appear human.
3. Do **not** inject random punctuation, misspellings, or grammar mistakes.
4. Do **not** vary syntax randomly without respecting voice.
5. Do **not** rewrite author-supplied prose merely because a phrase appears in the
   lexicon.
6. Do **not** optimize against secret or reverse-engineered detector thresholds.
7. Do **not** market LineWright as "undetectable."
8. Prefer genuine stylistic diversity over detector-specific manipulation.

### Product language

Use:

> LineWright reduces repetitive AI writing habits and helps preserve the author's
> individual voice.

Avoid:

> LineWright makes AI writing undetectable.
