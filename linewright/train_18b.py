"""Dispatch 18B orchestrator: first REAL Dataset A gradient training on the GX10.

Flow (QAT runs only if LoRA passes every gate):
  integrity-before -> LoRA 20-step -> LoRA integrity/eval -> QAT 20-step ->
  QAT integrity/eval -> base/LoRA/QAT comparison.

Uses the real 28-record Dataset A train split for gradients (authorized here); the
7 held-out evaluation records never enter gradients. Every result is real. On any
failure it stops immediately, preserves evidence, and does not proceed.

  python -m linewright.train_18b --base-model-dir /workspace/hf-cache/prism-ml/Ternary-Bonsai-4B-unpacked
"""
import argparse
import json
import os
import shutil

from linewright import config as C
from linewright import integrity, train
from linewright.eval import evaluate
from linewright.compare import build_md as build_comparison

RUN = "training/runs/dataset-a-smoke-v1"
INTEG = f"{RUN}/integrity-18b"
HARNESS = "training/evaluation/dataset-a-smoke-eval-v1.yaml"
LORA_CFG = "training/configs/dataset-a-lora-smoke-v1.yaml"
QAT_CFG = "training/configs/dataset-a-ternary-qat-smoke-v1.yaml"
PROTECTED = ["datasets/dataset-a/compiled/experimental-v1/**",
             "datasets/dataset-a/prompts/**", "datasets/dataset-a/manifests/**",
             "training/configs/**", "ternary/**", "linewright/**"]


def _load(p):
    return json.load(open(C.abs_repo(p), encoding="utf-8"))


def _phase(manifest, code):
    d = manifest.get("backend_diagnostics", {})
    sm = manifest.get("step_metrics", [])
    losses = [s["loss"] for s in sm]
    grads = [s["grad_norm"] for s in sm]
    peaks = [s.get("cuda_peak_mb") for s in sm if s.get("cuda_peak_mb")]
    reloads = manifest.get("checkpoint_reload_results", [])
    return {
        "status": manifest.get("status"), "stop_reason": manifest.get("stop_reason"),
        "completed_steps": manifest.get("completed_steps"), "exit_code": code,
        "initial_loss": losses[0] if losses else None,
        "final_loss": losses[-1] if losses else None,
        "min_loss": min(losses) if losses else None,
        "max_grad_norm": max(grads) if grads else None,
        "gradient_warnings": len(manifest.get("gradient_warnings", [])),
        "peak_cuda_mb": max(peaks) if peaks else None,
        "diagnostics": d, "step_metrics": sm,
        "checkpoint_reloads": [{"step": r.get("step"), "ok": r.get("ok"),
                                "type": r.get("checkpoint_type")} for r in reloads],
        "repository_verification_ok": (manifest.get("repository_verification") or {}).get("ok"),
    }


