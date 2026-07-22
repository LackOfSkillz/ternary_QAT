"""Finalize the Dispatch-26 stronger-base run: score, verify integrity, aggregate per model.

Consumes the frozen plan + collected normalized results (all three roles). Scores every output
with the Dispatch-21 mechanical gates + Dispatch-23 Module-J slop (reusing battery.score),
adds packet-family supplementary deterministic checks (protected-line preservation, anachronism,
canon-date fidelity), verifies output/prompt/contract/gen-settings hashes + deterministic
mechanical replay, and writes:

  item-level-results.json   per (item, role): mechanical_pass, slop_severity, hit_token_cap,
                            reasoning_trace_detected, packet checks, integrity
  run-summary.json          per-role rates incl. core_prose_pass_rate (fast A+B), packet-arm rates

4B control on the fast battery is NOT rerun here (reused from Dispatch 24). Model identity stays
in these artifacts and is stripped before any reviewer packet.
"""
import glob
import hashlib
import json
import os
import re
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.battery.score import load_battery, score_output, spec_for
from linewright.evaluation.execution.plan import verify_plan_hash
from linewright.evaluation.gates import evaluate_response
from linewright.evaluation.calibration.replay import replay, replay_passed

RUN_DIR = os.path.join(_REPO, "benchmarks", "runs", "lwdb-stronger-base-v1")
NORM = os.path.join(RUN_DIR, "normalized-results")
PF_ITEMS = os.path.join(_REPO, "benchmarks", "active-core", "packet-family-v1", "packet-items.jsonl")

CORE_PROSE_MODULES = ("A_long_form_scene", "B_focused_revision")
PROTECTED_LINE = ("The stairs went up in the dark the way she remembered, ninety-nine of them, "
                  "and she counted every one.")
ANACHRONISMS = ["phone", "mobile", "internet", "email", "text message", "smartphone", "laptop"]
CANON_BAD_DATES = ["1970", "1972", "1969", "1973"]   # decommission/loss canon is 1971 / 14 Nov 1971


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_pf_items():
    return {r["item_id"]: r for r in (json.loads(l) for l in open(PF_ITEMS, encoding="utf-8") if l.strip())}


def synth_packet_item(pf):
    """Build a score_output-compatible item dict for a packet-family record (all prose)."""
    return {
        "item_id": pf["item_id"],
        "module": "A_long_form_scene" if pf["task_family"] == "scene_drafting" else "B_focused_revision",
        "task_family": pf["task_family"],
        "prompt_surface": pf["packet_arm"],
        "output_contract": {"schema_id": "prose-v1"},
        "input": {"source": ""},
        "reference_expectations": {},
    }


PF_CONTRACT = {"expected_output_type": "prose", "validation_expectations": {},
               "no_change_case": False, "refusal_expectation": None,
               "behavior_contract_id": "pf-prose"}


def packet_checks(pf, text):
    tf = pf["task_family"]
    low = text.lower()
    out = {}
    if "pe-opening-line" in pf.get("protected_ids", []):
        out["protected_line_preserved"] = PROTECTED_LINE in text
    out["anachronism_present"] = any(a in low for a in ANACHRONISMS)
    out["canon_date_1971_ok"] = ("1971" in text) or (tf == "scene_drafting")  # date only required where relevant
    out["wrong_canon_date"] = any(d in text for d in CANON_BAD_DATES)
    if tf == "canon_sensitive_continuation":
        out["logbook_fact_present"] = ("23:40" in text or "did not go down" in low or "not return" in low)
    return out


