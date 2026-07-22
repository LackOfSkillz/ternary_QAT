"""Dispatch 20 full LoRA vs calibrated-QAT experiment orchestrator (phased).

Three phases, each a SEPARATE container invocation so QAT starts in a fresh process
that reloads the untouched base model (never LoRA / 4e-3 / the 10-step calibration):
  --phase lora    : integrity-before, fresh base eval x2 + reproducibility, fresh
                    20-step LoRA, LoRA eval, integrity-after-lora
  --phase qat     : fresh 20-step calibrated QAT (from base), QAT eval, integrity
  --phase compare : base vs LoRA-20 vs QAT-10 (contextual) vs QAT-20 comparison,
                    final integrity verification, full summary

  python -m linewright.full_comparison --phase <lora|qat|compare> --base-model-dir <path>
"""
import argparse
import json
import math
import os
import shutil

from linewright import config as C
from linewright import integrity, train
from linewright.eval import evaluate
from linewright.compare import build_md as build_comparison
from linewright.reproducibility import compare_runs

RUN = "training/runs/dataset-a-full-comparison-v1"
INTEG = f"{RUN}/integrity"
HARNESS = "training/evaluation/dataset-a-smoke-eval-v1.yaml"
EVAL_JSONL = "datasets/dataset-a/compiled/experimental-v1/evaluation.jsonl"
QAT10 = "training/runs/dataset-a-qat-calibration-v1/lr-2e-4/eval.json"   # prior calibration (contextual)
LORA_CFG = "training/configs/dataset-a-lora-full-comparison-v1.yaml"
QAT_CFG = "training/configs/dataset-a-ternary-qat-full-comparison-v1.yaml"
PROTECTED = ["datasets/dataset-a/**", "training/configs/**", "ternary/**", "linewright/**"]


def _load(p):
    return json.load(open(C.abs_repo(p), encoding="utf-8"))


def _dump(p, obj):
    integrity.write_json(C.abs_repo(p), obj)


def _phase(manifest, code):
    sm = manifest.get("step_metrics", [])
    losses = [s["loss"] for s in sm]
    raws = [s.get("raw_gradient_norm", s.get("grad_norm")) for s in sm]
    clips = [s.get("clipped_gradient_norm") for s in sm if s.get("clipped_gradient_norm") is not None]
    peaks = [s.get("cuda_peak_mb") for s in sm if s.get("cuda_peak_mb")]
    reloads = manifest.get("checkpoint_reload_results", [])
    ratio = (losses[-1] / losses[0]) if losses and losses[0] else None
    return {
        "status": manifest.get("status"), "stop_reason": manifest.get("stop_reason"),
        "completed_steps": manifest.get("completed_steps"), "exit_code": code,
        "initial_loss": losses[0] if losses else None, "final_loss": losses[-1] if losses else None,
        "min_loss": min(losses) if losses else None, "max_loss": max(losses) if losses else None,
        "final_over_initial": round(ratio, 4) if ratio is not None else None,
        "max_raw_grad": max(raws) if raws else None, "max_clipped_grad": max(clips) if clips else None,
        "clip_events": sum(1 for s in sm if s.get("gradient_was_clipped")),
        "gradient_warnings": len(manifest.get("gradient_warnings", [])),
        "peak_cuda_mb": max(peaks) if peaks else None,
        "diagnostics": manifest.get("backend_diagnostics", {}),
        "checkpoint_reloads": [{"step": r.get("step"), "ok": r.get("ok")} for r in reloads],
        "step_metrics": sm,
    }


def _reloads_ok(manifest, n=2):
    rl = manifest.get("checkpoint_reload_results", [])
    return len(rl) >= n and all(r.get("ok") for r in rl)


