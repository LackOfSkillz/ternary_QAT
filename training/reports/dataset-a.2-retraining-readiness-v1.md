# Dataset A.2 — Retraining Readiness Gate (Dispatch 21, Phase J)

The conditions that must ALL hold before a new LoRA or ternary-QAT run may begin. Encoded
machine-checkably in `linewright/evaluation/advancement.py::check_retraining_readiness`.

## Readiness flags (all must be true)

```yaml
dataset_schema_valid: true
all_records_static_valid: true
behavior_coverage_approved: true
source_family_split_clean: true
story_world_split_clean: true
duplicate_scan_clean: true
memorization_scan_clean: true
pilot_review_complete: true
aedan_dataset_approval: true
claude_dataset_approval: true
chatgpt_dataset_approval: true
```

`check_retraining_readiness(state)` returns `{ready, blockers}`; a missing flag is treated
as not-ready, never as a pass.

## Current status (this dispatch)

The mechanical prerequisites are met by construction and can be re-verified any time:

| flag | status now | evidence |
|---|---|---|
| dataset_schema_valid | ✅ | `validate_a2.py` passes |
| all_records_static_valid | ✅ | `validate_a2.py` passes (shape + gates) |
| source_family_split_clean | ✅ | Phase-D grouping check passes |
| story_world_split_clean | ✅ | disjoint train/eval worlds |
| duplicate_scan_clean | ✅ | no shared source openings / hashes |
| memorization_scan_clean | ✅ | no gold overlaps another training target |
| behavior_coverage_approved | ⏳ | requires human coverage sign-off |
| pilot_review_complete | ⏳ | requires the three-reviewer blind pass |
| aedan/claude/chatgpt_dataset_approval | ⏳ | requires reviewer approval |

So the dataset is **mechanically ready** but **not review-approved**: the human/independent
approvals are outstanding by design. `next_training_run` stays **blocked**.

## The next training comparison (once ready)

When the gate opens, the next run must use:

- the **same untouched base model** (`prism-ml/Ternary-Bonsai-4B-unpacked`);
- **independent** LoRA and QAT starts from that base (QAT never resumes LoRA);
- the **proven QAT stability recipe** unchanged (lr 2e-4, warmup 3, clip 1.0, raw-norm
  abort rail 100 / two-consecutive) — Dispatch 21 did not modify it;
- an **expanded held-out** evaluation (each behavior tested by several records);
- **per-task token budgets** (the fake-quant eval cost from Dispatch 20 must be bounded);
- the **hardened evaluator** (the nine Phase-E gates, not parse-only);
- **blinded candidate review** with the Phase-H advancement rule.

The original high-learning-rate QAT hypothesis remains a **separate** mechanistic
experiment, not folded into the dataset comparison.

## Standing interpretation until the gate opens

```yaml
training_result_interpretation: provisional
model_quality_claims: prohibited
gary_prose_review: deferred
next_training_run: blocked
```
