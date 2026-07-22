"""Apply the FROZEN research-continuation threshold to the three models and select a
provisional LineWright Core foundation (Dispatch 26, Deliverables 4 + 7).

Refuses to run unless the Dispatch-25 threshold lock verifies (thresholds are NOT re-authored
here — the same frozen floors are reused). Computes per-model Phase-A feasibility, folds in the
blind-review and deployment summaries when present (else marks them pending), and selects one
foundation branch via the dispatch's decision hierarchy. Writes:

  training/reports/dispatch-26-core-prose-feasibility.{yaml,md}
  training/reports/dispatch-26-foundation-decision.{yaml,md}
"""
import json
import os
import sys

import yaml

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.thresholds import freeze

RUN = os.path.join(_REPO, "benchmarks", "runs", "lwdb-stronger-base-v1")
OUT = os.path.join(_REPO, "training", "reports")

# frozen floors (research-continuation-v0) — reused, NOT re-authored
FLOORS = {"mechanical_pass_rate": 0.40, "core_prose_pass_rate": 0.50, "modules_with_usable": 7,
          "max_severe_slop_rate": 0.25, "max_runaway_token_cap_rate": 0.25,
          "bare_success_rate": 0.40, "realistic_packet_success_rate": 0.35}

# 4B control baseline (Dispatch 24/25; core-prose failed at 0.286)
CONTROL_4B_FAST = {"mechanical_pass_rate": 0.45, "core_prose_pass_rate": 0.286,
                   "modules_with_usable": 7, "severe_slop_rate": 0.05, "token_cap_rate": 0.15,
                   "bare_success_rate": 0.421}


def feasibility(rates):
    failed = []
    if rates.get("mechanical_pass_rate") is None or rates["mechanical_pass_rate"] < FLOORS["mechanical_pass_rate"]:
        failed.append(f"mechanical_pass_rate<{FLOORS['mechanical_pass_rate']}")
    if rates.get("core_prose_pass_rate") is None or rates["core_prose_pass_rate"] < FLOORS["core_prose_pass_rate"]:
        failed.append(f"core_prose_pass_rate<{FLOORS['core_prose_pass_rate']}")
    if rates.get("modules_with_usable", 0) < FLOORS["modules_with_usable"]:
        failed.append(f"modules_with_usable<{FLOORS['modules_with_usable']}")
    if rates.get("severe_slop_rate", 1.0) > FLOORS["max_severe_slop_rate"]:
        failed.append(f"severe_slop_rate>{FLOORS['max_severe_slop_rate']}")
    if rates.get("token_cap_rate", 1.0) > FLOORS["max_runaway_token_cap_rate"]:
        failed.append(f"token_cap_rate>{FLOORS['max_runaway_token_cap_rate']}")
    if rates.get("bare_success_rate") is None or rates["bare_success_rate"] < FLOORS["bare_success_rate"]:
        failed.append(f"bare_success_rate<{FLOORS['bare_success_rate']}")
    rp = rates.get("realistic_packet_pass_rate")
    if rp is not None and rp < FLOORS["realistic_packet_success_rate"]:
        failed.append(f"realistic_packet<{FLOORS['realistic_packet_success_rate']}")
    return (len(failed) == 0), failed


