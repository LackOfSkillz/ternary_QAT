# Gate 0 — manual review flags

Human-authored flags to accompany the auto-generated
[`gate-0-revision-deltas.md`](gate-0-revision-deltas.md). These raise issues for
Gate 1 adversarial review; **no record is promoted or rewritten on their basis in
this correction dispatch** (per Dispatch 13's instruction to expose, not fix).

## dsa-revision-001 (Dark Speculative)

The gold's replacement image — *"a tap was running, steady, into a basin that had
stopped filling long ago"* — may be intentionally uncanny (a tap running into an
already-overflowing/blocked basin) or may be **logically muddled**. Flag for
Gary's Tier B judgment on whether the image reads as deliberately wrong vs.
accidentally incoherent.

## dsa-revision-002 (Dark Speculative — no-change case)

The **rejected response may be too obviously bad** (a heavily padded rewrite) and
therefore insufficiently tempting as a failure exemplar. Flag for possible
replacement with a subtler over-edit during Gate 1.

## dsa-revision-006 (Suspense/Mystery)

Auto-report flags: an **em dash was introduced** (`before he was ready for it —
locked`) that is not among the authorized changes, plus a colon and a large edit
distance for a rhythm-only task. **Do not auto-remove the dash** — surfaced for
human judgment on whether the rhythm repair overreached into punctuation/semantic
additions.

## dsa-canon-002 (Canon extraction)

**Mediated-source precision.** The record may treat a disputed claim as externally
established where the more accurate encoding is *"Edith reports that Margaret
disputes her account"* — i.e., certainty should be `character_belief` /
`mediated`, not `established`. Flag for Gate 1 to confirm belief-vs-truth labeling
on the mediated claim.

## dsa-scene-003 (Scene contract) — RESOLVED in Dispatch 13

The viewpoint-field ambiguity is resolved: the scene-contract output now splits
`viewpoint_character` (Sena — the known focal decision-maker, filled) from
`narrative_perspective` (unstated, correctly nulled and flagged). See the record
and `specification.md`. No further action needed beyond Gate 1 confirmation.
