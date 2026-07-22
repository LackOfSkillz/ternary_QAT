"""Dispatch 27 Phase A — score BF16 (reused D26) vs official Q4_K_M and check the frozen
Q4-preservation floor. Deterministic mechanical gates + Module-J slop over the 15 frozen
confirmation prose tasks per precision; computes Q4-vs-BF16 deltas and applies
qwen-q4-confirmation-floor-v0 (frozen before scoring). Writes q4-preservation-summary.json.
"""
import glob
import json
import os
import sys

import yaml

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.battery.score import load_battery, score_output

RUN = os.path.join(_REPO, "benchmarks", "runs", "qwen-prose-confirmation-v1")
Q4 = os.path.join(RUN, "normalized-results", "q4")
D26 = os.path.join(_REPO, "benchmarks", "runs", "lwdb-stronger-base-v1", "normalized-results")
PF_ITEMS = os.path.join(_REPO, "benchmarks", "active-core", "packet-family-v1", "packet-items.jsonl")
FLOOR = os.path.join(_REPO, "benchmarks", "thresholds", "qwen-q4-confirmation-floor-v0.yaml")

CONF = ["lwdb-a-length-short", "lwdb-a-length-long", "lwdb-a-quiet-scene", "lwdb-c-restraint-fix",
        "lwdb-b-voice-terse", "lwdb-b-voice-lyrical", "lwdb-g-turn-single",
        "pf-scene_drafting-bare", "pf-scene_drafting-realistic", "pf-scene_drafting-long",
        "pf-focused_revision-compact", "pf-focused_revision-realistic",
        "pf-focused_revision-long_salience_repaired",
        "pf-canon_sensitive_continuation-realistic", "pf-canon_sensitive_continuation-long"]

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


def score_dir(records, fast_items, fast_contracts, pfi):
    out = {}
    for r in records:
        iid = r["benchmark_item_id"]
        if iid not in CONF:
            continue
        item, contract = item_and_contract(iid, fast_items, fast_contracts, pfi)
        sc = score_output(item, contract, r.get("output_text", ""), r.get("hit_token_cap", False))
        out[iid] = {"mechanical_pass": sc["mechanical"]["mechanical_pass"],
                    "slop_severity": sc["slop"]["summary"]["severity"],
                    "hit_token_cap": r.get("hit_token_cap", False),
                    "reasoning_trace": r.get("reasoning_trace_detected", False),
                    "output_tokens": r.get("output_tokens")}
    return out


def agg(scored):
    n = len(scored)
    return {"n": n,
            "mechanical_pass_rate": round(sum(1 for v in scored.values() if v["mechanical_pass"]) / n, 3),
            "severe_slop_rate": round(sum(1 for v in scored.values() if v["slop_severity"] == "severe") / n, 3),
            "token_cap_rate": round(sum(1 for v in scored.values() if v["hit_token_cap"]) / n, 3),
            "reasoning_trace_rate": round(sum(1 for v in scored.values() if v["reasoning_trace"]) / n, 3)}


def main():
    fast_items, fast_contracts = load_battery()
    pfi = pf_items()
    q4_recs = [json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(Q4, "*.json"))]
    bf16_recs = [json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(D26, "*qwen3_8b_non_thinking.json"))]
    q4 = score_dir(q4_recs, fast_items, fast_contracts, pfi)
    bf16 = score_dir(bf16_recs, fast_items, fast_contracts, pfi)
    assert set(q4) == set(CONF), sorted(set(CONF) - set(q4))
    assert set(bf16) == set(CONF), sorted(set(CONF) - set(bf16))

    q4a, bf16a = agg(q4), agg(bf16)
    floor = yaml.safe_load(open(FLOOR, encoding="utf-8"))["q4_preservation"]
    deltas = {
        "mechanical_pass_drop": round(bf16a["mechanical_pass_rate"] - q4a["mechanical_pass_rate"], 3),
        "severe_slop_increase": round(q4a["severe_slop_rate"] - bf16a["severe_slop_rate"], 3),
        "token_cap_increase": round(q4a["token_cap_rate"] - bf16a["token_cap_rate"], 3),
        "q4_reasoning_leak": q4a["reasoning_trace_rate"],
    }
    checks = {
        "mechanical_pass_drop_ok": deltas["mechanical_pass_drop"] <= floor["max_mechanical_pass_rate_drop"]["value"],
        "severe_slop_increase_ok": deltas["severe_slop_increase"] <= floor["max_severe_slop_rate_increase"]["value"],
        "token_cap_increase_ok": deltas["token_cap_increase"] <= floor["max_token_cap_rate_increase"]["value"],
        "no_reasoning_leak": deltas["q4_reasoning_leak"] == 0,
    }
    summary = {"dispatch": 27, "phase": "A", "confirmation_set_size": len(CONF),
               "bf16_reference": bf16a, "q4_k_m": q4a, "deltas_q4_vs_bf16": deltas,
               "mechanical_floor_checks": checks,
               "mechanical_preservation_pass": all(checks.values()),
               "note": "Mechanical/deterministic Q4-preservation only. Blind PROSE preservation is "
                       "scored separately (LM sub-agents = supporting; Gary + independent human = "
                       "the deciding gate).",
               "per_item": {iid: {"bf16": bf16[iid], "q4": q4[iid]} for iid in CONF}}
    with open(os.path.join(RUN, "q4-preservation-summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"bf16": bf16a, "q4": q4a, "deltas": deltas, "checks": checks,
                      "mechanical_preservation_pass": summary["mechanical_preservation_pass"]}, indent=1))


if __name__ == "__main__":
    main()
