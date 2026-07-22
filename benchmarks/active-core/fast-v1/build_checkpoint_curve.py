"""Freeze the existing-checkpoint-curve subset + plan (Dispatch 25, D8).

Selects a fixed 9-item diagnostic subset of the frozen fast battery (frozen BEFORE any curve
generation) and builds a hashed generation plan comparing target_base, LoRA step-10, and LoRA
step-20 (the checkpoints that exist for the dataset-a-full-comparison-v1 LoRA run). No new
checkpoints are invented. Writes generation-plan.json + checkpoint-manifest.json.
"""
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.battery.plan_builder import assemble_prompt
from linewright.evaluation.execution.plan import create_plan

RUN_ID = "lwdb-checkpoint-curve-v0"
RUN_DIR = os.path.join(_REPO, "benchmarks", "runs", RUN_ID)
FASTV1 = os.path.join(_REPO, "benchmarks", "active-core", "fast-v1")

# frozen subset (short scene, long scene, surface bare, surface compiled, restraint clean,
# focused revision, canon application, structured protocol, stability-long)
SUBSET = ["lwdb-a-length-short", "lwdb-a-length-long", "lwdb-f-surface-bare",
          "lwdb-f-surface-compiled", "lwdb-c-restraint-clean", "lwdb-c-restraint-fix",
          "lwdb-d-canon-apply", "lwdb-e-scene-contract", "lwdb-i-stability-long"]

ROLES = {
    "target_base": {"identity": "prism-ml/Ternary-Bonsai-4B-unpacked",
                    "revision": "4485fae7a00129467b9329b738110d88b2942a1a",
                    "tokenizer_revision": "4485fae7a00129467b9329b738110d88b2942a1a",
                    "adapter": None, "endpoint_id": "ep-base", "host": "gx10-9141"},
    "lora_10": {"identity": "base + LoRA step-10",
                "checkpoint": "training/runs/dataset-a-full-comparison-v1/lora/checkpoints/step-10",
                "revision": "lora-step-10", "endpoint_id": "ep-lora10", "host": "gx10-9141"},
    "lora_20": {"identity": "base + LoRA step-20",
                "checkpoint": "training/runs/dataset-a-full-comparison-v1/lora/checkpoints/step-20",
                "revision": "lora-step-20", "endpoint_id": "ep-lora20", "host": "gx10-9141"},
}


def _load(name, key):
    return {r[key]: r for r in (json.loads(l) for l in
            open(os.path.join(FASTV1, name), encoding="utf-8") if l.strip())}


def main():
    os.makedirs(RUN_DIR, exist_ok=True)
    items = _load("items.jsonl", "item_id")
    contracts = _load("contracts.jsonl", "contract_id")
    plan_items = []
    for iid in SUBSET:
        it = items[iid]
        c = contracts[it["behavior_contract_id"]]
        plan_items.append({
            "item_id": iid,
            "prompt": json.dumps(assemble_prompt(it, c), sort_keys=True, ensure_ascii=False),
            "behavior_contract": {"contract_id": c["contract_id"],
                                  "output_schema_id": c["output_schema_id"],
                                  "expected_output_type": c["expected_output_type"],
                                  "forbidden_failures": c["forbidden_failures"],
                                  "validation_expectations": c["validation_expectations"],
                                  "no_change_case": c["no_change_case"],
                                  "refusal_expectation": c["refusal_expectation"]},
            "model_roles": list(ROLES),
        })
    plan = create_plan(
        battery_version="fast-v1-subset9", battery_profile="calibration",
        execution_mode="sequential_single_host", scheduling_policy="model_sequential",
        items=plan_items, model_descriptors={r: {k: v for k, v in d.items() if k != "host"}
                                             for r, d in ROLES.items()},
        generation_settings={"temperature": 0.0, "top_p": 1.0, "seed": 20260722},
        seeds={r: 20260722 for r in ROLES}, max_new_tokens=1024,
        retry_policy_id="default", output_directory=f"benchmarks/runs/{RUN_ID}/normalized-results",
        created_at="2026-07-22", plan_id=RUN_ID)

    def w(name, obj):
        with open(os.path.join(RUN_DIR, name), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=2); fh.write("\n")
    w("generation-plan.json", plan)
    w("checkpoint-manifest.json", {
        "run_id": RUN_ID, "dispatch": 25, "subset_frozen_before_generation": True,
        "subset_item_ids": SUBSET, "checkpoints": ROLES,
        "note": "existing LoRA checkpoints only (step-10, step-20) + untouched base; no invented checkpoints."})
    print(f"curve subset frozen: {len(SUBSET)} items x {len(ROLES)} checkpoints = "
          f"{len(SUBSET)*len(ROLES)} jobs; plan_hash={plan['plan_hash'][:12]}")


if __name__ == "__main__":
    main()
