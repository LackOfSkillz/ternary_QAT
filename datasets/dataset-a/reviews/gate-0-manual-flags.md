# Gate 0 — manual review flags

Human-authored flags to accompany the auto-generated
[`gate-0-revision-deltas.md`](gate-0-revision-deltas.md). Originally raised in
Dispatch 13 (expose, not fix). **Dispatch 14 has since applied the Gate 1/Gate 2
corrections**; resolution notes are appended per item below. Records remain
`draft` / `unassigned` / `excluded_from_training: true` — corrected, not approved.

## dsa-revision-001 (Dark Speculative)

The gold's replacement image — *"a tap was running, steady, into a basin that had
stopped filling long ago"* — may be intentionally uncanny (a tap running into an
already-overflowing/blocked basin) or may be **logically muddled**. Flag for
Gary's Tier B judgment on whether the image reads as deliberately wrong vs.
accidentally incoherent.

**Resolved (Dispatch 14):** replaced with a legibly-wrong image — *"the dining
chairs had been lined up facing the wall, evenly spaced, their backs to her"* — a
concrete object-state a person clearly arranged, not an ambiguous fluid image.

## dsa-revision-002 (Dark Speculative — no-change case)

The **rejected response may be too obviously bad** (a heavily padded rewrite) and
therefore insufficiently tempting as a failure exemplar. Flag for possible
replacement with a subtler over-edit during Gate 1.

**Resolved (Dispatch 14):** the record now uses the structured no-change protocol
(`changed: false`, source text preserved), and the rejected response is a
*competent* over-edit (normalized simile, compressed repetition) that reads
cleanly but still rewrites clean prose.

## dsa-revision-006 (Suspense/Mystery)

Auto-report flags: an **em dash was introduced** (`before he was ready for it —
locked`) that is not among the authorized changes, plus a colon and a large edit
distance for a rhythm-only task. **Do not auto-remove the dash** — surfaced for
human judgment on whether the rhythm repair overreached into punctuation/semantic
additions.

**Resolved (Dispatch 14):** the rhythm repair was rewritten to combine clipped
sentences only — no em dash, no colon, no interior interpretation ("before he was
ready for it" removed), keeping "The light moved." as the closing punch. The
record's `invention_budget` is `none`, and the evaluation now distinguishes
authorized structural combination from unauthorized punctuation/semantic additions.

## dsa-canon-002 (Canon extraction)

**Mediated-source precision.** The record may treat a disputed claim as externally
established where the more accurate encoding is *"Edith reports that Margaret
disputes her account"* — i.e., certainty should be `character_belief` /
`mediated`, not `established`. Flag for Gate 1 to confirm belief-vs-truth labeling
on the mediated claim.

**Resolved (Dispatch 14):** the Margaret fact is now phrased as a mediated report
— *"Edith reports that Margaret disputes her account of the will"* — and kept
`certainty: "established"`, because what is established is Edith's report. No
`mediated` enum was added; the specification's "certainty applies to the
proposition as phrased" rule governs.

## dsa-scene-003 (Scene contract) — RESOLVED in Dispatch 13

The viewpoint-field ambiguity is resolved: the scene-contract output now splits
`viewpoint_character` (Sena — the known focal decision-maker, filled) from
`narrative_perspective` (unstated, correctly nulled and flagged). See the record
and `specification.md`. No further action needed beyond Gate 1 confirmation.
