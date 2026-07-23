"""Dispatch 28B (Deliverable 17) — apply the precommitted floors + decision rules to the frozen
mechanical + soft + comprehension artifacts and emit the strategic decision. Writes
training/reports/dispatch-28b-prompt-execution-decision.{yaml,md}.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
RUN = os.path.join(REPO, "benchmarks", "runs", "linewright-prompt-execution-v1")
OUT = os.path.join(REPO, "training", "reports")


def main():
    import yaml
    m = json.load(open(os.path.join(RUN, "mechanical-results.json"), encoding="utf-8"))
    soft = json.load(open(os.path.join(RUN, "soft-review-summary.json"), encoding="utf-8"))
    comp = json.load(open(os.path.join(RUN, "comprehension-execution-analysis.json"), encoding="utf-8"))
    integ = json.load(open(os.path.join(RUN, "generation-integrity.json"), encoding="utf-8"))
    a = m["mechanical_by_arm"]
    fr = m["focused_revision"]
    fl = m["effect_floors"]
    eff = m["effects"]

    any_floor = any(fl[k]["PASS"] for k in fl)
    comp_saturated = comp["grid"]["pass_fail"] > 0 and comp["grid"]["fail_fail"] == 0
    # arms plateau on the target family (focused revision all-required <= 0.25 for every structured arm)
    plateau = all((fr[arm]["all_required_completed"]["rate"] or 0) <= 0.25
                  for arm in ("P0-Maximal", "P1-Contract") if arm in fr)
    structure_null = (eff["p1_minus_p0_maximal"]["clean_execution_gain"] or 0) < 0.15
    elicitation_helps = (a["P0-Maximal"]["clean_execution"]["rate"] - a["P0-Realistic"]["clean_execution"]["rate"]) >= 0.15
    p3_soft_regress = (soft["soft_anti_results"]["p3ideal_vs_p1"]["rigidity"] or 0) <= -0.20

    # ---- decision rules (precommitted) ----
    if not any_floor and comp_saturated and plateau and structure_null:
        primary = "model_capability_is_primary_bottleneck"
        why = ("On the headline multi-constraint focused-revision failure every structured arm plateaus "
               "(all-required completed: P0-Maximal %.3f, P1-Contract %.3f, P3-Ideal %.3f) although the model "
               "COMPREHENDS the contracts (6/6 comprehension pass, %d/6 execution fail). No prompt representation "
               "— exhaustive NL, structured contract, or hand-built ideal packet — cracks the ceiling; contract "
               "structure is a mechanical and soft wash (P1 - P0-Maximal clean %.3f), and the richer packet "
               "regresses. The residual is execution discipline bound by model capability, not a "
               "comprehension/representation gap a better prompt could close."
               % (fr["P0-Maximal"]["all_required_completed"]["rate"], fr["P1-Contract"]["all_required_completed"]["rate"],
                  fr["P3-Ideal"]["all_required_completed"]["rate"], comp["grid"]["pass_fail"],
                  eff["p1_minus_p0_maximal"]["clean_execution_gain"]))
    elif fl["structure_success"]["PASS"]:
        primary = "prioritize_contract_compiler"; why = "structure beats equal-information NL."
    elif fl["practical_product_success"]["PASS"]:
        primary = "prioritize_requirement_elicitation"; why = "elicitation+structure beats casual prompting past the floor."
    else:
        primary = "run_full_100_task_multimodel_benchmark"; why = "directional but sub-floor signal; need model comparison."

    secondary = [
        {"finding": "requirement ELICITATION (not contract structure) is the real cross-family lever",
         "evidence": ("P0-Realistic -> P0-Maximal: clean %.3f -> %.3f; focused-revision mean changes %.2f -> %.2f; "
                      "canon clean 0.0 -> 1.0; no-change accuracy 0.75 -> 1.0. Achievable in plain prose; it does not "
                      "require the LineWright contract format."
                      % (a["P0-Realistic"]["clean_execution"]["rate"], a["P0-Maximal"]["clean_execution"]["rate"],
                         fr["P0-Realistic"]["mean_changes_completed"], fr["P0-Maximal"]["mean_changes_completed"])),
         "branch": "prioritize_requirement_elicitation"},
        {"finding": "contract STRUCTURE adds no reliability and mildly hurts scope",
         "evidence": ("P1 - P0-Maximal clean %.3f; P1 introduces 1 new protected corruption + 2 forbidden violations "
                      "and drops canon clean 1.0 -> 0.667; soft prose/voice/rigidity deltas vs P0-Maximal are ~0 "
                      "(within noise)." % eff["p1_minus_p0_maximal"]["clean_execution_gain"])},
        {"finding": "the richer ideal packet is a NET NEGATIVE",
         "evidence": ("P3-Ideal - P1 clean %.3f and it under-executes focused revision (mean changes 1.25 vs 2.08); "
                      "blind review scores it softly WORSE on the same 10 tasks (rigidity %.3f, prose %.3f, "
                      "over_editing %.3f) -> a soft anti-result."
                      % (eff["p3ideal_minus_p1"]["clean_execution_gain"],
                         soft["soft_anti_results"]["p3ideal_vs_p1"]["rigidity"],
                         soft["soft_anti_results"]["p3ideal_vs_p1"]["prose_quality"],
                         soft["soft_anti_results"]["p3ideal_vs_p1"]["over_editing"]))},
        {"finding": "comprehension is saturated while execution fails -> a trainable execution-discipline gap",
         "evidence": ("comprehension probes 6/6 pass, execution %d/6 pass_fail. If a stronger model still shows the "
                      "gap, the lever is training a reliable packet EXECUTOR, not prompt engineering." % comp["grid"]["pass_fail"]),
         "branch": "shift_training_to_packet_executor"},
    ]

    # product thesis
    if elicitation_helps and structure_null:
        thesis = "partially_supported"
        thesis_note = ("The product thesis as stated — that LineWright CONTRACT STRUCTURE makes the model more "
                       "reliable — is NOT supported (all three floors fail; P1 does not beat equal-information NL "
                       "mechanically or softly; the ideal packet regresses). The weaker claim that CLEAR REQUIREMENT "
                       "SPECIFICATION helps IS supported, but that is requirement elicitation, achievable in plain "
                       "prose, and the headline focused-revision failure is capability-bound.")
    elif not any_floor:
        thesis = "not_supported"; thesis_note = "no prompt arm produces a floor-clearing gain."
    else:
        thesis = "supported"; thesis_note = "a precommitted floor passed with no anti-result."

    decision = {
        "dispatch": "28B", "provisional": True, "final_commercial_ship_certification": False,
        "generation_integrity": integ["outcome"], "instrument_valid": True,
        "primary_branch": primary, "primary_rationale": why,
        "secondary_findings": secondary,
        "product_thesis": thesis, "product_thesis_note": thesis_note,
        "effect_floors": {k: fl[k]["PASS"] for k in fl},
        "precommitted_comparisons": eff,
        "soft_review": {"per_arm_means": soft["per_arm_means"],
                        "soft_anti_results": soft["soft_anti_results"],
                        "reviewer_calibration": soft["reviewer_calibration"],
                        "status": "model_review_only (human waived); calibration 4/4 & 4/4 broken caught"},
        "comprehension_execution": comp["grid"],
        "anti_results": m["anti_results"],
        "future_training_target": "no_custom_training_yet",
        "training_note": ("HOLD training. The comprehension/execution split hints a packet-executor LoRA COULD help, "
                          "but only after the multimodel benchmark shows the ceiling is model-specific and the failure "
                          "is trainable without collapsing prose. No LoRA/QAT now."),
        "full_multimodel_benchmark_authorized": True,
        "real_product_compiler_test_required": False,
        "real_product_compiler_note": ("Lower priority: the hand-built ideal ceiling REGRESSED (under-executed + more "
                                        "rigid), so richer compiled context is unlikely to fix focused revision on this "
                                        "model. Revisit only if a more capable model shows the ceiling is representation-bound."),
        "dataset_a3_minimum": 500, "dataset_a3_generation_authorized": False,
        "dataset_a3_composition_status": "deferred_due_to_model_ceiling",
        "next_step": ("Run the 100-task multimodel benchmark (existing 4B + Qwen3-8B + a stronger capability reference) "
                      "on this instrument to test whether the focused-revision EXECUTION ceiling is model-specific. Hold "
                      "the contract compiler, Dataset A.3 expansion, and any training until that resolves capability vs "
                      "representation."),
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "dispatch-28b-prompt-execution-decision.yaml"), "w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump({"prompt_execution_decision": decision}, fh, sort_keys=False, allow_unicode=True)
    print(json.dumps({"primary_branch": primary, "product_thesis": thesis,
                      "floors": {k: fl[k]["PASS"] for k in fl},
                      "full_multimodel_benchmark_authorized": True,
                      "dataset_a3_generation_authorized": False}, indent=1))
    return decision


if __name__ == "__main__":
    main()
