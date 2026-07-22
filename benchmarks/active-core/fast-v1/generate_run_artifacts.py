"""Generate the frozen run artifacts for the first fast-battery execution (Dispatch 24).

Writes the frozen generation plan, endpoint descriptors, the run manifest (candidate
selection basis), and the preflight/health-check record into a run directory. This does NOT
generate model outputs — it freezes the plan and records readiness so the operator (or a
follow-up) can execute the dual-GX10 generation against the exact same plan_hash.
"""
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.battery.plan_builder import build_plan, endpoint_descriptor

RUN_ID = "lwdb-fast-v1-20260722"
RUN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "runs", RUN_ID)

# --- real preflight health-check (recorded 2026-07-22) ---
PREFLIGHT = {
    "run_id": RUN_ID, "checked_at": "2026-07-22",
    "base_gx10": {"host": "gx10-9141", "tailscale_ip": "100.92.130.112", "gpu": "NVIDIA GB10",
                  "reachable": True, "base_model_present": "7.6G",
                  "docker_image": "linewright-ternary-train:run001", "provisioned": True},
    "candidate_gx10": {"host": "gx10-5611", "tailscale_ip": "100.97.81.71", "gpu": "NVIDIA GB10",
                       "reachable": True, "ram_gb": 121, "python": "3.12.3", "torch": "2.11.0+cu130",
                       "base_model_present": False, "adapter_present": False,
                       "transformers_peft_present": "pending", "code_present": False,
                       "provisioned": False,
                       "provisioning_needed": ["base model (transfer over 192.168.10.x)",
                                               "LoRA-20 adapter", "transformers + peft",
                                               "linewright/ternary code"]},
    "inter_node_link": {"subnet": "192.168.10.0/24", "mtu": 9000, "base": "192.168.10.1",
                        "candidate": "192.168.10.2"},
    "model_serving_endpoints_running": False,
    "endpoint_type_planned": "local_huggingface (in-process HF generation per node)",
}

# --- candidate selection (dispatch Tuned Candidate Selection) ---
RUN_MANIFEST = {
    "run_id": RUN_ID, "battery_version": "fast-v1", "dispatch": 24,
    "execution_mode": "parallel_multi_host", "production_approved": False,
    "candidate": {
        "model_name": "Ternary-Bonsai-4B-unpacked + LoRA adapter",
        "checkpoint_path": "training/runs/dataset-a-full-comparison-v1/lora/checkpoints/step-20",
        "checkpoint_fraction": 1.0, "training_method": "LoRA (rank 16) on ternary base",
        "training_run_id": "dataset-a-full-comparison-v1", "model_revision": "lora-step-20",
        "tokenizer_revision": "4485fae7a00129467b9329b738110d88b2942a1a",
        "quantization": "ternary base (unpacked) + fp LoRA adapter", "merge_status": "unmerged (adapter applied at load)",
        "endpoint_id": "ep-candidate",
        "selection_basis": "Dispatch-24 selection rule: most recent technically-valid, "
        "non-catastrophic checkpoint with complete provenance. QAT-20 excluded (Dispatch-20/23 "
        "evidence: catastrophically degenerate, 0/7 mechanical). LoRA-20 is the best available "
        "non-excluded candidate (4/7 mechanical; partially degenerate but not catastrophic) and "
        "runs the fast path (base+adapter, no fake-quant). Experimental smoke checkpoint; not a "
        "quality claim."},
    "target_base": {"model_name": "prism-ml/Ternary-Bonsai-4B-unpacked",
                    "model_revision": "4485fae7a00129467b9329b738110d88b2942a1a",
                    "endpoint_id": "ep-base"},
}

GEN_SETTINGS = {"temperature": 0.0, "top_p": 1.0, "top_k": 0, "repetition_penalty": 1.0,
                "seed": 20260722}


def main():
    os.makedirs(RUN_DIR, exist_ok=True)
    base_ep = endpoint_descriptor("ep-base", "local_huggingface",
                                  "prism-ml/Ternary-Bonsai-4B-unpacked", "gx10-9141",
                                  model_roles=["target_base"])
    cand_ep = endpoint_descriptor("ep-candidate", "local_huggingface",
                                  "Ternary-Bonsai-4B-unpacked+lora-step-20", "gx10-5611",
                                  model_roles=["new_candidate"])
    plan = build_plan(
        base_descriptor={"identity": RUN_MANIFEST["target_base"]["model_name"],
                         "revision": RUN_MANIFEST["target_base"]["model_revision"],
                         "tokenizer_revision": RUN_MANIFEST["candidate"]["tokenizer_revision"],
                         "endpoint_id": "ep-base", "host": "gx10-9141"},
        candidate_descriptor={"identity": RUN_MANIFEST["candidate"]["model_name"],
                              "checkpoint": RUN_MANIFEST["candidate"]["checkpoint_path"],
                              "revision": RUN_MANIFEST["candidate"]["model_revision"],
                              "tokenizer_revision": RUN_MANIFEST["candidate"]["tokenizer_revision"],
                              "endpoint_id": "ep-candidate", "host": "gx10-5611"},
        generation_settings=GEN_SETTINGS, seeds={"target_base": 20260722, "new_candidate": 20260722},
        max_new_tokens=1024, output_directory=f"benchmarks/runs/{RUN_ID}/normalized-results",
        execution_mode="parallel_multi_host", scheduling_policy="round_robin",
        plan_id=RUN_ID, created_at="2026-07-22")

    def w(name, obj):
        with open(os.path.join(RUN_DIR, name), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    w("generation-plan.json", plan)
    w("endpoint-manifest.json", {"endpoints": [base_ep, cand_ep]})
    w("run-manifest.json", RUN_MANIFEST)
    w("preflight.json", PREFLIGHT)
    print(f"run_id={RUN_ID} plan_hash={plan['plan_hash'][:16]} jobs={len(plan['item_ids'])*2} -> {RUN_DIR}")


if __name__ == "__main__":
    main()
