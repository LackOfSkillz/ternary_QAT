"""Ternary-QAT stability calibration orchestrator (Dispatch 19).

Runs QAT calibration candidates IN ORDER and stops at the FIRST that passes the
stability gate. Default order: lr 2e-4, then lr 5e-5 (only if 2e-4 fails). The
5e-4 probe is never run automatically (Part 10). The stable checkpoint is evaluated
and compared against the existing base + 20-step LoRA results. base-model and
repository integrity are captured around the whole calibration.

  python -m linewright.qat_calibrate --base-model-dir /workspace/hf-cache/prism-ml/Ternary-Bonsai-4B-unpacked
"""
import argparse
import json
import math
import os

from linewright import config as C
from linewright import integrity, train
from linewright.eval import evaluate
from linewright.compare import build_md as build_comparison

RUN = "training/runs/dataset-a-qat-calibration-v1"
INTEG = f"{RUN}/integrity"
HARNESS = "training/evaluation/dataset-a-smoke-eval-v1.yaml"
EVAL_JSONL = "datasets/dataset-a/compiled/experimental-v1/evaluation.jsonl"
SMOKE = "training/runs/dataset-a-smoke-v1"          # prior base + LoRA evals
PROTECTED = ["datasets/dataset-a/compiled/experimental-v1/**",
             "datasets/dataset-a/prompts/**", "datasets/dataset-a/manifests/**",
             "training/configs/**", "ternary/**", "linewright/**"]
CANDIDATES = [
    ("2e-4", "training/configs/dataset-a-ternary-qat-calibration-2e-4-v1.yaml"),
    ("5e-5", "training/configs/dataset-a-ternary-qat-calibration-5e-5-v1.yaml"),
]


def _load(p):
    return json.load(open(C.abs_repo(p), encoding="utf-8"))


def stability_gate(manifest, base_ok, repo_ok):
    sm = manifest.get("step_metrics", [])
    losses = [s["loss"] for s in sm]
    raws = [s.get("raw_gradient_norm", s.get("grad_norm")) for s in sm]
    completed = manifest.get("completed_steps") == 10 and manifest.get("status") == "completed"
    finite_loss = all(math.isfinite(x) for x in losses) and bool(losses)
    finite_grad = all(math.isfinite(x) for x in raws) and bool(raws)
    reloads = manifest.get("checkpoint_reload_results", [])
    reload_ok = len(reloads) >= 2 and all(r.get("ok") for r in reloads)
    ratio = (losses[-1] / losses[0]) if losses and losses[0] else None
    ratio_ok = ratio is not None and ratio <= 3.0
    passed = all([completed, finite_loss, finite_grad, reload_ok, base_ok, repo_ok, ratio_ok])
    return {
        "passed": passed, "completed_10": completed, "all_losses_finite": finite_loss,
        "all_gradients_finite": finite_grad, "checkpoints_reload": reload_ok,
        "base_model_unchanged": base_ok, "repository_integrity_ok": repo_ok,
        "final_over_initial": round(ratio, 4) if ratio is not None else None,
        "ratio_ok": ratio_ok,
        "initial_loss": losses[0] if losses else None,
        "final_loss": losses[-1] if losses else None,
        "min_loss": min(losses) if losses else None, "max_loss": max(losses) if losses else None,
        "max_raw_grad": max(raws) if raws else None,
        "max_clipped_grad": max((s.get("clipped_gradient_norm") for s in sm
                                 if s.get("clipped_gradient_norm") is not None), default=None),
        "clip_events": sum(1 for s in sm if s.get("gradient_was_clipped")),
        "gradient_warnings": len(manifest.get("gradient_warnings", [])),
        "completed_steps": manifest.get("completed_steps"),
        "stop_reason": manifest.get("stop_reason"),
    }