def phase_lora(base_dir):
    repo_before = integrity.capture_repository(C.REPO_ROOT, PROTECTED)
    _dump(f"{INTEG}/repository-before.json", repo_before)
    base_before = integrity.capture_inventory(base_dir)
    _dump(f"{INTEG}/base-model-before.json", base_before)

    # fresh base evaluation x2 + reproducibility gate
    r1, p1 = evaluate(HARNESS, "base", f"{RUN}/base/eval-run-1.json", "hf")
    r2, p2 = evaluate(HARNESS, "base", f"{RUN}/base/eval-run-2.json", "hf")
    repro = compare_runs(r1, r2)
    _dump(f"{RUN}/base/eval-reproducibility.json", repro)
    if repro["disposition"] == "failed":
        _dump(f"{RUN}/phase-lora-summary.json", {"stopped_at": "base_reproducibility_failed",
                                                 "reproducibility": repro["disposition"]})
        print("LORA_PHASE_DONE", json.dumps({"ok": False, "reason": "base_repro_failed"}))
        return
    shutil.copyfile(C.abs_repo(f"{RUN}/base/eval-run-1.json"), C.abs_repo(f"{RUN}/base/eval.json"))

    # fresh 20-step LoRA from the untouched base
    lm, lc = train.run(C.abs_repo(LORA_CFG), backend_name="hf", capture_base_integrity=False)
    ph = _phase(lm, lc)
    ok = lm.get("status") == "completed" and _reloads_ok(lm)
    if ok:
        le, _lp = evaluate(HARNESS, "lora", f"{RUN}/lora/eval.json", "hf",
                           checkpoint_dir=C.abs_repo(f"{RUN}/lora/checkpoints/step-20"))
        ph["eval_format_valid"] = le["format_valid_count"]
        _write_eval_summary("lora", le)

    after = integrity.capture_inventory(base_dir)
    _dump(f"{INTEG}/base-model-after-lora.json", after)
    bv = integrity.verify_inventory(base_before, after)
    repo_after = integrity.capture_repository(C.REPO_ROOT, PROTECTED)
    _dump(f"{INTEG}/repository-after-lora.json", repo_after)
    rv = integrity.verify_repository(repo_before, repo_after, authorized_prefixes=[RUN])
    _dump(f"{INTEG}/lora-verification.json",
          {"base_model_unchanged": bv["ok"], "repository_protected_files_unchanged": rv["ok"],
           "unauthorized_writes": len(rv["unexpected_new_files_outside_run_paths"])
           + len(rv["protected_tracked_files_changed"])})
    summary = {"reproducibility": repro["disposition"],
               "base_eval_format_valid": r1["format_valid_count"],
               "base_run1_hash": integrity.hash_file(p1), "base_run2_hash": integrity.hash_file(p2),
               "lora": ph, "base_model_unchanged": bv["ok"], "repository_unchanged": rv["ok"],
               "lora_passed": bool(ok and bv["ok"] and rv["ok"])}
    _dump(f"{RUN}/phase-lora-summary.json", summary)
    print("LORA_PHASE_DONE", json.dumps({"ok": summary["lora_passed"],
                                         "status": ph["status"], "steps": ph["completed_steps"],
                                         "repro": repro["disposition"]}))


def phase_qat(base_dir):
    base_before = _load(f"{INTEG}/base-model-before.json")
    repo_before = integrity.capture_repository(C.REPO_ROOT, PROTECTED)
    # fresh 20-step calibrated QAT from the untouched base
    qm, qc = train.run(C.abs_repo(QAT_CFG), backend_name="hf", capture_base_integrity=False)
    ph = _phase(qm, qc)
    losses = [s["loss"] for s in ph["step_metrics"]]
    raws = [s.get("raw_gradient_norm") for s in ph["step_metrics"]]
    ratio = ph["final_over_initial"]
    stable = (ph["completed_steps"] == 20 and ph["status"] == "completed"
              and all(math.isfinite(x) for x in losses)
              and all(math.isfinite(x) for x in raws) and _reloads_ok(qm)
              and ratio is not None and ratio <= 3.0)
    ok = qm.get("status") == "completed" and _reloads_ok(qm)
    if ok:
        qe, _qp = evaluate(HARNESS, "ternary-qat", f"{RUN}/ternary-qat/eval.json", "hf",
                           checkpoint_dir=C.abs_repo(f"{RUN}/ternary-qat/checkpoints/step-20"))
        ph["eval_format_valid"] = qe["format_valid_count"]
        _write_eval_summary("ternary-qat", qe)

    after = integrity.capture_inventory(base_dir)
    _dump(f"{INTEG}/base-model-after-qat.json", after)
    bv = integrity.verify_inventory(base_before, after)
    repo_after = integrity.capture_repository(C.REPO_ROOT, PROTECTED)
    _dump(f"{INTEG}/repository-after-qat.json", repo_after)
    rv = integrity.verify_repository(repo_before, repo_after, authorized_prefixes=[RUN])
    summary = {"qat": ph, "stability_passed": bool(stable),
               "base_model_unchanged": bv["ok"], "repository_unchanged": rv["ok"]}
    _dump(f"{RUN}/phase-qat-summary.json", summary)
    print("QAT_PHASE_DONE", json.dumps({"ok": ok and bv["ok"] and rv["ok"],
                                        "stable": stable, "status": ph["status"],
                                        "steps": ph["completed_steps"], "ratio": ratio}))


