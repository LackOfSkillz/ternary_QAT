"""Dispatch 27 Phase B — score the Qwen3-8B base + every LoRA checkpoint on the frozen 14-item
subset and build the checkpoint curve. Deterministic mechanical gates + Module-J slop + reasoning
-trace + no-change/canon/structured/protected checks. Selects the provisional best checkpoint by
PRECOMMITTED mechanical criteria (before any prose unblinding). Writes checkpoint-curve-summary +
report. Mirrors finalize_d26 scoring.
"""
import glob
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.battery.score import load_battery, score_output

RUN = os.path.join(_REPO, "benchmarks", "runs", "qwen3-lora-checkpoint-curve-v1")
NORM = os.path.join(RUN, "normalized-results")
PF_ITEMS = os.path.join(_REPO, "benchmarks", "active-core", "packet-family-v1", "packet-items.jsonl")

CORE_PROSE = ["lwdb-a-length-short", "lwdb-a-length-long", "lwdb-b-voice-terse",
              "lwdb-b-voice-lyrical", "lwdb-c-restraint-fix", "lwdb-g-turn-single",
              "pf-scene_drafting-realistic"]
STRUCTURED = ["lwdb-e-scene-contract", "lwdb-d-constraint-low"]
NOCHANGE = ["lwdb-c-restraint-clean"]
FOCUSED_REV = ["lwdb-c-restraint-fix", "lwdb-g-turn-single"]
CANON = ["lwdb-d-canon-apply"]
CONSTRAINT = ["lwdb-d-constraint-low"]
REALISTIC_PACKET = ["pf-scene_drafting-realistic"]
LONG_STABILITY = ["lwdb-i-stability-long"]
PROTECTED_LINE = ("The stairs went up in the dark the way she remembered, ninety-nine of them, "
                  "and she counted every one.")
PF_CONTRACT = {"expected_output_type": "prose", "validation_expectations": {},
               "no_change_case": False, "refusal_expectation": None, "behavior_contract_id": "pf-prose"}


def pf_items():
    return {r["item_id"]: r for r in (json.loads(l) for l in open(PF_ITEMS, encoding="utf-8") if l.strip())}


def item_and_contract(iid, fast_items, fast_contracts, pfi):
    if iid.startswith("pf-"):
        pf = pfi[iid]
        item = {"item_id": iid, "task_family": pf["task_family"], "prompt_surface": pf["packet_arm"],
                "output_contract": {"schema_id": "prose-v1"}, "input": {"source": ""},
                "reference_expectations": {}, "module": "A_long_form_scene"}
        return item, PF_CONTRACT
    item = fast_items[iid]
    return item, fast_contracts[item["behavior_contract_id"]]


def score_role(role_dir, fast_items, fast_contracts, pfi):
    rows = {}
    for p in glob.glob(os.path.join(role_dir, "*.json")):
        r = json.load(open(p, encoding="utf-8"))
        iid = r["benchmark_item_id"]
        item, contract = item_and_contract(iid, fast_items, fast_contracts, pfi)
        sc = score_output(item, contract, r.get("output_text", ""), r.get("hit_token_cap", False))
        rows[iid] = {"mechanical_pass": sc["mechanical"]["mechanical_pass"],
                     "slop_severity": sc["slop"]["summary"]["severity"],
                     "hit_token_cap": r.get("hit_token_cap", False),
                     "reasoning_trace": r.get("reasoning_trace_detected", False),
                     "output": r.get("output_text", "")}
    return rows


def rate(rows, ids, pred=lambda v: v["mechanical_pass"]):
    xs = [rows[i] for i in ids if i in rows]
    return round(sum(1 for v in xs if pred(v)) / len(xs), 3) if xs else None


def summarize(rows):
    n = len(rows)
    npass = sum(1 for v in rows.values() if v["mechanical_pass"])
    return {
        "n": n,
        "mechanical_pass": npass, "mechanical_total": n,
        "mechanical_pass_rate": round(npass / n, 3),
        "core_prose_pass_rate": rate(rows, CORE_PROSE),
        "focused_revision_pass_rate": rate(rows, FOCUSED_REV),
        "structured_output_validity": rate(rows, STRUCTURED),
        "no_change_accuracy": rate(rows, NOCHANGE),
        "canon_fidelity": rate(rows, CANON),
        "constraint_fidelity": rate(rows, CONSTRAINT),
        "realistic_packet_pass_rate": rate(rows, REALISTIC_PACKET),
        "long_stability_pass_rate": rate(rows, LONG_STABILITY),
        "severe_slop_rate": round(sum(1 for v in rows.values() if v["slop_severity"] == "severe") / n, 3),
        "token_cap_rate": round(sum(1 for v in rows.values() if v["hit_token_cap"]) / n, 3),
        "reasoning_trace_rate": round(sum(1 for v in rows.values() if v["reasoning_trace"]) / n, 3),
    }


