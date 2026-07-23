"""Dispatch 28B — render mechanical-report.md from the frozen result artifacts (15 sections)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(
    HERE, "..", "runs", "linewright-prompt-execution-v1")
RUN = os.path.abspath(RUN)
ARMS = ["P0-Realistic", "P0-Maximal", "P1-Contract", "P3-Ideal"]


def j(name):
    return json.load(open(os.path.join(RUN, name), encoding="utf-8"))


def main():
    m = j("mechanical-results.json")
    integ = j("generation-integrity.json")
    pos = j("instruction-position-analysis.json")
    comp = j("comprehension-execution-analysis.json")
    a = m["mechanical_by_arm"]
    fr = m["focused_revision"]
    eff = m["effects"]
    fl = m["effect_floors"]
    anti = m["anti_results"]
    L = []
    P = L.append
    P("# Mechanical results — LineWright Prompt-Execution v1 (Dispatch 28B)\n")
    P("Deterministic scoring via the frozen `validators/checks.py`. Primary metric: clean_execution "
      "(all required changes made AND protected preserved AND no forbidden change AND unaffected scope "
      "kept AND output contract satisfied). No LLM grader for primary correctness.\n")

    P("## 1. Generation integrity")
    P(f"- Outcome **{integ['outcome']}** — {integ['actual_outputs']}/100 outputs, "
      f"{integ['comprehension_outputs']} comprehension; missing {integ['missing_outputs']}, "
      f"duplicates {integ['duplicate_outputs']}, token caps {integ['token_cap_hits']}, "
      f"reasoning traces {integ['reasoning_trace_count']}, technical failures {integ['technical_failures']}.")
    P(f"- Env: {integ['environment']}\n")

    P("## 2. Overall results by arm\n")
    P("| arm | n | clean_exec | all_required | invalid_unchanged | protected_acc | unauth_edit | no_change_acc | shape | critical |")
    P("|---|---|---|---|---|---|---|---|---|---|")
    for arm in ARMS:
        x = a[arm]
        P(f"| {arm} | {x['n']} | {x['clean_execution']['rate']} | {x['all_required_completed']['rate']} "
          f"| {x['invalid_unchanged']['rate']} | {x['protected_text_accuracy']} | {x['unauthorized_edit_rate']['rate']} "
          f"| {(x['no_change_accuracy'] or {}).get('rate')} | {x['output_shape_validity']['rate']} | {x['critical_failure_count']} |")
    P("")

    P("## 3. Clean execution success (primary composite)")
    P("- " + " · ".join(f"{arm} {a[arm]['clean_execution']['rate']}" for arm in ARMS) + "\n")

    P("## 4. Required-change completion")
    P("- all-required-completed: " + " · ".join(f"{arm} {a[arm]['all_required_completed']['rate']}" for arm in ARMS) + "\n")

    P("## 5. Returned-unchanged analysis")
    P("- invalid-unchanged (revision arms): " + " · ".join(f"{arm} {a[arm]['invalid_unchanged']['rate']}" for arm in ARMS))
    P("- valid no-change accuracy: " + " · ".join(f"{arm} {(a[arm]['no_change_accuracy'] or {}).get('rate')}" for arm in ARMS) + "\n")

    P("## 6. Partial-fix distribution (focused revision, changes completed 0..5)")
    for arm in ARMS:
        if arm in fr:
            P(f"- {arm}: mean {fr[arm]['mean_changes_completed']} · dist {fr[arm]['partial_fix_distribution']}")
    P("")

    P("## 7. Protected-text preservation")
    P("- accuracy: " + " · ".join(f"{arm} {a[arm]['protected_text_accuracy']}" for arm in ARMS))
    P("- corruption count: " + " · ".join(f"{arm} {a[arm]['protected_corruption_count']}" for arm in ARMS) + "\n")

    P("## 8. Unauthorized editing / over-compliance")
    P("- unauthorized-edit rate (revision): " + " · ".join(f"{arm} {a[arm]['unauthorized_edit_rate']['rate']}" for arm in ARMS))
    P("- forbidden violations by arm: " + str(anti["forbidden_violations_by_arm"]) + "\n")

    P("## 9. No-change judgment")
    P("- restraint accuracy: " + " · ".join(f"{arm} {(a[arm]['no_change_accuracy'] or {}).get('rate')}" for arm in ARMS) + "\n")

    P("## 10. Canon / voice / scene / structured families (clean rate by arm)")
    for arm in ARMS:
        fams = m["family_by_arm"][arm]
        P(f"- {arm}: " + ", ".join(f"{k}={v['clean']['rate']}" for k, v in sorted(fams.items())))
    P("")

    P("## 11. Instruction-position analysis (focused revision, clean rate)")
    for arm in ARMS:
        if arm in pos["instruction_position"]:
            row = pos["instruction_position"][arm]
            P(f"- {arm}: " + ", ".join(f"{p}={row[p]['clean_execution']['rate']}" for p in ("early", "middle", "late") if p in row))
    P("")

    P("## 12. Comprehension vs execution (6 probes)")
    P(f"- grid {comp['grid']} — {comp['interpretation']}\n")

    P("## 13. Precommitted effect floors")
    for name, block in fl.items():
        P(f"- **{name}: {'PASS' if block['PASS'] else 'FAIL'}** — " +
          ", ".join(f"{k}={v}" for k, v in block.items() if k != "PASS"))
    P("")
    P("### Precommitted comparisons")
    P(f"- P1 − P0-Maximal (structure alone): clean {eff['p1_minus_p0_maximal']['clean_execution_gain']}, "
      f"focused all-required {eff['p1_minus_p0_maximal']['focused_revision_all_required_gain']}, "
      f"invalid-unchanged reduction {eff['p1_minus_p0_maximal']['invalid_unchanged_reduction']}")
    P(f"- P1 − P0-Realistic (elicitation+structure): clean {eff['p1_minus_p0_realistic']['clean_execution_gain']}, "
      f"invalid-unchanged reduction {eff['p1_minus_p0_realistic']['invalid_unchanged_reduction']}")
    P(f"- P3-Ideal − P1 (richer packet): clean {eff['p3ideal_minus_p1']['clean_execution_gain']}, "
      f"canon {eff['p3ideal_minus_p1']['canon_gain']}, voice {eff['p3ideal_minus_p1']['voice_gain']}\n")

    P("## 14. Anti-results (P1 vs P0-Maximal)")
    P(f"- new protected corruption: {anti['new_protected_text_corruption']} · unauthorized-edit increase: "
      f"{anti['unauthorized_edit_rate_increase']} · new critical failures: {anti['new_critical_failures_p1_vs_p0max']} "
      f"· no-change accuracy drop: {anti['no_change_accuracy_drop']}\n")

    P("## 15. Headline reading")
    P("- Requirement elicitation (P0-Realistic → P0-Maximal) is the real lever: clean "
      f"{a['P0-Realistic']['clean_execution']['rate']} → {a['P0-Maximal']['clean_execution']['rate']}, "
      f"focused mean-changes {fr['P0-Realistic']['mean_changes_completed']} → {fr['P0-Maximal']['mean_changes_completed']}.")
    P("- Contract STRUCTURE (P1) does not beat equivalent maximal NL (P0-Maximal) and mildly hurts "
      "(1 new protected corruption, 2 forbidden violations, canon 1.0→0.667). All three precommitted "
      "floors FAIL.")
    P("- The richer ideal packet does not beat P1 and under-executes focused revision (mean 1.25).")
    P("- Comprehension is saturated (6/6) while execution fails (4/6 pass_fail): the residual "
      "multi-constraint focused-revision failure is EXECUTION DISCIPLINE at a model-capability ceiling, "
      "not a representation/comprehension gap that a better prompt could close.")

    open(os.path.join(RUN, "mechanical-report.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L))
    print("wrote mechanical-report.md")


if __name__ == "__main__":
    main()