def main():
    plan = json.load(open(os.path.join(RUN_DIR, "generation-plan.json"), encoding="utf-8"))
    assert verify_plan_hash(plan), "plan hash does not verify"
    fast_items, fast_contracts = load_battery()
    pf_items = load_pf_items()
    results = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(NORM, "*.json")))]
    print(f"collected {len(results)} normalized results")

    # integrity
    problems, seen, replays = [], set(), []
    rows = []
    for r in results:
        iid, role, jid = r["benchmark_item_id"], r["model_role"], r["job_id"]
        if jid in seen:
            problems.append(f"dup {jid}")
        seen.add(jid)
        if r["output_hash"] != _sha(r["output_text"]):
            problems.append(f"{jid}: output hash mismatch")
        if r["prompt_hash"] != plan["item_hashes"].get(iid):
            problems.append(f"{jid}: prompt hash != plan")
        if r["generation_settings_hash"] != plan["generation_settings_hash"]:
            problems.append(f"{jid}: gen-settings hash != plan")
        allowed = plan["items"][iid].get("model_roles", plan["model_roles"])
        if role not in allowed:
            problems.append(f"{jid}: role {role} not allowed for {iid}")

        is_pf = iid.startswith("pf-")
        if is_pf:
            item = synth_packet_item(pf_items[iid])
            contract = PF_CONTRACT
        else:
            item = fast_items[iid]
            contract = fast_contracts[item["behavior_contract_id"]]
        scored = score_output(item, contract, r.get("output_text", ""), r.get("hit_token_cap", False))
        spec = spec_for(item, contract)
        rep = replay("battery-mechanical", "v1",
                     lambda out: evaluate_response(out, spec, hit_token_cap=r.get("hit_token_cap", False)),
                     r["output_text"])
        replays.append(rep)
        row = {"item_id": iid, "model_role": role,
               "mechanical_pass": scored["mechanical"]["mechanical_pass"],
               "failure_labels": scored["mechanical"]["failure_labels"],
               "slop_severity": scored["slop"]["summary"]["severity"],
               "hit_token_cap": r.get("hit_token_cap", False),
               "output_tokens": r.get("output_tokens"),
               "reasoning_trace_detected": r.get("reasoning_trace_detected", False),
               "is_packet": is_pf}
        if is_pf:
            row["packet_arm"] = pf_items[iid]["packet_arm"]
            row["task_family"] = pf_items[iid]["task_family"]
            row["packet_checks"] = packet_checks(pf_items[iid], r.get("output_text", ""))
        rows.append(row)

    expected = sum(len(plan["items"][i].get("model_roles", plan["model_roles"])) for i in plan["item_ids"])
    integ = {"expected_jobs": expected, "got_jobs": len(results),
             "missing": expected - len(results), "problems": problems,
             "mechanical_replay_identical": replay_passed(replays)}

    # per-role aggregation
    by_role = {}
    for row in rows:
        by_role.setdefault(row["model_role"], []).append(row)
    summary = {}
    for role, rr in by_role.items():
        fast = [x for x in rr if not x["is_packet"]]
        pf = [x for x in rr if x["is_packet"]]
        core = [x for x in fast if fast_items.get(x["item_id"], {}).get("module") in CORE_PROSE_MODULES
                and fast_contracts.get(fast_items[x["item_id"]]["behavior_contract_id"], {}).get("expected_output_type") == "prose"]
        def rate(xs, pred=lambda x: x["mechanical_pass"]):
            return round(sum(1 for x in xs if pred(x)) / len(xs), 3) if xs else None
        arm_rates = {}
        for arm in ["bare", "compact", "realistic", "long", "long_noisy", "long_salience_repaired"]:
            a = [x for x in pf if x.get("packet_arm") == arm]
            arm_rates[arm] = rate(a)
        # feasibility inputs over the FAST battery (comparable to the 4B Dispatch-24 baseline)
        bare_fast = [x for x in fast if fast_items.get(x["item_id"], {}).get("prompt_surface") == "bare"]
        mods = {}
        for x in fast:
            m = fast_items.get(x["item_id"], {}).get("module", "?")[0]
            usable = x["mechanical_pass"] and x["slop_severity"] != "severe"
            mods[m] = mods.get(m, False) or usable
        summary[role] = {
            "n_fast": len(fast), "n_packet": len(pf),
            "fast_mechanical_pass_rate": rate(fast),
            "core_prose_pass_rate": rate(core),
            "core_prose_n": len(core),
            "bare_success_rate": rate(bare_fast),
            "modules_with_usable": sum(1 for v in mods.values() if v),
            "realistic_packet_pass_rate": arm_rates.get("realistic"),
            "severe_slop_rate": rate(rr, lambda x: x["slop_severity"] == "severe"),
            "token_cap_rate": rate(rr, lambda x: x["hit_token_cap"]),
            "reasoning_trace_rate": rate(rr, lambda x: x["reasoning_trace_detected"]),
            "packet_arm_pass_rates": arm_rates,
            "protected_line_preserved_rate": rate(
                [x for x in pf if "protected_line_preserved" in x.get("packet_checks", {})],
                lambda x: x["packet_checks"]["protected_line_preserved"]),
            "anachronism_rate": rate(pf, lambda x: x.get("packet_checks", {}).get("anachronism_present", False)),
        }

    with open(os.path.join(RUN_DIR, "item-level-results.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(RUN_DIR, "run-summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"run_id": "lwdb-stronger-base-v1", "plan_hash": plan["plan_hash"],
                   "integrity": integ, "per_role": summary}, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"integrity": integ, "per_role_core_prose": {
        r: summary[r]["core_prose_pass_rate"] for r in summary}}, indent=1))


if __name__ == "__main__":
    main()
