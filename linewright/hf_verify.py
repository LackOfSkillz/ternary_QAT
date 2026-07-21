"""GX10 real-model verification orchestrator (Dispatch 18A.1, Parts 5/7/9/11/12/13).

Runs, in order, with base-model + repository integrity captured around each phase:
  base eval run 1 -> base eval run 2 -> reproducibility gate ->
  (only if accepted) LoRA one-step -> (only if LoRA passes) ternary-QAT one-step.

Every real result is derived from the actual model; nothing is synthesized. On any
failure it stops immediately, preserves evidence, and does NOT proceed to the next
gradient phase. Writes all evidence under training/runs/dataset-a-smoke-v1/.

Run inside the GX10 container:
  python -m linewright.hf_verify --base-model-dir /workspace/hf-cache/prism-ml/Ternary-Bonsai-4B-unpacked
"""
import argparse
import json
import os
import platform
import time

from linewright import config as C
from linewright import integrity
from linewright import train
from linewright.eval import evaluate
from linewright.reproducibility import compare_runs

RUN = "training/runs/dataset-a-smoke-v1"
INTEG = f"{RUN}/integrity-hf"
BASE = f"{RUN}/base"
HARNESS = "training/evaluation/dataset-a-smoke-eval-v1.yaml"
LORA_CFG = "training/configs/dataset-a-hf-lora-onestep.yaml"
QAT_CFG = "training/configs/dataset-a-hf-qat-onestep.yaml"
PROTECTED = ["datasets/dataset-a/compiled/experimental-v1/**",
             "datasets/dataset-a/prompts/**", "training/configs/**",
             "ternary/**", "linewright/**"]


