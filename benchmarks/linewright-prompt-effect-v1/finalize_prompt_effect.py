"""Dispatch 28 — score all Prompt-Effect v1 outputs and aggregate by arm / family / instruction
position, with headline effect sizes and anti-result metrics. Rules come only from the frozen
task manifest via score_prompt_effect.score_output. Writes mechanical-results.json + report.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
from score_prompt_effect import load_tasks, score_output

RUN = os.path.join(_REPO, "benchmarks", "runs", "linewright-prompt-effect-v1")
NORM = os.path.join(RUN, "normalized-results")
ARMS = ["P0-Realistic", "P0-Maximal", "P1-Contract", "P3-Ideal"]
REVISION = "multi_constraint_focused_revision"


def rate(xs, pred):
    xs = list(xs)
    return round(sum(1 for x in xs if pred(x)) / len(xs), 3) if xs else None


def agg(rows):
    n = len(rows)
    if not n:
        return None
    return {
        "n": n,
        "all_required_completed": {"count": sum(1 for r in rows if r["all_required_completed"]),
                                   "total": n, "rate": rate(rows, lambda r: r["all_required_completed"])},
        "mean_required_completion": round(sum(r["required_completed"] / r["required_total"] for r in rows) / n, 3),
        "returned_unchanged": {"count": sum(1 for r in rows if r["returned_unchanged"]),
                               "total": n, "rate": rate(rows, lambda r: r["returned_unchanged"])},
        "protected_accuracy": rate([r for r in rows if r["protected_total"]], lambda r: r["protected_ok"]),
        "protected_corruption_count": sum(1 for r in rows if r["protected_corruption"]),
        "unauthorized_edit_rate": rate(rows, lambda r: r["unauthorized_edit"]),
        "output_shape_validity": rate(rows, lambda r: r["output_shape_ok"]),
        "clean_success_rate": rate(rows, lambda r: r["clean_success"]),
    }


def partial_fix(rows):
    d = {"0": 0, "1": 0, "2": 0, "3": 0, "4+": 0, "all": 0}
    for r in rows:
        c = r["required_completed"]
        d[str(c) if c <= 3 else "4+"] = d.get(str(c) if c <= 3 else "4+", 0) + 1
        if r["all_required_completed"]:
            d["all"] += 1
    return d


def main():
    tasks = load_tasks()
    recs = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(NORM, "*.json")))]
    scored = []
    for r in recs:
        t = tasks[r["task_id"]]
        s = score_output(t, r.get("output_text", ""))
        s.update({"arm": r["arm"], "instruction_position": t["diagnostics"]["instruction_position"],
                  "reasoning_trace": r.get("reasoning_trace_detected", False),
                  "token_cap": r.get("token_cap_hit", False)})
        scored.append(s)

    by_arm = {a: [s for s in scored if s["arm"] == a] for a in ARMS}
    overall_by_arm = {a: agg(rows) for a, rows in by_arm.items() if rows}
    fam_by_arm = {}
    for a in ARMS:
        fam_by_arm[a] = {fam: agg([s for s in by_arm[a] if s["task_family"] == fam])
                         for fam in set(s["task_family"] for s in by_arm[a])}
    rev_by_arm = {a: agg([s for s in by_arm[a] if s["task_family"] == REVISION]) for a in ARMS if by_arm[a]}
    partial_by_arm = {a: partial_fix([s for s in by_arm[a] if s["task_family"] == REVISION]) for a in ARMS if by_arm[a]}
    # instruction position (revision family)
    pos_by_arm = {}
    for a in ARMS:
        if not by_arm[a]:
            continue
        pos_by_arm[a] = {}
        for pos in ("early", "middle", "late"):
            rows = [s for s in by_arm[a] if s["task_family"] == REVISION and s["instruction_position"] == pos]
            pos_by_arm[a][pos] = {"all_required_completed": rate(rows, lambda r: r["all_required_completed"]),
                                  "returned_unchanged": rate(rows, lambda r: r["returned_unchanged"]),
                                  "protected_accuracy": rate([r for r in rows if r["protected_total"]], lambda r: r["protected_ok"]),
                                  "unauthorized_edit_rate": rate(rows, lambda r: r["unauthorized_edit"])} if rows else None

    def eff(a, b, key_path):
        # a - b on a metric; over the SHARED tasks so P3-Ideal (10 tasks) compares fairly
        ta = {s["task_id"]: s for s in by_arm[a]}
        tb = {s["task_id"]: s for s in by_arm[b]}
        shared = sorted(set(ta) & set(tb))
        if not shared:
            return None
        def m(sd):
            return sum(1 for tid in shared if key_path(sd[tid])) / len(shared)
        return round(m(ta) - m(tb), 3)

    completed = lambda r: r["all_required_completed"]
    unchanged = lambda r: r["returned_unchanged"]
    headline = {
        "p1_minus_p0_maximal": {"all_required_completed": eff("P1-Contract", "P0-Maximal", completed),
                                "returned_unchanged": eff("P1-Contract", "P0-Maximal", unchanged)},
        "p1_minus_p0_realistic": {"all_required_completed": eff("P1-Contract", "P0-Realistic", completed),
                                  "returned_unchanged": eff("P1-Contract", "P0-Realistic", unchanged)},
        "p3ideal_minus_p1": {"all_required_completed": eff("P3-Ideal", "P1-Contract", completed),
                             "returned_unchanged": eff("P3-Ideal", "P1-Contract", unchanged)},
        "p3ideal_minus_p0_realistic": {"all_required_completed": eff("P3-Ideal", "P0-Realistic", completed)},
    }
    anti_by_arm = {a: {"protected_corruption": sum(1 for s in by_arm[a] if s["protected_corruption"]),
                       "unauthorized_edit": sum(1 for s in by_arm[a] if s["unauthorized_edit"]),
                       "reasoning_trace": sum(1 for s in by_arm[a] if s["reasoning_trace"]),
                       "token_cap": sum(1 for s in by_arm[a] if s["token_cap"])} for a in ARMS if by_arm[a]}

    integ = {"expected_outputs": 100, "actual_outputs": len(recs),
             "reasoning_trace_count": sum(1 for s in scored if s["reasoning_trace"]),
             "token_cap_count": sum(1 for s in scored if s["token_cap"])}

    out = {"run_id": "linewright-prompt-effect-v1", "generation_integrity": integ,
           "overall_by_arm": overall_by_arm, "family_by_arm": fam_by_arm,
           "focused_revision_by_arm": rev_by_arm, "partial_fix_by_arm": partial_by_arm,
           "instruction_position_by_arm": pos_by_arm, "headline_effects": headline,
           "anti_result_by_arm": anti_by_arm,
           "per_output": [{k: s[k] for k in ("task_id", "arm", "task_family", "all_required_completed",
                          "required_completed", "required_total", "returned_unchanged", "protected_ok",
                          "unauthorized_edit", "clean_success")} for s in scored]}
    with open(os.path.join(RUN, "mechanical-results.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"outputs": len(recs), "overall_all_required": {a: overall_by_arm[a]["all_required_completed"]["rate"] for a in overall_by_arm},
                      "revision_returned_unchanged": {a: rev_by_arm[a]["returned_unchanged"]["rate"] for a in rev_by_arm},
                      "revision_all_required": {a: rev_by_arm[a]["all_required_completed"]["rate"] for a in rev_by_arm},
                      "headline": headline, "anti": anti_by_arm}, indent=1))
    return out


if __name__ == "__main__":
    main()
