"""Score fast-battery outputs (Dispatch 24, Workstreams H + I).

Runs the Dispatch-21 mechanical gates and the Dispatch-23 Module-J slop analysis over each
normalized output, and builds per-role corpus slop summaries. Deterministic; one mechanical
result + one slop report per output. Structured (JSON/YAML) items get a slop report marked
prose-not-applicable for prose-specific dimensions.
"""
import json
import os

from linewright import config as C
from linewright.evaluation import contracts as contract_mod
from linewright.evaluation.gates import evaluate_response, gate_summary, GateResult
from linewright.evaluation.slop.report import build_slop_report
from linewright.evaluation.slop.corpus import corpus_slop_summary

BATTERY_DIR = os.path.join("benchmarks", "active-core", "fast-v1")


def _load(name):
    p = C.abs_repo(os.path.join(BATTERY_DIR, name))
    return {r["item_id"]: r for r in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}


def load_battery():
    items = _load("items.jsonl")
    contracts = {c["contract_id"]: c for c in
                 (json.loads(l) for l in open(C.abs_repo(os.path.join(BATTERY_DIR, "contracts.jsonl")),
                                              encoding="utf-8") if l.strip())}
    return items, contracts


def spec_for(item, contract):
    oc = contract_mod.resolve(item["output_contract"])
    exps = dict(contract.get("validation_expectations") or {})
    exps.update(item.get("reference_expectations") or {})
    if exps.get("changed") is False:
        oc = dict(oc, expects_no_change=True)
    return {"output_contract": oc, "source": item["input"].get("source", ""),
            "gold": "", "validation_expectations": exps, "train_targets": []}


def score_output(item, contract, output_text, hit_token_cap=False):
    spec = spec_for(item, contract)
    gm = evaluate_response(output_text, spec, hit_token_cap=hit_token_cap)
    summ = gate_summary(gm)
    mech = {"item_id": item["item_id"], "gates": summ["gates"],
            "mechanical_pass": summ["mechanical_pass"], "failure_labels": sorted(
                {l for v in gm.values() if isinstance(v, GateResult) for l in v.failure_labels})}
    is_prose = contract["expected_output_type"] == "prose"
    slop = build_slop_report(output_text, output_id=item["item_id"],
                             detector_manifest_id="lwdb-fast-v1",
                             source=item["input"].get("source") or None,
                             hit_token_cap=hit_token_cap,
                             input_characteristics={"task_type": item["task_family"],
                                                     "prompt_surface": item["prompt_surface"]})
    if not is_prose:
        slop["summary"]["limitations"].append("structured output: prose-specific slop "
                                               "dimensions not applicable")
    return {"mechanical": mech, "slop": slop}


def score_run(normalized_results):
    """``normalized_results`` = list of records with benchmark_item_id, model_role, output_text,
    hit_token_cap. Returns per-output scores + per-role corpus summaries (identity kept here;
    stripped before reviewer packets)."""
    items, contracts = load_battery()
    per_output, by_role_outputs = [], {}
    for r in normalized_results:
        iid, role = r["benchmark_item_id"], r["model_role"]
        item = items[iid]
        contract = contracts[item["behavior_contract_id"]]
        scored = score_output(item, contract, r.get("output_text", ""),
                              r.get("hit_token_cap", False))
        per_output.append({"result_id": r.get("result_id"), "item_id": iid, "model_role": role,
                           **scored})
        if contract["expected_output_type"] == "prose":
            by_role_outputs.setdefault(role, []).append(
                {"output_id": f"{role}:{iid}", "text": r.get("output_text", "")})
    corpus = {role: corpus_slop_summary(outs, role) for role, outs in by_role_outputs.items()}
    return {"per_output": per_output, "corpus_summaries": corpus}