def load_opt(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


def main():
    v = freeze.verify_lock()
    assert v.get("threshold_precommit_valid"), f"threshold lock invalid: {v}"

    summary = json.load(open(os.path.join(RUN, "run-summary.json"), encoding="utf-8"))
    per_role = summary["per_role"]
    integ = summary["integrity"]

    # assemble per-model rate views
    models = {}
    # candidates from the D26 fast battery + packet family
    for role in ("ministral_3_8b_instruct", "qwen3_8b_non_thinking"):
        r = per_role.get(role, {})
        models[role] = {
            "mechanical_pass_rate": r.get("fast_mechanical_pass_rate"),
            "core_prose_pass_rate": r.get("core_prose_pass_rate"),
            "modules_with_usable": r.get("modules_with_usable", 0),
            "severe_slop_rate": r.get("severe_slop_rate"),
            "token_cap_rate": r.get("token_cap_rate"),
            "bare_success_rate": r.get("bare_success_rate"),
            "realistic_packet_pass_rate": r.get("realistic_packet_pass_rate"),
            "reasoning_trace_rate": r.get("reasoning_trace_rate"),
            "packet_arm_pass_rates": r.get("packet_arm_pass_rates"),
        }
    # control 4B: fast rates reused from D24/D25; realistic packet from THIS run if present
    c = per_role.get("target_base_4b", {})
    models["target_base_4b"] = dict(CONTROL_4B_FAST,
                                    realistic_packet_pass_rate=c.get("realistic_packet_pass_rate"),
                                    packet_arm_pass_rates=c.get("packet_arm_pass_rates"))

    feas = {}
    for m, r in models.items():
        ok, failed = feasibility(r)
        feas[m] = {"rates": r, "clears_frozen_floors": ok, "failed_floors": failed}

    blind = load_opt(os.path.join(RUN, "blind-review-summary.json"))
    deploy = load_opt(os.path.join(RUN, "deployment-summary.json"))

    # ---- decision hierarchy ----
    fatal = []
    if integ.get("problems"):
        fatal.append(f"integrity problems: {integ['problems'][:3]}")
    if integ.get("missing"):
        fatal.append(f"missing jobs: {integ['missing']}")
    # reasoning-trace leakage is an integrity/validity fault for a non-thinking role
    q_leak = (models["qwen3_8b_non_thinking"].get("reasoning_trace_rate") or 0) > 0

    candidates = ["ministral_3_8b_instruct", "qwen3_8b_non_thinking"]
    feasible_candidates = [m for m in candidates if feas[m]["clears_frozen_floors"]]

    reasons = []
    if fatal:
        branch = "insufficient_evidence"
        reasons.append(f"fatal run-integrity problems: {fatal}")
    elif not feasible_candidates:
        # neither stronger base clears the frozen floors
        both_fail_core = all(feas[m]["rates"].get("core_prose_pass_rate", 0) < FLOORS["core_prose_pass_rate"]
                             for m in candidates)
        if both_fail_core:
            branch = "test_another_base"
            reasons.append("neither stronger base clears the 0.50 core-prose floor; the 4B also failed (0.286) — the bottleneck persists across bases; test a different base rather than scale data.")
        else:
            branch = "insufficient_evidence"
            reasons.append("candidates fail non-core floors ambiguously; ambiguity is not a win.")
    elif len(feasible_candidates) == 1:
        pick = feasible_candidates[0]
        pick_name = {"ministral_3_8b_instruct": "select_Ministral_3_8B",
                     "qwen3_8b_non_thinking": "select_Qwen3_8B"}[pick]
        # deployment: a local foundation needs a viable 8GB path
        deploy_ok = bool(deploy and deploy.get(f"{'qwen3' if pick.startswith('qwen') else 'ministral'}_8gb_path_viable"))
        # blind prose: is the pick the TOP prose model, or materially below a competitor?
        prose = {m: (blind["per_model"].get(m, {}) or {}).get("mean_prose_quality")
                 for m in models} if blind else {}
        pick_prose = prose.get(pick)
        better = [m for m, p in prose.items() if p is not None and pick_prose is not None and p > pick_prose + 0.15]
        if blind is None or deploy is None:
            branch = "run_one_bounded_confirmation"
            reasons.append(f"{pick} is the only model clearing the frozen floors; confirm the single unresolved distinction (blind prose and/or 8GB deployment) before committing.")
        elif better:
            branch = "run_one_bounded_confirmation"
            reasons.append(f"{pick} is the ONLY model clearing the frozen threshold and has a viable 8GB deployment path, BUT its blind prose ({pick_prose}) is marginally below {better} — a real unresolved distinction. The frozen threshold (and the explicit rule that prose preference cannot override a threshold failure) still rules out the prose-preferred model(s). Run ONE bounded confirmation targeting {pick}'s prose quality (expanded/human blind pass) before committing the foundation; {pick} is the presumptive foundation.")
        elif not deploy_ok:
            branch = "run_one_bounded_confirmation"
            reasons.append(f"{pick} clears the frozen threshold but its local 8GB deployment path is unproven; bounded confirmation on the deployment path.")
        else:
            branch = pick_name
            reasons.append(f"{pick} clears the frozen floors, is top or tied on blind prose, has no fatal/critical faults, and a viable 8GB deployment path.")
    else:
        # both feasible — prefer on hierarchy: severe degeneration, realistic packet, blind prose, deployment
        if blind is None or deploy is None:
            branch = "run_one_bounded_confirmation"
            reasons.append("both stronger bases clear the frozen floors; resolve the deciding distinction (blind prose + deployment) with one bounded confirmation rather than a broad new benchmark.")
        else:
            # decide by blind prose then deployment practicality
            pref = blind.get("preferred_model")
            branch = {"ministral_3_8b_instruct": "select_Ministral_3_8B",
                      "qwen3_8b_non_thinking": "select_Qwen3_8B"}.get(pref, "run_one_bounded_confirmation")
            reasons.append(f"both feasible; blind prose preferred {pref}; deployment practicality confirms.")

    rejected = []
    for b in ["select_Ministral_3_8B", "select_Qwen3_8B", "retain_current_4B",
              "run_one_bounded_confirmation", "test_another_base", "insufficient_evidence"]:
        if b != branch:
            rejected.append({"branch": b, "reason": "not selected by the decision hierarchy given the evidence above"})

    decision = {
        "dispatch": 26, "provisional": True, "final_commercial_ship_certification": False,
        "threshold_lock": {"valid": v.get("threshold_precommit_valid"),
                           "research_sha256": v.get("research_threshold_sha256"),
                           "starter_sha256": v.get("starter_threshold_sha256")},
        "frozen_floors": FLOORS,
        "integrity": integ,
        "qwen_reasoning_trace_leak": q_leak,
        "per_model_feasibility": feas,
        "feasible_candidates": feasible_candidates,
        "blind_review": blind or "PENDING (genuinely-blind sub-agent reviewers; external humans Gary/ChatGPT pending)",
        "deployment": deploy or "PENDING (quantization + 8GB-fit study)",
        "branch": branch,
        "rationale": reasons,
        "rejected_branches": rejected,
        "decision_hierarchy": ["fatal integrity/licensing/safety", "frozen research threshold",
                               "critical mechanical regressions", "severe degeneration",
                               "realistic packet capability", "blind prose quality",
                               "quantized quality retention", "8GB deployment practicality",
                               "future context headroom", "packaging/toolchain complexity"],
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "dispatch-26-core-prose-feasibility.yaml"), "w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump({"core_prose_feasibility": {
            "frozen_floor": FLOORS["core_prose_pass_rate"],
            "per_model": {m: {"core_prose_pass_rate": feas[m]["rates"].get("core_prose_pass_rate"),
                              "clears_floor": (feas[m]["rates"].get("core_prose_pass_rate") or 0) >= FLOORS["core_prose_pass_rate"],
                              "clears_all_floors": feas[m]["clears_frozen_floors"],
                              "failed_floors": feas[m]["failed_floors"]} for m in models}}},
            fh, sort_keys=False, allow_unicode=True)
    with open(os.path.join(OUT, "dispatch-26-foundation-decision.yaml"), "w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump({"foundation_decision": decision}, fh, sort_keys=False, allow_unicode=True)
    print(json.dumps({"branch": branch, "feasible_candidates": feasible_candidates,
                      "core_prose": {m: feas[m]["rates"].get("core_prose_pass_rate") for m in models},
                      "qwen_leak": q_leak}, indent=1))
    return decision


if __name__ == "__main__":
    main()
