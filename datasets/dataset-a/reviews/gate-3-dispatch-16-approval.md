---
gate_3_status: approved_for_experimental_freeze
production_approval: false
reviewer: Gary Mix
reviewed_baseline: "7492546"
approval_date: "2026-07-21"
freeze_id: dataset-a-experimental-v1
---

# Gate 3 approval — Dispatch 16 calibration batch

**Reviewer:** Gary Mix (final human Gate 3 authority)
**Reviewed baseline:** `7492546` (`origin/linewright-experiments`)
**Approval date:** 2026-07-21

## Gate 2 disposition (independent model review)

- reviewer: Claude / Aedan
- result: **conditional_pass**
- required corrections: 1
- advisory reviews: 2

## Records reviewed

- `dsa-revision-011` … `dsa-revision-020` (the 10-record calibration batch)
- modified `dsa-revision-003` (comparative-template correction)

## Gate 3 decisions

| record | decision |
|---|---|
| dsa-revision-011 | approve **after** evaluation-wording fix (Correction A) |
| dsa-revision-015 | approved as written |
| dsa-revision-017 | approve **after** invention-budget clarification (Correction B) |
| all other Dispatch 16 records (012, 013, 014, 016, 018, 019, 020) | approved |
| modified dsa-revision-003 | approved |

## Required wording corrections (both applied in this dispatch)

- **Correction A — dsa-revision-011:** the Evaluation FAIL criterion was reworded so
  it no longer risks conflating a legitimate physical sensation with a
  named-emotion sensation cliché. New wording: *"FAIL on substituting another
  named-emotion sensation cliché, such as 'taste of dread,' 'knot of fear,' or
  'fist of panic,' or on raising the emotional volume."* Source, gold, rejected
  response, task intent, invention budget, and style profile are unchanged.
- **Correction B — dsa-revision-017:** the bounded invention budget now explicitly
  permits *unnamed functional crew roles already implied by the command-deck
  setting* (and concrete observable deck details), while prohibiting new **named**
  characters, relationships, motives, plot facts, a changed outcome, and a second
  pressure/weight metaphor. Reviewer notes updated to match. Source, gold, and
  rejected response are unchanged.

## Confirmations

- Gary **approves the Dispatch 16 calibration batch** (and the full 35-record
  Dataset A experimental corpus) **for the first experimental training rehearsal**
  (LoRA and ternary-QAT smoke tests).
- This is **not production approval.** Every frozen record carries
  `production_approved: false` and `experimental_use_only: true`. Smoke-test
  results must not be represented as evidence of production quality.
- The use of copyrighted and public-model-derived material for internal training
  and experimentation is an **accepted project decision** and is **not** a training
  blocker in this workflow. The broader copyright/training-material decision is
  **not** reopened here.
- **Provenance remains required.** Every record keeps a truthful `origin`,
  `teacher_model`, and provenance statement; the accepted licensing posture does
  not erase provenance recording.

```yaml
gate_3_status: approved_for_experimental_freeze
production_approval: false
```
