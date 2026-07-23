"""Dispatch 28B — deterministic mechanical scorer for the Prompt-Execution v1 run.

Uses ONLY validators/checks.py for check semantics (no arm-specific rules, no LLM grader). Reads
normalized-results/, writes mechanical-results.json, item-level-results.json, mechanical-report.md,
instruction-position-analysis.json, anti-result-analysis.json. Primary metric: clean_execution.
"""
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from validators import checks as C  # noqa: E402

RUN = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(
    HERE, "..", "runs", "linewright-prompt-execution-v1")
RUN = os.path.abspath(RUN)
ARMS = ["P0-Realistic", "P0-Maximal", "P1-Contract", "P3-Ideal"]
ARM_DIR = {"P0-Realistic": "p0-realistic", "P0-Maximal": "p0-maximal",
           "P1-Contract": "p1-contract", "P3-Ideal": "p3-ideal"}
REVISION = ("multi_constraint_focused_revision", "protected_text_revision", "voice_preserving_revision")


def load_tasks():
    return {t["task_id"]: t for t in (json.loads(l) for l in
            open(os.path.join(HERE, "task-manifest.jsonl"), encoding="utf-8") if l.strip())}


def load_outputs():
    out = {}
    for arm, d in ARM_DIR.items():
        dd = os.path.join(RUN, "normalized-results", d)
        if not os.path.isdir(dd):
            continue
        for fn in os.listdir(dd):
            if fn.endswith(".json"):
                r = json.load(open(os.path.join(dd, fn), encoding="utf-8"))
                out[(r["task_id"], arm)] = r
    return out


def score_output(task, rec):
    gt = task["evaluation_ground_truth"]
    fam = task["task_family"]
    text = rec.get("normalized_text", rec.get("output_text", ""))
    src = task["source_passage"]

    req = gt["required_changes"]
    req_pass = [{"id": r["id"], "passed": C.check(r["check"], text)} for r in req]
    completed = sum(1 for r in req_pass if r["passed"])
    all_completed = (completed == len(req)) if req else True

    prot = gt["protected_elements"]
    protected_preserved = sum(1 for p in prot if p["text"] in text)
    protected_ok = protected_preserved == len(prot)
    protected_corruption = bool(prot) and not protected_ok

    forb = gt["forbidden_changes"]
    forb_viol = [f["id"] for f in forb if not C.check(f["check"], text)]
    forbidden_ok = not forb_viol

    unaff = gt["unaffected_spans"]
    unaff_preserved = sum(1 for u in unaff if u["text"] in text)
    unaffected_ok = unaff_preserved == len(unaff)
    unauthorized_edit = (bool(unaff) and not unaffected_ok) or bool(forb_viol)

    shape = gt["expected_output_shape"]
    shape_checks = task["machine_checks"]["output_shape_checks"]
    shape_ok = all(C.check(c["check"], text) for c in shape_checks) if shape_checks else True

    ru = C.returned_unchanged(src, text) if src else False
    valid_nc = gt["valid_no_change_case"]
    invalid_unchanged = ru and not valid_nc and fam in REVISION

    src_norm = C.normalize(src) if src else ""
    restraint = valid_nc and protected_ok and forbidden_ok and (ru or (src_norm and src_norm in C.normalize(text)))
    unnecessary_edit = valid_nc and not restraint

    if valid_nc:
        clean = bool(restraint)
    else:
        clean = (all_completed and protected_ok and forbidden_ok and unaffected_ok
                 and shape_ok and not invalid_unchanged)
    critical_failure = protected_corruption or invalid_unchanged or (fam == "structured_protocol" and not shape_ok)

    return {
        "task_id": task["task_id"], "task_family": fam,
        "required_total": len(req), "completed": completed,
        "completion_rate": round(completed / len(req), 3) if req else None,
        "all_required_completed": all_completed, "required_results": req_pass,
        "returned_unchanged": ru, "valid_no_change": valid_nc, "invalid_unchanged": invalid_unchanged,
        "protected_total": len(prot), "protected_preserved": protected_preserved,
        "protected_ok": protected_ok, "protected_corruption": protected_corruption,
        "forbidden_total": len(forb), "forbidden_violations": forb_viol, "forbidden_ok": forbidden_ok,
        "unaffected_total": len(unaff), "unaffected_preserved": unaff_preserved,
        "unaffected_ok": unaffected_ok, "unauthorized_edit": unauthorized_edit,
        "output_shape_ok": shape_ok, "restraint_correct": restraint if valid_nc else None,
        "unnecessary_edit": unnecessary_edit if valid_nc else None,
        "clean_execution": clean, "critical_failure": critical_failure,
        "token_cap_hit": rec.get("token_cap_hit"), "reasoning_trace": rec.get("reasoning_trace_detected"),
    }


