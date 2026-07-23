# Mechanical results — LineWright Prompt-Execution v1 (Dispatch 28B)

Deterministic scoring via the frozen `validators/checks.py`. Primary metric: clean_execution (all required changes made AND protected preserved AND no forbidden change AND unaffected scope kept AND output contract satisfied). No LLM grader for primary correctness.

## 1. Generation integrity
- Outcome **valid** — 100/100 outputs, 6 comprehension; missing 0, duplicates 0, token caps 0, reasoning traces 0, technical failures 0.
- Env: {'gpu': 'NVIDIA GB10', 'torch': '2.10.0a0+b558c986e8.nv25.11', 'transformers': '5.14.1', 'model_revision': 'b968826d9c46dd6066d109eabc6255188de91218', 'thinking': 'disabled', 'decoding': 'greedy', 'seed': 20260723}

## 2. Overall results by arm

| arm | n | clean_exec | all_required | invalid_unchanged | protected_acc | unauth_edit | no_change_acc | shape | critical |
|---|---|---|---|---|---|---|---|---|---|
| P0-Realistic | 30 | 0.4 | 0.346 | 0.15 | 0.889 | 0.05 | 0.75 | 0.75 | 7 |
| P0-Maximal | 30 | 0.633 | 0.615 | 0.0 | 1.0 | 0.0 | 1.0 | 0.0 | 1 |
| P1-Contract | 30 | 0.567 | 0.615 | 0.0 | 0.963 | 0.05 | 1.0 | 0.5 | 2 |
| P3-Ideal | 10 | 0.6 | 0.556 | 0.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0 |

## 3. Clean execution success (primary composite)
- P0-Realistic 0.4 · P0-Maximal 0.633 · P1-Contract 0.567 · P3-Ideal 0.6

## 4. Required-change completion
- all-required-completed: P0-Realistic 0.346 · P0-Maximal 0.615 · P1-Contract 0.615 · P3-Ideal 0.556

## 5. Returned-unchanged analysis
- invalid-unchanged (revision arms): P0-Realistic 0.15 · P0-Maximal 0.0 · P1-Contract 0.0 · P3-Ideal 0.0
- valid no-change accuracy: P0-Realistic 0.75 · P0-Maximal 1.0 · P1-Contract 1.0 · P3-Ideal 1.0

## 6. Partial-fix distribution (focused revision, changes completed 0..5)
- P0-Realistic: mean 1.0 · dist {'0': 4, '1': 6, '2': 0, '3': 2, '4': 0, '5': 0}
- P0-Maximal: mean 2.25 · dist {'0': 0, '1': 3, '2': 4, '3': 4, '4': 1, '5': 0}
- P1-Contract: mean 2.083 · dist {'0': 0, '1': 4, '2': 3, '3': 5, '4': 0, '5': 0}
- P3-Ideal: mean 1.25 · dist {'0': 1, '1': 1, '2': 2, '3': 0, '4': 0, '5': 0}

## 7. Protected-text preservation
- accuracy: P0-Realistic 0.889 · P0-Maximal 1.0 · P1-Contract 0.963 · P3-Ideal 1.0
- corruption count: P0-Realistic 3 · P0-Maximal 0 · P1-Contract 1 · P3-Ideal 0

## 8. Unauthorized editing / over-compliance
- unauthorized-edit rate (revision): P0-Realistic 0.05 · P0-Maximal 0.0 · P1-Contract 0.05 · P3-Ideal 0.0
- forbidden violations by arm: {'P0-Realistic': 0, 'P0-Maximal': 0, 'P1-Contract': 2, 'P3-Ideal': 0}

## 9. No-change judgment
- restraint accuracy: P0-Realistic 0.75 · P0-Maximal 1.0 · P1-Contract 1.0 · P3-Ideal 1.0

## 10. Canon / voice / scene / structured families (clean rate by arm)
- P0-Realistic: canon_continuation=0.0, constraint_bound_scene=1.0, multi_constraint_focused_revision=0.083, no_change_judgment=0.75, protected_text_revision=0.8, structured_protocol=0.0, voice_preserving_revision=0.667
- P0-Maximal: canon_continuation=1.0, constraint_bound_scene=1.0, multi_constraint_focused_revision=0.167, no_change_judgment=1.0, protected_text_revision=1.0, structured_protocol=0.0, voice_preserving_revision=1.0
- P1-Contract: canon_continuation=0.667, constraint_bound_scene=1.0, multi_constraint_focused_revision=0.083, no_change_judgment=1.0, protected_text_revision=1.0, structured_protocol=0.0, voice_preserving_revision=1.0
- P3-Ideal: canon_continuation=1.0, constraint_bound_scene=1.0, multi_constraint_focused_revision=0.0, no_change_judgment=1.0, protected_text_revision=1.0, voice_preserving_revision=1.0

## 11. Instruction-position analysis (focused revision, clean rate)
- P0-Realistic: early=0.0, middle=0.25, late=0.0
- P0-Maximal: early=0.25, middle=0.25, late=0.0
- P1-Contract: early=0.0, middle=0.25, late=0.0
- P3-Ideal: early=0.0, middle=0.0

## 12. Comprehension vs execution (6 probes)
- grid {'pass_pass': 2, 'fail_fail': 0, 'pass_fail': 4, 'fail_pass': 0} — 4 task(s) understood but not executed -> execution-discipline failure; 2 task(s) understood and executed

## 13. Precommitted effect floors
- **structure_success: FAIL** — clean_gain>=0.15=False, focused_all_required_gain>=0.20=False, invalid_unchanged_reduction>=0.20=False, no_new_critical_failures=False, protected_not_worse=False, unauthorized_not_worse=False
- **practical_product_success: FAIL** — clean_gain>=0.20=False, invalid_unchanged_reduction>=0.25=False, no_new_critical_failures=True
- **ideal_packet_signal: FAIL** — clean_gain>=0.10=False, canon_or_voice_gain>=0.15=False, no_new_critical_failures=True

### Precommitted comparisons
- P1 − P0-Maximal (structure alone): clean -0.066, focused all-required 0.0, invalid-unchanged reduction 0.0
- P1 − P0-Realistic (elicitation+structure): clean 0.167, invalid-unchanged reduction 0.15
- P3-Ideal − P1 (richer packet): clean 0.0, canon 0.0, voice 0.0

## 14. Anti-results (P1 vs P0-Maximal)
- new protected corruption: 1 · unauthorized-edit increase: True · new critical failures: 1 · no-change accuracy drop: 0.0

## 15. Headline reading
- Requirement elicitation (P0-Realistic → P0-Maximal) is the real lever: clean 0.4 → 0.633, focused mean-changes 1.0 → 2.25.
- Contract STRUCTURE (P1) does not beat equivalent maximal NL (P0-Maximal) and mildly hurts (1 new protected corruption, 2 forbidden violations, canon 1.0→0.667). All three precommitted floors FAIL.
- The richer ideal packet does not beat P1 and under-executes focused revision (mean 1.25).
- Comprehension is saturated (6/6) while execution fails (4/6 pass_fail): the residual multi-constraint focused-revision failure is EXECUTION DISCIPLINE at a model-capability ceiling, not a representation/comprehension gap that a better prompt could close.