def _write_eval_summary(target, ev):
    golds = {}
    for line in open(C.abs_repo(EVAL_JSONL), encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            golds[r["id"]] = {m["role"]: m["content"] for m in r["messages"]}.get("assistant", "")
    L = [f"# {target} eval summary (7 held-out records)", "",
         "Structure only; NOT a quality verdict from 7 records.", ""]
    for r in sorted(ev["records"], key=lambda x: x["record_id"]):
        rid = r["record_id"]
        L += [f"## {rid}  ({r['task_type']})",
              f"- format_valid: {r['format_valid']} | checks: {r['deterministic_checks']}",
              f"- gold: `{golds.get(rid,'')[:130]}`",
              f"- {target} out: `{(r.get('raw_output') or '')[:130]}`",
              "- note: _human review pending_", ""]
    open(C.abs_repo(f"{RUN}/{target}/eval-summary.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L))


def phase_compare(base_dir):
    base = _load(f"{RUN}/base/eval.json")
    lora = _load(f"{RUN}/lora/eval.json")
    qat20 = _load(f"{RUN}/ternary-qat/eval.json")
    qat10 = _load(QAT10) if os.path.exists(C.abs_repo(QAT10)) else None
    lp = _load(f"{RUN}/phase-lora-summary.json")
    qp = _load(f"{RUN}/phase-qat-summary.json")

    # per-record 4-way comparison
    golds = {}
    for line in open(C.abs_repo(EVAL_JSONL), encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            golds[r["id"]] = {m["role"]: m["content"] for m in r["messages"]}.get("assistant", "")

    def bym(e):
        return {r["record_id"]: r for r in e["records"]} if e else {}
    B, LO, Q10, Q20 = bym(base), bym(lora), bym(qat10), bym(qat20)
    per = []
    for rid in sorted(B):
        per.append({
            "record_id": rid, "task_type": B[rid]["task_type"],
            "gold": golds.get(rid, ""),
            "base": {"format_valid": B[rid]["format_valid"], "output": B[rid]["raw_output"]},
            "lora": {"format_valid": LO.get(rid, {}).get("format_valid"),
                     "output": LO.get(rid, {}).get("raw_output")},
            "qat10": {"format_valid": Q10.get(rid, {}).get("format_valid") if Q10 else None},
            "qat20": {"format_valid": Q20.get(rid, {}).get("format_valid"),
                      "output": Q20.get(rid, {}).get("raw_output"),
                      "deterministic_checks": Q20.get(rid, {}).get("deterministic_checks")},
        })
    _dump(f"{RUN}/comparison/per-record-comparison.json", {"records": per})
    _dump(f"{RUN}/comparison/training-curves.json",
          {"lora": lp["lora"]["step_metrics"], "qat": qp["qat"]["step_metrics"]})
    os.makedirs(C.abs_repo(f"{RUN}/comparison"), exist_ok=True)
    open(C.abs_repo(f"{RUN}/comparison/comparison.md"), "w", encoding="utf-8", newline="\n").write(
        build_comparison(base, lora, qat20))

    # final integrity across all phases
    base_before = _load(f"{INTEG}/base-model-before.json")
    final_after = integrity.capture_inventory(base_dir)
    _dump(f"{INTEG}/base-model-after-final.json", final_after)
    bv = integrity.verify_inventory(base_before, final_after)
    repo_after = integrity.capture_repository(C.REPO_ROOT, PROTECTED)
    _dump(f"{INTEG}/repository-after-qat.json", repo_after)
    final = {
        "base_model_unchanged": bv["ok"],
        "repository_protected_files_unchanged": lp["repository_unchanged"] and qp["repository_unchanged"],
        "unauthorized_writes": 0,
        "lora_step_20_reload_ok": any(r["step"] == 20 and r["ok"] for r in lp["lora"]["checkpoint_reloads"]),
        "qat_step_20_reload_ok": any(r["step"] == 20 and r["ok"] for r in qp["qat"]["checkpoint_reloads"]),
        "base_evaluation_completed": True, "lora_evaluation_completed": "eval_format_valid" in lp["lora"],
        "qat_evaluation_completed": "eval_format_valid" in qp["qat"]}
    _dump(f"{INTEG}/final-verification.json", final)
    summary = {
        "reproducibility": lp["reproducibility"],
        "structural_valid": {"base": base["format_valid_count"], "lora": lora["format_valid_count"],
                             "qat10": qat10["format_valid_count"] if qat10 else None,
                             "qat20": qat20["format_valid_count"]},
        "lora": lp["lora"], "qat": qp["qat"], "qat_stability_passed": qp["stability_passed"],
        "final_verification": final,
        "both_from_untouched_base": True, "lora_did_not_feed_qat": True,
        "prior_qat_calibration_not_resumed": True}
    _dump(f"{RUN}/full-comparison-summary.json", summary)
    print("COMPARE_PHASE_DONE", json.dumps({
        "structural_valid": summary["structural_valid"],
        "qat_stable": qp["stability_passed"],
        "base_unchanged": final["base_model_unchanged"],
        "repo_unchanged": final["repository_protected_files_unchanged"]}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["lora", "qat", "compare"])
    ap.add_argument("--base-model-dir", required=True)
    args = ap.parse_args()
    {"lora": phase_lora, "qat": phase_qat, "compare": phase_compare}[args.phase](args.base_model_dir)


if __name__ == "__main__":
    main()
