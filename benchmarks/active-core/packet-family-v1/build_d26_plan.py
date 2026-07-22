"""Freeze the Dispatch-26 stronger-base generation plan (committed BEFORE generation).

Merges the frozen Fast Battery v1 items (candidates only; 4B control reused from Dispatch 24)
with the new Packet-Family v1 items (all three roles) into ONE hashed plan. Per-item
model_roles restrict which roles run each item, so the plan enumerates exactly 94 new jobs:
  * fast battery: 20 items x {ministral, qwen}          = 40
  * packet family: 18 items x {4b, ministral, qwen}     = 54

Model descriptors carry identity/revision/tokenizer_revision + a non-secret loader hint and
the Qwen non-thinking flag. Secrets never appear. The plan hash covers benchmark semantics
only (see execution/plan.py).
"""
import json
import os

from linewright.evaluation.execution.plan import create_plan, verify_plan_hash
from linewright.evaluation.battery.plan_builder import assemble_prompt

FAST = os.path.join("benchmarks", "active-core", "fast-v1")
PF = os.path.join("benchmarks", "active-core", "packet-family-v1")

MINISTRAL = "ministral_3_8b_instruct"
QWEN = "qwen3_8b_non_thinking"
BASE4B = "target_base_4b"

DESCRIPTORS = {
    BASE4B: {
        "identity": "prism-ml/Ternary-Bonsai-4B-unpacked", "revision": "unpacked",
        "tokenizer_revision": "unpacked", "endpoint_id": "ep-4b",
        "loader": "causal_lm", "enable_thinking": None, "precision": "bf16_unpacked",
        "chat_template": "model_default", "system_prompt": None},
    MINISTRAL: {
        "identity": "mistralai/Ministral-3-8B-Instruct-2512",
        "revision": "5b26027e7b19eeb4b7352e1fed3926375dd2cb4d",
        "tokenizer_revision": "5b26027e7b19eeb4b7352e1fed3926375dd2cb4d",
        "endpoint_id": "ep-ministral", "loader": "mistral3_text_only",
        "enable_thinking": None, "precision": "fp8_official", "modality": "text_only",
        "chat_template": "chat_template.jinja", "system_prompt": None},
    QWEN: {
        "identity": "Qwen/Qwen3-8B",
        "revision": "b968826d9c46dd6066d109eabc6255188de91218",
        "tokenizer_revision": "b968826d9c46dd6066d109eabc6255188de91218",
        "endpoint_id": "ep-qwen", "loader": "causal_lm", "enable_thinking": False,
        "precision": "bf16", "chat_template": "model_default", "system_prompt": None},
}


def _read_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def _fast_items():
    items = _read_jsonl(os.path.join(FAST, "items.jsonl"))
    contracts = {c["contract_id"]: c for c in _read_jsonl(os.path.join(FAST, "contracts.jsonl"))}
    out = []
    for it in items:
        c = contracts[it["behavior_contract_id"]]
        prompt = assemble_prompt(it, c)
        out.append({
            "item_id": it["item_id"],
            "prompt": json.dumps(prompt, sort_keys=True, ensure_ascii=False),
            "behavior_contract": {"contract_id": c["contract_id"],
                                  "output_schema_id": c["output_schema_id"],
                                  "expected_output_type": c["expected_output_type"],
                                  "forbidden_failures": c["forbidden_failures"],
                                  "validation_expectations": c["validation_expectations"],
                                  "no_change_case": c["no_change_case"],
                                  "refusal_expectation": c["refusal_expectation"]},
            "model_roles": [MINISTRAL, QWEN],   # 4B reused from Dispatch 24
        })
    return out


def _packet_items():
    items = _read_jsonl(os.path.join(PF, "packet-items.jsonl"))
    out = []
    for it in items:
        contract = {
            "contract_id": f"pf-{it['task_family']}", "output_schema_id": "prose-v1",
            "expected_output_type": it["output_type"],
            "forbidden_failures": ["empty_output", "repeated_ngram", "runaway_length",
                                   "duplicate_sentence"],
            "validation_expectations": {"protected_ids": it["protected_ids"]},
            "no_change_case": False,
            "refusal_expectation": None}
        out.append({
            "item_id": it["item_id"], "prompt": it["prompt"],
            "behavior_contract": contract,
            "model_roles": [BASE4B, MINISTRAL, QWEN],
        })
    return out


def build(created_at="2026-07-22", output_directory="benchmarks/runs/lwdb-stronger-base-v1"):
    items = _fast_items() + _packet_items()
    seeds = {r: 20260722 for r in DESCRIPTORS}
    gen = {"temperature": 0.0, "top_p": 1.0, "top_k": 0, "repetition_penalty": 1.0,
           "seed": 20260722}
    plan = create_plan(
        battery_version="stronger-base-extension-v1", battery_profile="fast+packet",
        execution_mode="parallel_multi_host", scheduling_policy="round_robin",
        items=items, model_descriptors=DESCRIPTORS, generation_settings=gen, seeds=seeds,
        max_new_tokens=1024, retry_policy_id="default", output_directory=output_directory,
        created_at=created_at, plan_id="lwdb-stronger-base-v1")
    assert verify_plan_hash(plan)
    n_jobs = sum(len(plan["items"][i]["model_roles"]) for i in plan["item_ids"])
    return plan, n_jobs


if __name__ == "__main__":
    plan, n_jobs = build()
    out = os.path.join("benchmarks", "runs", "lwdb-stronger-base-v1")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "generation-plan.json"), "w", encoding="utf-8") as fh:
        json.dump(plan, fh, ensure_ascii=False, indent=1)
    print(f"froze plan {plan['plan_id']} hash={plan['plan_hash'][:16]} items={len(plan['item_ids'])} jobs={n_jobs}")
