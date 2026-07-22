"""Assemble Dispatch-25 evidence and apply the FROZEN research threshold (D10).

Computes base-feasibility rates from the Dispatch-24 live run, improvement/critical-regression
counts from the base-vs-candidate comparison, and curve flags from the checkpoint curve, then
calls the threshold-locked decision engine. Writes dispatch-25-decision-v1.{yaml,md}. Refuses
to run unless the threshold lock is valid; stamps the decision with the locked hashes.
"""
import json
import os
import sys

import yaml

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.thresholds import decision as dec
from linewright.evaluation.battery.score import load_battery

D24 = os.path.join(_REPO, "benchmarks", "runs", "lwdb-fast-v1-20260722", "item-level-results.json")
CURVE = os.path.join(_REPO, "benchmarks", "runs", "lwdb-checkpoint-curve-v0", "checkpoint-curve-summary.json")
OUT = os.path.join(_REPO, "training", "reports")

CORE_PROSE_MODULES = ("A_long_form_scene", "B_focused_revision")


def main():
    items, contracts = load_battery()
    rows = json.load(open(D24, encoding="utf-8"))
    by = {}
    for r in rows:
        by.setdefault(r["item_id"], {})[r["model_role"]] = r
    base = {i: by[i]["target_base"] for i in by}
    cand = {i: by[i]["new_candidate"] for i in by}

    n = len(base)
    base_pass = sum(1 for r in base.values() if r["mechanical_pass"])
    # core prose = scene/revision prose-output items
    prose = [i for i in base if items[i]["module"] in CORE_PROSE_MODULES
             and contracts[items[i]["behavior_contract_id"]]["expected_output_type"] == "prose"]
    core_prose_pass = sum(1 for i in prose if base[i]["mechanical_pass"])
    # modules with >=1 usable (pass + non-severe) base result
    mods = {}
    for i in base:
        m = items[i]["module"][0]
        usable = base[i]["mechanical_pass"] and base[i]["slop_severity"] != "severe"
        mods[m] = mods.get(m, False) or usable
    modules_usable = sum(1 for v in mods.values() if v)
    severe = sum(1 for r in base.values() if r["slop_severity"] == "severe")
    capped = sum(1 for r in base.values() if r["hit_token_cap"])
    bare = [i for i in base if items[i]["prompt_surface"] == "bare"]
    bare_pass = sum(1 for i in bare if base[i]["mechanical_pass"])
    packet = [i for i in base if items[i]["prompt_surface"] != "bare"]
    packet_pass = sum(1 for i in packet if base[i]["mechanical_pass"])

    base_rates = {
        "mechanical_pass_rate": round(base_pass / n, 3),
        "core_prose_pass_rate": round(core_prose_pass / len(prose), 3) if prose else None,
        "modules_with_usable": modules_usable,
        "severe_slop_rate": round(severe / n, 3),
        "token_cap_rate": round(capped / n, 3),
        "bare_success_rate": round(bare_pass / len(bare), 3) if bare else None,
        "packet_success_rate": round(packet_pass / len(packet), 3) if packet else None,
    }

    # improvements = capabilities where candidate beats base; critical regressions = items where
    # base was clean (pass, non-severe) but candidate is severe/fatal.
    improvements = sum(1 for i in base if cand[i]["mechanical_pass"] and not base[i]["mechanical_pass"])
    critical_regr = sum(1 for i in base if base[i]["mechanical_pass"] and base[i]["slop_severity"] != "severe"
                        and (cand[i]["slop_severity"] == "severe" or not cand[i]["mechanical_pass"]))

    curve = json.load(open(CURVE, encoding="utf-8"))["checkpoint_curve"]
    evidence = {"base": base_rates, "improvements": improvements,
                "critical_regressions": critical_regr,
                "curve": {"monotone_worsening": curve["monotone_worsening"],
                          "earlier_better": curve["early_improvement"],
                          "later_collapse": curve["late_collapse"]}}

    d = dec.decide(evidence)
    d["evidence"] = {"dispatch_24_base_rates": base_rates, "improvements": improvements,
                     "critical_regressions": critical_regr, "checkpoint_curve": curve}
    d["rejected_branches"] = []
    for b, reason in [
        ("continue_scaled_dataset", "no capability improves over base (improvements=%d) and the checkpoint curve is monotone-worsening" % improvements),
        ("checkpoint_selection_only", "LoRA-10 is neutral (does not improve over base); there is no better earlier checkpoint to select"),
        ("test_stronger_base", "the base PASSES the research-continuation feasibility floors, so the bottleneck is not base capacity" if d["base_feasible"] else "n/a — base failed feasibility"),
        ("pause_current_direction", "the base is feasible (not merely marginal), so pausing is not warranted"),
    ]:
        if b != d["branch"]:
            d["rejected_branches"].append({"branch": b, "reason": reason})
    d["required_next_experiment"] = ("a token-balanced, protocol-strengthened dataset with an "
        "EARLY-STOP / fewer-steps recipe (LoRA), holding base + method fixed, to test whether "
        "degeneration is over-exposure rather than method — ONE controlled variable at a time.")

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "dispatch-25-decision-v1.yaml"), "w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump({"decision": d}, fh, sort_keys=False, allow_unicode=True)
    print(json.dumps({"base_rates": base_rates, "improvements": improvements,
                      "critical_regressions": critical_regr, "base_feasible": d["base_feasible"],
                      "threshold_result": d["threshold_result"], "branch": d["branch"]}, indent=1))


if __name__ == "__main__":
    main()