def rate(items, key):
    vals = [i[key] for i in items if i[key] is not None]
    return {"count": sum(1 for v in vals if v), "total": len(vals),
            "rate": round(sum(1 for v in vals if v) / len(vals), 3) if vals else None}


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def main():
    tasks = load_tasks()
    outs = load_outputs()
    items = {}
    for (tid, arm), rec in outs.items():
        items[(tid, arm)] = score_output(tasks[tid], rec)
    by_arm = defaultdict(list)
    for (tid, arm), it in items.items():
        by_arm[arm].append(it)

    def arm_block(arm):
        its = by_arm.get(arm, [])
        rev = [i for i in its if i["task_family"] in REVISION]
        nc = [i for i in its if i["task_family"] == "no_change_judgment"]
        return {
            "n": len(its),
            "clean_execution": rate(its, "clean_execution"),
            "all_required_completed": rate([i for i in its if not i["valid_no_change"]], "all_required_completed"),
            "required_change_completion_rate": mean([i["completion_rate"] for i in its]),
            "invalid_unchanged": rate([i for i in its if i["task_family"] in REVISION], "invalid_unchanged"),
            "protected_text_accuracy": (round(sum(i["protected_preserved"] for i in its) /
                                        sum(i["protected_total"] for i in its), 3)
                                        if sum(i["protected_total"] for i in its) else None),
            "protected_corruption_count": sum(1 for i in its if i["protected_corruption"]),
            "unauthorized_edit_rate": rate([i for i in its if i["task_family"] in REVISION], "unauthorized_edit"),
            "output_shape_validity": rate([i for i in its if tasks[i["task_id"]]["evaluation_ground_truth"]["expected_output_shape"] != "prose"], "output_shape_ok"),
            "no_change_accuracy": rate(nc, "restraint_correct") if nc else None,
            "critical_failure_count": sum(1 for i in its if i["critical_failure"]),
            "token_cap_hits": sum(1 for i in its if i["token_cap_hit"]),
            "reasoning_traces": sum(1 for i in its if i["reasoning_trace"]),
        }

    mech_by_arm = {arm: arm_block(arm) for arm in ARMS}

    # family x arm
    fam_by_arm = {}
    for arm in ARMS:
        fam_by_arm[arm] = {}
        for fam in set(t["task_family"] for t in tasks.values()):
            its = [i for i in by_arm.get(arm, []) if i["task_family"] == fam]
            if its:
                fam_by_arm[arm][fam] = {"n": len(its), "clean": rate(its, "clean_execution"),
                                        "all_required": rate([i for i in its if not i["valid_no_change"]], "all_required_completed")}

    # focused revision detail
    fr_tasks = [tid for tid, t in tasks.items() if t["task_family"] == "multi_constraint_focused_revision"]
    fr = {}
    for arm in ARMS:
        its = [items[(tid, arm)] for tid in fr_tasks if (tid, arm) in items]
        if not its:
            continue
        dist = Counter(i["completed"] for i in its)
        fr[arm] = {
            "n": len(its),
            "all_required_completed": rate(its, "all_required_completed"),
            "invalid_unchanged": rate(its, "invalid_unchanged"),
            "mean_changes_completed": mean([i["completed"] for i in its]),
            "protected_text_accuracy": round(sum(i["protected_preserved"] for i in its) / sum(i["protected_total"] for i in its), 3) if sum(i["protected_total"] for i in its) else None,
            "unauthorized_edit_rate": rate(its, "unauthorized_edit"),
            "partial_fix_distribution": {str(k): dist.get(k, 0) for k in range(0, 6)},
        }

    # instruction position + critical type (focused revision)
    pos_analysis, ctype_analysis = {}, {}
    for arm in ARMS:
        pos_analysis[arm], ctype_analysis[arm] = {}, {}
        for pos in ("early", "middle", "late"):
            tset = [tid for tid in fr_tasks if tasks[tid]["diagnostics"]["instruction_position"] == pos]
            its = [items[(tid, arm)] for tid in tset if (tid, arm) in items]
            if its:
                pos_analysis[arm][pos] = {
                    "all_required_completed": rate(its, "all_required_completed"),
                    "invalid_unchanged": rate(its, "invalid_unchanged"),
                    "protected_text_accuracy": round(sum(i["protected_preserved"] for i in its) / max(1, sum(i["protected_total"] for i in its)), 3),
                    "clean_execution": rate(its, "clean_execution")}
        for ct in ("required_correction", "protected_text_rule", "unauthorized_rewrite_prohibition", "output_shape_requirement"):
            tset = [tid for tid in fr_tasks if tasks[tid]["diagnostics"]["critical_instruction_type"] == ct]
            its = [items[(tid, arm)] for tid in tset if (tid, arm) in items]
            if its:
                ctype_analysis[arm][ct] = {"clean_execution": rate(its, "clean_execution"),
                                           "all_required_completed": rate(its, "all_required_completed")}

    # precommitted comparisons
    def clean_rate(arm, subset=None):
        its = [items[(tid, arm)] for tid in (subset or tasks) if (tid, arm) in items]
        r = rate(its, "clean_execution")
        return r["rate"]

    def fr_all_req(arm):
        return fr.get(arm, {}).get("all_required_completed", {}).get("rate")

    def invalid_rate(arm):
        its = [items[(tid, arm)] for tid, t in tasks.items()
               if t["task_family"] in REVISION and (tid, arm) in items]
        return rate(its, "invalid_unchanged")["rate"]

    def g(a, b):
        return round(a - b, 3) if (a is not None and b is not None) else None

    p3_subset = json.load(open(os.path.join(HERE, "p3-ideal-subset.json"), encoding="utf-8"))["tasks"]
    canon_tasks = [t for t in p3_subset if tasks[t]["task_family"] == "canon_continuation"]
    voice_tasks = [t for t in p3_subset if tasks[t]["task_family"] == "voice_preserving_revision"]

    effects = {
        "p1_minus_p0_maximal": {
            "clean_execution_gain": g(clean_rate("P1-Contract"), clean_rate("P0-Maximal")),
            "focused_revision_all_required_gain": g(fr_all_req("P1-Contract"), fr_all_req("P0-Maximal")),
            "invalid_unchanged_reduction": g(invalid_rate("P0-Maximal"), invalid_rate("P1-Contract"))},
        "p1_minus_p0_realistic": {
            "clean_execution_gain": g(clean_rate("P1-Contract"), clean_rate("P0-Realistic")),
            "invalid_unchanged_reduction": g(invalid_rate("P0-Realistic"), invalid_rate("P1-Contract"))},
        "p3ideal_minus_p1": {
            "clean_execution_gain": g(clean_rate("P3-Ideal", p3_subset), clean_rate("P1-Contract", p3_subset)),
            "canon_gain": g(clean_rate("P3-Ideal", canon_tasks), clean_rate("P1-Contract", canon_tasks)),
            "voice_gain": g(clean_rate("P3-Ideal", voice_tasks), clean_rate("P1-Contract", voice_tasks))},
    }

    # floors
    p1m = effects["p1_minus_p0_maximal"]
    p1r = effects["p1_minus_p0_realistic"]
    p3 = effects["p3ideal_minus_p1"]
    new_crit_p1_vs_p0max = mech_by_arm["P1-Contract"]["critical_failure_count"] - mech_by_arm["P0-Maximal"]["critical_failure_count"]
    floors = {
        "structure_success": {
            "clean_gain>=0.15": (p1m["clean_execution_gain"] or -9) >= 0.15,
            "focused_all_required_gain>=0.20": (p1m["focused_revision_all_required_gain"] or -9) >= 0.20,
            "invalid_unchanged_reduction>=0.20": (p1m["invalid_unchanged_reduction"] or -9) >= 0.20,
            "no_new_critical_failures": new_crit_p1_vs_p0max <= 0,
            "protected_not_worse": (mech_by_arm["P1-Contract"]["protected_text_accuracy"] or 0) >= (mech_by_arm["P0-Maximal"]["protected_text_accuracy"] or 0),
            "unauthorized_not_worse": (mech_by_arm["P1-Contract"]["unauthorized_edit_rate"]["rate"] or 0) <= (mech_by_arm["P0-Maximal"]["unauthorized_edit_rate"]["rate"] or 0)},
        "practical_product_success": {
            "clean_gain>=0.20": (p1r["clean_execution_gain"] or -9) >= 0.20,
            "invalid_unchanged_reduction>=0.25": (p1r["invalid_unchanged_reduction"] or -9) >= 0.25,
            "no_new_critical_failures": mech_by_arm["P1-Contract"]["critical_failure_count"] - mech_by_arm["P0-Realistic"]["critical_failure_count"] <= 0},
        "ideal_packet_signal": {
            "clean_gain>=0.10": (p3["clean_execution_gain"] or -9) >= 0.10,
            "canon_or_voice_gain>=0.15": max((p3["canon_gain"] or -9), (p3["voice_gain"] or -9)) >= 0.15,
            "no_new_critical_failures": True},
    }
    for k in floors:
        floors[k]["PASS"] = all(v for kk, v in floors[k].items() if kk != "PASS")

    # anti-results (P1 vs P0-Maximal primary)
    anti = {
        "new_protected_text_corruption": mech_by_arm["P1-Contract"]["protected_corruption_count"] - mech_by_arm["P0-Maximal"]["protected_corruption_count"],
        "unauthorized_edit_rate_increase": (mech_by_arm["P1-Contract"]["unauthorized_edit_rate"]["rate"] or 0) > (mech_by_arm["P0-Maximal"]["unauthorized_edit_rate"]["rate"] or 0),
        "no_change_accuracy_drop": g((mech_by_arm["P0-Maximal"]["no_change_accuracy"] or {}).get("rate"), (mech_by_arm["P1-Contract"]["no_change_accuracy"] or {}).get("rate")),
        "new_critical_failures_p1_vs_p0max": new_crit_p1_vs_p0max,
        "forbidden_violations_by_arm": {arm: sum(len(i["forbidden_violations"]) for i in by_arm.get(arm, [])) for arm in ARMS},
    }

    results = {
        "dispatch": "28B", "instrument": "linewright-prompt-execution-v1",
        "scored_outputs": len(items),
        "mechanical_by_arm": mech_by_arm, "family_by_arm": fam_by_arm,
        "focused_revision": fr, "effects": effects, "effect_floors": floors,
        "anti_results": anti,
    }
    item_level = {f"{tid}::{arm}": it for (tid, arm), it in items.items()}
    os.makedirs(RUN, exist_ok=True)
    json.dump(results, open(os.path.join(RUN, "mechanical-results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(item_level, open(os.path.join(RUN, "item-level-results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"instruction_position": pos_analysis, "critical_instruction_type": ctype_analysis},
              open(os.path.join(RUN, "instruction-position-analysis.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(anti, open(os.path.join(RUN, "anti-result-analysis.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(json.dumps({"scored": len(items),
                      "clean_execution": {a: mech_by_arm[a]["clean_execution"]["rate"] for a in ARMS},
                      "fr_all_required": {a: fr_all_req(a) for a in ARMS},
                      "effects": {k: v.get("clean_execution_gain") for k, v in effects.items()},
                      "floors": {k: floors[k]["PASS"] for k in floors}}, indent=1))
    return results


if __name__ == "__main__":
    main()