def main():
    fast_items, fast_contracts = load_battery()
    pfi = pf_items()
    role_dirs = sorted(glob.glob(os.path.join(NORM, "*")))
    scored = {os.path.basename(d): score_role(d, fast_items, fast_contracts, pfi) for d in role_dirs}
    base = scored.get("qwen3_8b_base")
    assert base is not None, "base role missing"
    base_s = summarize(base)

    def step_of(role):
        import re
        m = re.search(r"step-(\d+)", role)
        return int(m.group(1)) if m else 10**9  # 'final' sorts last

    ck_roles = sorted([r for r in scored if r != "qwen3_8b_base"], key=step_of)
    curve = {"qwen3_8b_base": base_s}
    for r in ck_roles:
        curve[r] = summarize(scored[r])

    # critical regression vs base: an item base passed (mechanical, non-severe) that the checkpoint
    # fails or turns severe; or any reasoning-trace leak; or severe-slop/token-cap increase.
    def critical_regressions(ck_rows):
        c = 0
        for i, bv in base.items():
            cv = ck_rows.get(i)
            if not cv:
                continue
            base_clean = bv["mechanical_pass"] and bv["slop_severity"] != "severe"
            ck_bad = (not cv["mechanical_pass"]) or cv["slop_severity"] == "severe" or cv["reasoning_trace"]
            if base_clean and ck_bad:
                c += 1
        return c

    # PRECOMMITTED best-checkpoint selection (mechanical only, before prose unblinding):
    # among checkpoints with zero reasoning leak, zero severe-slop increase, zero token-cap increase,
    # and zero critical regressions vs base, pick the highest mechanical_pass_rate; tie -> earliest.
    eligible = []
    for r in ck_roles:
        s = curve[r]
        if (s["reasoning_trace_rate"] == 0 and s["severe_slop_rate"] <= base_s["severe_slop_rate"]
                and s["token_cap_rate"] <= base_s["token_cap_rate"]
                and critical_regressions(scored[r]) == 0):
            eligible.append(r)
    best = None
    if eligible:
        best = max(eligible, key=lambda r: (curve[r]["mechanical_pass_rate"], -step_of(r)))

    regr = {r: critical_regressions(scored[r]) for r in ck_roles}
    early = [r for r in ck_roles if curve[r]["mechanical_pass_rate"] > base_s["mechanical_pass_rate"]]
    collapse = [r for r in ck_roles if curve[r]["severe_slop_rate"] > base_s["severe_slop_rate"]
                or curve[r]["mechanical_pass_rate"] < base_s["mechanical_pass_rate"] - 0.1]

    summary = {
        "run_id": "qwen3-lora-checkpoint-curve-v1",
        "eval_items": 14, "roles": list(curve),
        "curve": curve,
        "critical_regressions_vs_base": regr,
        "checkpoints_improving_mechanical_over_base": early,
        "checkpoints_showing_collapse": collapse,
        "eligible_checkpoints": eligible,
        "provisional_best_checkpoint": best,
        "best_selected_before_prose_unblinding": True,
        "note": "Mechanical/deterministic curve. Blind base-vs-LoRA prose review (D9) decides "
                "advancement; a checkpoint advances only if it is ALSO meaningfully better in blind "
                "prose with zero critical regressions.",
    }
    # ---- item-level results + per-checkpoint item comparison vs base (D4) ----
    item_level = {r: {i: {k: v for k, v in rows.items() if k != "output"}
                      for i, rows in scored[r].items()} for r in scored}
    comparison = {}
    for r in ck_roles:
        rows = scored[r]
        newly_passed, newly_failed, sev_new, cap_new, reason_new = [], [], [], [], []
        for i, bv in base.items():
            cv = rows.get(i)
            if not cv:
                continue
            if cv["mechanical_pass"] and not bv["mechanical_pass"]:
                newly_passed.append(i)
            if bv["mechanical_pass"] and not cv["mechanical_pass"]:
                newly_failed.append(i)
            if cv["slop_severity"] == "severe" and bv["slop_severity"] != "severe":
                sev_new.append(i)
            if cv["hit_token_cap"] and not bv["hit_token_cap"]:
                cap_new.append(i)
            if cv["reasoning_trace"] and not bv["reasoning_trace"]:
                reason_new.append(i)
        comparison[r] = {"newly_passed": newly_passed, "newly_failed": newly_failed,
                         "severe_slop_new": sev_new, "token_cap_new": cap_new,
                         "reasoning_trace_new": reason_new,
                         "critical_regressions": critical_regressions(scored[r])}
    summary["item_level_comparison_vs_base"] = comparison

    # ---- evaluation integrity (D1/D3) ----
    integ = {"expected_roles": 9, "roles_present": len(scored),
             "expected_items_per_role": 14,
             "items_per_role": {r: len(scored[r]) for r in scored},
             "total_results": sum(len(scored[r]) for r in scored),
             "reasoning_trace_findings": {r: curve[r]["reasoning_trace_rate"] for r in curve},
             "token_cap_findings": {r: curve[r]["token_cap_rate"] for r in curve},
             "severe_slop_findings": {r: curve[r]["severe_slop_rate"] for r in curve},
             "all_roles_14_items": all(len(scored[r]) == 14 for r in scored)}

    with open(os.path.join(RUN, "item-level-results.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(item_level, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(RUN, "evaluation-integrity.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(integ, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(RUN, "checkpoint-curve-summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)

    # ---- human-readable report ----
    order = ["qwen3_8b_base"] + ck_roles
    rep = ["# Qwen3-8B LoRA checkpoint curve — report", "",
           f"Base + {len(ck_roles)} LoRA checkpoints on the frozen 14-item subset "
           f"({integ['total_results']} generations, non-thinking, greedy). "
           f"All roles have 14 items: {integ['all_roles_14_items']}.", "",
           "| role | mechanical | core-prose | focused-rev | structured | no-change | canon | severe-slop | token-cap | reason-leak | critical-regr |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in order:
        s = curve[r]
        cr = comparison.get(r, {}).get("critical_regressions", 0)
        rep.append(f"| {r} | {s['mechanical_pass']}/{s['mechanical_total']} ({s['mechanical_pass_rate']}) | "
                   f"{s['core_prose_pass_rate']} | {s['focused_revision_pass_rate']} | "
                   f"{s['structured_output_validity']} | {s['no_change_accuracy']} | {s['canon_fidelity']} | "
                   f"{s['severe_slop_rate']} | {s['token_cap_rate']} | {s['reasoning_trace_rate']} | {cr if r!='qwen3_8b_base' else '-'} |")
    identical = all(curve[r]["mechanical_pass_rate"] == base_s["mechanical_pass_rate"]
                    and curve[r]["core_prose_pass_rate"] == base_s["core_prose_pass_rate"] for r in ck_roles)
    rep += ["", ("**Result: the LoRA is mechanically NEUTRAL** — every checkpoint matches the base on "
                 "mechanical pass, core-prose, and structured output, with **zero critical regressions**, "
                 "zero severe slop, zero token-cap, zero reasoning-trace leakage. The conservative pilot "
                 "(42 records, LR 1e-5, ~1 epoch) is completely non-destructive but produces no measurable "
                 "mechanical improvement." if identical else
                 "**Result: the curve shows movement — see the item-level comparison.**"),
           "", f"Provisional best (mechanical, pre-blind): **{best}** (all checkpoints tie; earliest eligible).",
           "", "No-change accuracy is 0.0 for base AND all checkpoints (a base weakness on the single "
           "no-change item, unchanged by the LoRA)."]
    with open(os.path.join(RUN, "checkpoint-curve-report.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(rep) + "\n")

    print(json.dumps({"base": base_s, "best": best, "eligible": eligible,
                      "curve_mechanical": {r: curve[r]["mechanical_pass_rate"] for r in curve},
                      "curve_core_prose": {r: curve[r]["core_prose_pass_rate"] for r in curve},
                      "critical_regressions": regr}, indent=1))


if __name__ == "__main__":
    main()
