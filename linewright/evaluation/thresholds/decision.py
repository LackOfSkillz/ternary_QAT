"""Apply the frozen research-continuation threshold to evidence (Dispatch 25, D10).

Refuses to run unless the threshold lock is valid, and stamps every decision with the locked
threshold hashes + commit so a decision can be tied to exactly the thresholds in force. The
ambiguous-middle rule is applied as written: ambiguity is never counted as improvement.
"""
from linewright.evaluation.thresholds.freeze import require_locked_before_analysis
from linewright.evaluation.thresholds.loader import load
from linewright.evaluation.thresholds import RESEARCH_THRESHOLD

_FLOORS = [
    ("minimum_total_mechanical_pass_rate", "mechanical_pass_rate", "ge"),
    ("minimum_core_prose_pass_rate", "core_prose_pass_rate", "ge"),
    ("minimum_required_modules_with_at_least_one_usable_result", "modules_with_usable", "ge"),
    ("maximum_severe_slop_rate", "severe_slop_rate", "le"),
    ("maximum_runaway_token_cap_rate", "token_cap_rate", "le"),
    ("minimum_bare_prompt_success_rate", "bare_success_rate", "ge"),
    ("minimum_realistic_packet_success_rate", "packet_success_rate", "ge"),
]


def _cmp(op, val, thr):
    return val >= thr if op == "ge" else val <= thr


def base_feasible(base_evidence, research):
    bf = research["research_continuation"]["base_feasibility"]
    checks = []
    ok = True
    for tkey, ekey, op in _FLOORS:
        thr = bf[tkey]["value"]
        val = base_evidence.get(ekey)
        passed = val is not None and _cmp(op, val, thr)
        ok = ok and passed
        checks.append({"floor": tkey, "op": op, "threshold": thr, "value": val, "pass": passed})
    return ok, checks


def decide(evidence, research=None):
    """``evidence`` = {base:{...rates...}, improvements:int, critical_regressions:int,
    curve:{monotone_worsening:bool, earlier_better:bool}}. Returns the decision dict."""
    lock = require_locked_before_analysis()
    research = research or load(RESEARCH_THRESHOLD)
    rc = research["research_continuation"]

    feasible, checks = base_feasible(evidence.get("base", {}), research)
    improvements = int(evidence.get("improvements", 0))
    critical_regr = int(evidence.get("critical_regressions", 0))
    curve = evidence.get("curve", {}) or {}
    min_improve = rc["trainability_signal"]["minimum_number_of_target_capabilities_showing_improvement"]["value"]

    # branch selection in priority order (rules quoted from the frozen threshold)
    if not feasible:
        failed_core = any(not c["pass"] and c["floor"] in
                          ("minimum_total_mechanical_pass_rate", "minimum_core_prose_pass_rate")
                          for c in checks)
        branch = "test_stronger_base" if failed_core else "pause_current_direction"
        result = "fail"
    elif curve.get("earlier_better") and curve.get("later_collapse"):
        branch, result = "checkpoint_selection_only", "ambiguous"
    elif improvements >= min_improve and critical_regr == 0 and not curve.get("monotone_worsening"):
        branch, result = "continue_scaled_dataset", "pass"
    elif critical_regr > 0 or curve.get("monotone_worsening"):
        branch, result = "revise_training_objective", "fail"
    else:
        # ambiguous middle: apply the frozen action (bounded confirmation; not improvement)
        branch, result = "insufficient_evidence", "ambiguous"

    return {
        "threshold_lock": {"research_sha256": lock["research_threshold_sha256"],
                           "starter_sha256": lock["starter_threshold_sha256"],
                           "git_commit": lock["git_commit"],
                           "threshold_precommit_valid": lock["threshold_precommit_valid"]},
        "base_feasible": feasible, "feasibility_checks": checks,
        "improvements": improvements, "critical_regressions": critical_regr, "curve": curve,
        "threshold_result": result, "branch": branch,
        "ambiguous_middle_action": rc["trainability_signal"]["ambiguous_middle_action"]["value"],
    }