def gpu_info():
    info = {"hostname": platform.node()}
    try:
        import torch
        info["torch"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info["device"] = torch.cuda.get_device_name(0)
            p = torch.cuda.get_device_properties(0)
            info["compute_capability"] = f"{p.major}.{p.minor}"
            info["total_mem_mb"] = round(p.total_memory / 2**20, 1)
            info["bf16"] = torch.cuda.is_bf16_supported()
            info["torch_cuda"] = torch.version.cuda
    except Exception as e:
        info["error"] = str(e)
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model-dir", required=True)
    args = ap.parse_args()
    base_dir = args.base_model_dir
    summary = {"gpu": gpu_info(), "phases": {}, "stopped_at": None}
    integrity.write_json(C.abs_repo(f"{INTEG}/gpu-info.json"), summary["gpu"])

    repo_before = integrity.capture_repository(C.REPO_ROOT, PROTECTED)
    base_before = integrity.capture_inventory(base_dir)
    integrity.write_json(C.abs_repo(f"{INTEG}/base-model-before.json"), base_before)
    summary["base_model_file_count"] = base_before["file_count"]
    summary["base_model_root_hash"] = base_before["root_hash"]

    def verify_base(tag):
        after = integrity.capture_inventory(base_dir)
        integrity.write_json(C.abs_repo(f"{INTEG}/base-model-after-{tag}.json"), after)
        v = integrity.verify_inventory(base_before, after)
        summary["phases"].setdefault("base_integrity", {})[tag] = v["ok"]
        return v

    try:
        # ---- base evaluation twice ----
        r1, p1 = evaluate(HARNESS, "base", f"{BASE}/hf-eval-run-1.json", backend_name="hf")
        r2, p2 = evaluate(HARNESS, "base", f"{BASE}/hf-eval-run-2.json", backend_name="hf")
        summary["phases"]["base_eval"] = {
            "run1": os.path.relpath(p1, C.REPO_ROOT), "run2": os.path.relpath(p2, C.REPO_ROOT),
            "record_count": r1["record_count"],
            "run1_hash": integrity.hash_file(p1), "run2_hash": integrity.hash_file(p2),
            "environment": r1.get("environment", {})}
        verify_base("eval")
        repro = compare_runs(r1, r2)
        integrity.write_json(C.abs_repo(f"{BASE}/hf-eval-reproducibility.json"), repro)
        summary["phases"]["reproducibility"] = {
            "disposition": repro["disposition"], "accepted": repro["accepted"],
            "exact": repro["exact_match"], "normalized": repro["normalized_match"],
            "materially_equivalent": repro["materially_equivalent"], "failed": repro["failed"]}
        if not repro["accepted"]:
            summary["stopped_at"] = "reproducibility_not_accepted"
            _finish(summary, repo_before)
            return

        # ---- LoRA one-step ----
        lora_manifest, lora_code = train.run(C.abs_repo(LORA_CFG), backend_name="hf",
                                             max_steps_override=1)
        summary["phases"]["lora"] = _phase_summary(lora_manifest, lora_code)
        verify_base("lora")
        if lora_manifest.get("status") != "completed":
            summary["stopped_at"] = "lora_one_step_failed"
            _finish(summary, repo_before)
            return

        # ---- ternary-QAT one-step (only after LoRA passes) ----
        qat_manifest, qat_code = train.run(C.abs_repo(QAT_CFG), backend_name="hf",
                                           max_steps_override=1)
        summary["phases"]["qat"] = _phase_summary(qat_manifest, qat_code)
        verify_base("qat")
        if qat_manifest.get("status") != "completed":
            summary["stopped_at"] = "qat_one_step_failed"

    except Exception as e:
        import traceback
        summary["exception"] = f"{type(e).__name__}: {e}"
        summary["traceback"] = traceback.format_exc()[-2000:]
        summary["stopped_at"] = summary["stopped_at"] or "exception"

    _finish(summary, repo_before)


def _phase_summary(manifest, code):
    d = manifest.get("backend_diagnostics", {})
    reloads = manifest.get("checkpoint_reload_results", [])
    return {
        "status": manifest.get("status"), "stop_reason": manifest.get("stop_reason"),
        "completed_steps": manifest.get("completed_steps"), "exit_code": code,
        "diagnostics": d,
        "checkpoint_reload": reloads[0] if reloads else None,
        "repository_verification_ok": (manifest.get("repository_verification") or {}).get("ok"),
    }


def _finish(summary, repo_before):
    repo_after = integrity.capture_repository(C.REPO_ROOT, PROTECTED)
    rv = integrity.verify_repository(repo_before, repo_after,
                                     authorized_prefixes=[RUN])
    integrity.write_json(C.abs_repo(f"{INTEG}/repository-verification.json"), rv)
    # final base-model verification across all captured afters
    base_before = json.load(open(C.abs_repo(f"{INTEG}/base-model-before.json"), encoding="utf-8"))
    all_ok = True
    for tag in ("eval", "lora", "qat"):
        p = C.abs_repo(f"{INTEG}/base-model-after-{tag}.json")
        if os.path.exists(p):
            v = integrity.verify_inventory(base_before, json.load(open(p, encoding="utf-8")))
            all_ok = all_ok and v["ok"]
    summary["repository_integrity_ok"] = rv["ok"]
    summary["base_model_integrity_ok"] = all_ok
    integrity.write_json(C.abs_repo(f"{INTEG}/base-model-verification.json"),
                         {"all_afters_ok": all_ok})
    integrity.write_json(C.abs_repo(f"{RUN}/hf-verify-summary.json"), summary)
    print("HF_VERIFY_DONE", json.dumps({"stopped_at": summary["stopped_at"],
                                        "repro": summary["phases"].get("reproducibility"),
                                        "lora": (summary["phases"].get("lora") or {}).get("status"),
                                        "qat": (summary["phases"].get("qat") or {}).get("status"),
                                        "base_integrity": summary.get("base_model_integrity_ok"),
                                        "repo_integrity": summary.get("repository_integrity_ok")}))


if __name__ == "__main__":
    main()