def _eval_summary_md(target, base_json, tgt_json, eval_file):
    golds = {}
    for line in open(C.abs_repo(eval_file), encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            golds[r["id"]] = {m["role"]: m["content"] for m in r["messages"]}.get("assistant", "")
    base = {r["record_id"]: r for r in base_json["records"]}
    tgt = {r["record_id"]: r for r in tgt_json["records"]}
    L = [f"# {target} eval summary (7 held-out records)", "",
         "Smoke comparison of base vs trained vs gold. **Seven records prove nothing",
         "about general quality**; structural validity and restraint are the only",
         "mechanical signals. Outputs are truncated for readability.", ""]
    for rid in sorted(tgt):
        b, t = base.get(rid, {}), tgt[rid]
        L += [f"## {rid}  ({t['task_type']})",
              f"- base format_valid: {b.get('format_valid')} | {target} format_valid: {t['format_valid']}",
              f"- deterministic_checks ({target}): {t['deterministic_checks']}",
              f"- gold: `{golds.get(rid,'')[:160]}`",
              f"- base out: `{(b.get('raw_output') or '')[:160]}`",
              f"- {target} out: `{(t.get('raw_output') or '')[:160]}`",
              "- note: _human review pending; mark improved/degraded/unchanged at Gate_", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model-dir", required=True)
    args = ap.parse_args()
    base_dir = args.base_model_dir
    summary = {"phases": {}, "stopped_at": None}

    repo_before = integrity.capture_repository(C.REPO_ROOT, PROTECTED)
    integrity.write_json(C.abs_repo(f"{INTEG}/repository-before.json"), repo_before)
    base_before = integrity.capture_inventory(base_dir)
    integrity.write_json(C.abs_repo(f"{INTEG}/base-model-before.json"), base_before)
    summary["base_model_root_hash"] = base_before["root_hash"]
    summary["base_model_file_count"] = base_before["file_count"]

    # Part 3: preserve accepted baseline; expose one as base/eval.json (never rerun)
    repro = _load(f"{RUN}/base/hf-eval-reproducibility.json")
    summary["baseline_reproducibility"] = repro["disposition"]
    if repro["disposition"] == "failed":
        summary["stopped_at"] = "baseline_not_accepted"
        _finish(summary, repo_before, base_before, base_dir)
        return
    if not os.path.exists(C.abs_repo(f"{RUN}/base/eval.json")):
        shutil.copyfile(C.abs_repo(f"{RUN}/base/hf-eval-run-1.json"),
                        C.abs_repo(f"{RUN}/base/eval.json"))

    def verify_base(tag):
        after = integrity.capture_inventory(base_dir)
        integrity.write_json(C.abs_repo(f"{INTEG}/base-model-after-{tag}.json"), after)
        v = integrity.verify_inventory(base_before, after)
        summary["phases"].setdefault("base_integrity", {})[tag] = v["ok"]
        return v

    try:
        # ---- LoRA 20-step ----
        lm, lc = train.run(C.abs_repo(LORA_CFG), backend_name="hf")
        summary["phases"]["lora"] = _phase(lm, lc)
        verify_base("lora")
        reloads_ok = all(r.get("ok") for r in lm.get("checkpoint_reload_results", []))
        if lm.get("status") != "completed" or not reloads_ok:
            summary["stopped_at"] = "lora_failed"
            _finish(summary, repo_before, base_before, base_dir)
            return
        le, lp = evaluate(HARNESS, "lora", f"{RUN}/lora/eval.json", "hf",
                          checkpoint_dir=C.abs_repo(f"{RUN}/lora/checkpoints/step-20"))
        summary["phases"]["lora_eval"] = {"path": os.path.relpath(lp, C.REPO_ROOT),
                                          "records": le["record_count"],
                                          "format_valid": le["format_valid_count"]}
        open(C.abs_repo(f"{RUN}/lora/eval-summary.md"), "w", encoding="utf-8", newline="\n").write(
            _eval_summary_md("lora", _load(f"{RUN}/base/eval.json"), le,
                             "datasets/dataset-a/compiled/experimental-v1/evaluation.jsonl"))

        # ---- QAT 20-step (only after LoRA passes) ----
        qm, qc = train.run(C.abs_repo(QAT_CFG), backend_name="hf")
        summary["phases"]["qat"] = _phase(qm, qc)
        verify_base("qat")
        qreloads_ok = all(r.get("ok") for r in qm.get("checkpoint_reload_results", []))
        if qm.get("status") != "completed" or not qreloads_ok:
            summary["stopped_at"] = "qat_failed"
            _finish(summary, repo_before, base_before, base_dir)
            return
        qe, qp = evaluate(HARNESS, "ternary-qat", f"{RUN}/ternary-qat/eval.json", "hf",
                          checkpoint_dir=C.abs_repo(f"{RUN}/ternary-qat/checkpoints/step-20"))
        summary["phases"]["qat_eval"] = {"path": os.path.relpath(qp, C.REPO_ROOT),
                                         "records": qe["record_count"],
                                         "format_valid": qe["format_valid_count"]}
        open(C.abs_repo(f"{RUN}/ternary-qat/eval-summary.md"), "w", encoding="utf-8", newline="\n").write(
            _eval_summary_md("ternary-qat", _load(f"{RUN}/base/eval.json"), qe,
                             "datasets/dataset-a/compiled/experimental-v1/evaluation.jsonl"))

        # ---- comparison ----
        md = build_comparison(_load(f"{RUN}/base/eval.json"), le, qe)
        os.makedirs(C.abs_repo(f"{RUN}/comparison"), exist_ok=True)
        open(C.abs_repo(f"{RUN}/comparison/comparison.md"), "w", encoding="utf-8", newline="\n").write(md)
        summary["comparison"] = {
            "base_format_valid": _load(f"{RUN}/base/eval.json")["format_valid_count"],
            "lora_format_valid": le["format_valid_count"],
            "qat_format_valid": qe["format_valid_count"]}

    except Exception as e:
        import traceback
        summary["exception"] = f"{type(e).__name__}: {e}"
        summary["traceback"] = traceback.format_exc()[-2500:]
        summary["stopped_at"] = summary["stopped_at"] or "exception"

    _finish(summary, repo_before, base_before, base_dir)


def _finish(summary, repo_before, base_before, base_dir):
    after = integrity.capture_inventory(base_dir)
    integrity.write_json(C.abs_repo(f"{INTEG}/base-model-after-final.json"), after)
    bv = integrity.verify_inventory(base_before, after)
    repo_after = integrity.capture_repository(C.REPO_ROOT, PROTECTED)
    integrity.write_json(C.abs_repo(f"{INTEG}/repository-after-qat.json"), repo_after)
    rv = integrity.verify_repository(repo_before, repo_after, authorized_prefixes=[RUN])
    integrity.write_json(C.abs_repo(f"{INTEG}/final-verification.json"),
                         {"base_model_unchanged": bv["ok"],
                          "repository_protected_files_unchanged": rv["ok"],
                          "unauthorized_writes": len(rv["unexpected_new_files_outside_run_paths"])
                          + len(rv["protected_tracked_files_changed"])})
    summary["base_model_unchanged"] = bv["ok"]
    summary["repository_unchanged"] = rv["ok"]
    integrity.write_json(C.abs_repo(f"{RUN}/train-18b-summary.json"), summary)
    print("TRAIN_18B_DONE", json.dumps({
        "stopped_at": summary["stopped_at"],
        "lora": (summary["phases"].get("lora") or {}).get("status"),
        "qat": (summary["phases"].get("qat") or {}).get("status"),
        "base_unchanged": summary.get("base_model_unchanged"),
        "repo_unchanged": summary.get("repository_unchanged")}))


if __name__ == "__main__":
    main()
