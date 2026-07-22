"""Build a frozen generation plan from the fast battery (Dispatch 24, Workstream F4).

Assembles each benchmark item into a single prompt (system + task instruction + any source /
context / canon / hard constraints), then freezes a hashed plan via the Dispatch-23 plan
module. target_base and new_candidate share every benchmark-semantic field; only host /
endpoint / model identity / revision differ. Secrets are referenced, never serialized.
"""
import json
import os

from linewright import config as C
from linewright.evaluation.execution.plan import create_plan

BATTERY_DIR = os.path.join("benchmarks", "active-core", "fast-v1")


def _load(name):
    p = C.abs_repo(os.path.join(BATTERY_DIR, name))
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def assemble_prompt(item, contract):
    inp = item["input"]
    parts = [inp["task_instruction"]]
    if inp.get("source"):
        parts.append("\n\nSOURCE:\n" + inp["source"])
    if inp.get("context"):
        parts.append("\n\nCONTEXT:\n" + inp["context"])
    if inp.get("canon"):
        parts.append("\n\nCANON:\n- " + "\n- ".join(inp["canon"]))
    if inp.get("hard_constraints"):
        parts.append("\n\nHARD CONSTRAINTS:\n- " + "\n- ".join(inp["hard_constraints"]))
    return {"system": inp["system_instruction"], "user": "".join(parts)}


def build_plan(*, base_descriptor, candidate_descriptor, generation_settings, seeds,
               max_new_tokens, output_directory, execution_mode="parallel_multi_host",
               scheduling_policy="round_robin", plan_id="lwdb-fast-v1-run",
               retry_policy_id="default", created_at="unset"):
    items_raw = _load("items.jsonl")
    contracts = {c["contract_id"]: c for c in _load("contracts.jsonl")}
    plan_items = []
    for it in items_raw:
        c = contracts[it["behavior_contract_id"]]
        prompt = assemble_prompt(it, c)
        plan_items.append({
            "item_id": it["item_id"],
            "prompt": json.dumps(prompt, sort_keys=True, ensure_ascii=False),
            "behavior_contract": {"contract_id": c["contract_id"],
                                  "output_schema_id": c["output_schema_id"],
                                  "expected_output_type": c["expected_output_type"],
                                  "forbidden_failures": c["forbidden_failures"],
                                  "validation_expectations": c["validation_expectations"],
                                  "no_change_case": c["no_change_case"],
                                  "refusal_expectation": c["refusal_expectation"]},
            "model_roles": ["target_base", "new_candidate"],
        })
    return create_plan(
        battery_version="fast-v1", battery_profile="fast", execution_mode=execution_mode,
        scheduling_policy=scheduling_policy, items=plan_items,
        model_descriptors={"target_base": base_descriptor, "new_candidate": candidate_descriptor},
        generation_settings=generation_settings, seeds=seeds, max_new_tokens=max_new_tokens,
        retry_policy_id=retry_policy_id, output_directory=output_directory,
        created_at=created_at, plan_id=plan_id)


def endpoint_descriptor(endpoint_id, endpoint_type, model_name, host_id, *, base_url=None,
                        auth_env=None, model_roles=None):
    """A committable endpoint descriptor. Auth is a REFERENCE (ENV name), never a literal key."""
    d = {"endpoint_id": endpoint_id, "endpoint_type": endpoint_type, "model_name": model_name,
         "host_metadata": {"host_id": host_id},
         "supported_parameters": ["temperature", "top_p", "max_new_tokens", "seed", "stop"],
         "unsupported_parameters": []}
    if base_url:
        d["base_url"] = base_url
    if auth_env:
        d["authentication_source"] = f"ENV:{auth_env}"
    if model_roles:
        d["host_metadata"]["model_roles"] = model_roles
    return d