def _eval_summary_md(base_j, lora_j, qat_j):
    golds = {}
    for line in open(C.abs_repo(EVAL_JSONL), encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            golds[r["id"]] = {m["role"]: m["content"] for m in r["messages"]}.get("assistant", "")
    b = {r["record_id"]: r for r in base_j["records"]}
    lo = {r["record_id"]: r for r in lora_j["records"]}
    q = {r["record_id"]: r for r in qat_j["records"]}
    L = ["# Calibrated QAT eval summary (base vs 20-step LoRA vs stable 10-step QAT)", "",
         "Seven held-out records — plumbing/structure only; NOT a quality verdict.", ""]
    for rid in sorted(q):
        L += [f"## {rid}  ({q[rid]['task_type']})",
              f"- format_valid: base {b.get(rid,{}).get('format_valid')} | "
              f"lora {lo.get(rid,{}).get('format_valid')} | qat {q[rid]['format_valid']}",
              f"- qat checks: {q[rid]['deterministic_checks']}",
              f"- gold: `{golds.get(rid,'')[:140]}`",
              f"- qat out: `{(q[rid].get('raw_output') or '')[:140]}`",
              "- note: _human review pending (improved / degraded / unchanged / indeterminate)_", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model-dir", required=True)
    args = ap.parse_args()
    base_dir = args.base_model_dir
    summary = {"candidate_order": [c[0] for c in CANDIDATES], "candidates": {},
               "first_stable_learning_rate": None, "stopped_at": None,
               "historical_failed": {"learning_rate": "4.0e-3", "result": "diverged",
                                     "abort_step": 14, "max_raw_grad": 149.0,
                                     "final_loss": 45.695248}}

    repo_before = integrity.capture_repository(C.REPO_ROOT, PROTECTED)
    integrity.write_json(C.abs_repo(f"{INTEG}/repository-before.json"), repo_before)
    base_before = integrity.capture_inventory(base_dir)
    integrity.write_json(C.abs_repo(f"{INTEG}/base-model-before.json"), base_before)

    try:
        for tag, cfg_path in CANDIDATES:
            manifest, code = train.run(C.abs_repo(cfg_path), backend_name="hf",
                                       capture_base_integrity=False)
            after = integrity.capture_inventory(base_dir)
            bv = integrity.verify_inventory(base_before, after)
            repo_after = integrity.capture_repository(C.REPO_ROOT, PROTECTED)
            rv = integrity.verify_repository(repo_before, repo_after, authorized_prefixes=[RUN])
            gate = stability_gate(manifest, bv["ok"], rv["ok"])
            summary["candidates"][tag] = {
                "learning_rate": manifest.get("effective_config", {}),
                "gate": gate,
                "step_metrics": manifest.get("step_metrics", []),
                "diagnostics": manifest.get("backend_diagnostics", {}),
                "checkpoint_reloads": [{"step": r.get("step"), "ok": r.get("ok")}
                                       for r in manifest.get("checkpoint_reload_results", [])],
            }
            if gate["passed"]:
                summary["first_stable_learning_rate"] = tag
                # evaluate the stable step-10 checkpoint
                ck = C.abs_repo(f"{RUN}/lr-{tag}/checkpoints/step-10")
                qe, qp = evaluate(HARNESS, "ternary-qat", f"{RUN}/lr-{tag}/eval.json", "hf",
                                  checkpoint_dir=ck)
                summary["candidates"][tag]["eval"] = {
                    "path": os.path.relpath(qp, C.REPO_ROOT),
                    "records": qe["record_count"], "format_valid": qe["format_valid_count"]}
                base_j, lora_j = _load(f"{SMOKE}/base/eval.json"), _load(f"{SMOKE}/lora/eval.json")
                open(C.abs_repo(f"{RUN}/lr-{tag}/eval-summary.md"), "w",
                     encoding="utf-8", newline="\n").write(_eval_summary_md(base_j, lora_j, qe))
                os.makedirs(C.abs_repo(f"{RUN}/comparison"), exist_ok=True)
                open(C.abs_repo(f"{RUN}/comparison/comparison.md"), "w",
                     encoding="utf-8", newline="\n").write(build_comparison(base_j, lora_j, qe))
                break                          # stop at first stable candidate
        else:
            summary["stopped_at"] = "no_stable_candidate"
    except Exception as e:
        import traceback
        summary["exception"] = f"{type(e).__name__}: {e}"
        summary["traceback"] = traceback.format_exc()[-2500:]
        summary["stopped_at"] = summary["stopped_at"] or "exception"

    # final integrity
    after = integrity.capture_inventory(base_dir)
    integrity.write_json(C.abs_repo(f"{INTEG}/base-model-after.json"), after)
    bv = integrity.verify_inventory(base_before, after)
    repo_after = integrity.capture_repository(C.REPO_ROOT, PROTECTED)
    integrity.write_json(C.abs_repo(f"{INTEG}/repository-after.json"), repo_after)
    rv = integrity.verify_repository(repo_before, repo_after, authorized_prefixes=[RUN])
    integrity.write_json(C.abs_repo(f"{INTEG}/final-verification.json"),
                         {"base_model_unchanged": bv["ok"],
                          "repository_protected_files_unchanged": rv["ok"],
                          "unauthorized_writes": len(rv["unexpected_new_files_outside_run_paths"])
                          + len(rv["protected_tracked_files_changed"])})
    summary["base_model_unchanged"] = bv["ok"]
    summary["repository_unchanged"] = rv["ok"]
    summary["ready_for_longer_qat_smoke"] = bool(summary["first_stable_learning_rate"])
    integrity.write_json(C.abs_repo(f"{RUN}/qat-calibration-summary.json"), summary)
    print("QAT_CALIBRATE_DONE", json.dumps({
        "first_stable": summary["first_stable_learning_rate"],
        "stopped_at": summary["stopped_at"],
        "base_unchanged": summary["base_model_unchanged"],
        "repo_unchanged": summary["repository_unchanged"],
        "candidates": {k: v["gate"]["passed"] for k, v in summary["candidates"].items()}}))


if __name__ == "__main__":
    main()
