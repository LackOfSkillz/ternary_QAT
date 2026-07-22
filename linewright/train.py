"""Guarded training entry point (Parts 2,3,5,6,7,10).

python -m linewright.train --config <cfg> [--validate-only | --dry-run | --max-steps-override N]

On the CPU host this runs a deterministic STUB training loop (no real gradients) so
the guards, integrity inventory, checkpoint/reload, and run manifest are exercised
end to end. Real gradient training runs on the GX10 image (backend: hf) and is NOT
performed by this dispatch. Every write goes through the authorized-path guard.
"""
import argparse
import json
import os

from linewright import config as C
from linewright import integrity, runtime
from linewright.backends import get_backend

RUN_ROOT = os.path.join("training", "runs", "dataset-a-smoke-v1")
PROTECTED_GLOBS = [
    "datasets/dataset-a/compiled/experimental-v1/*.jsonl",
    "datasets/dataset-a/prompts/*.txt",
    "ternary/*.py",
]


def _load_and_validate(cfg_path, overrides):
    cfg = C.load_config(cfg_path)
    result = C.validate_config(cfg, cfg_path, require_hashes=True, check_overrides=overrides)
    return cfg, result


def run(cfg_path, validate_only=False, dry_run=False, max_steps_override=None,
        backend_name="stub", inject=None, base_model_dir=None,
        capture_base_integrity=True):
    overrides = {}
    if max_steps_override is not None:
        overrides["max_steps"] = int(max_steps_override)
    cfg, result = _load_and_validate(cfg_path, overrides)

    for line in result.messages:
        print(line)
    for p in result.problems:
        print("  !!", p)
    if validate_only:
        return {"validate_only": True, "ok": result.ok}, (0 if result.ok else 1)
    if not result.ok:
        return {"ok": False, "stop_reason": "config_invalid",
                "problems": result.problems}, 1
    if inject and backend_name == "hf":
        raise ValueError("failure injection is not permitted in an hf run")

    # target is inferred from the config's own blocks so it is correct for the
    # smoke configs AND the one-step rehearsal configs (experiment_id varies).
    if "ternary_qat" in cfg:
        target = "ternary-qat"
    elif "lora" in cfg:
        target = "lora"
    else:
        target = "lora"
    out_dir = C.abs_repo(cfg["paths"]["output_dir"])
    # authorize every declared run root; per-run integrity lives under this run's
    # own output_dir so smoke and calibration runs never collide.
    writer = runtime.AuthorizedWriter([C.abs_repo(r) for r in C.AUTHORIZED_OUTPUT_ROOTS])
    integ_dir = os.path.join(out_dir, "integrity")

    # ---- integrity: capture BEFORE ----
    repo_before = integrity.capture_repository(C.REPO_ROOT, PROTECTED_GLOBS)
    integrity.write_json(writer.resolve(os.path.join(integ_dir, "repository-before.json")),
                         repo_before)
    base_before = None
    base_dir = base_model_dir or cfg.get("model", {}).get("base_model_path")
    if not capture_base_integrity:
        base_dir = None                        # orchestrator handles base integrity
    if base_dir and os.path.isdir(base_dir):
        base_before = integrity.capture_inventory(base_dir)
        integrity.write_json(writer.resolve(os.path.join(integ_dir, "base-model-before.json")),
                             base_before)

    max_steps = overrides.get("max_steps", cfg["optimization"]["max_steps"])
    ckpt_int = cfg.get("intervals", {}).get("checkpoint_interval_steps", 10)
    seed = cfg.get("reproducibility", {}).get("seed", 0)
    # A backend that trains is created only for a real run (not dry-run) so the 4B
    # model is not loaded during a dry-run. inject is a stub-only test facility.
    backend = None
    if not dry_run:
        backend = get_backend(backend_name).from_config(
            cfg, target=target, for_training=True, inject=inject)

    manifest = {
        "run_id": f"{cfg['experiment_id']}-{target}",
        "target": target, "config_path": os.path.relpath(cfg_path, C.REPO_ROOT),
        "config_sha256": C.sha256_file(cfg_path),
        "effective_config": {"max_steps": max_steps,
                             "effective_batch_size": C.effective_batch_size(cfg),
                             "seed": seed,
                             "overrides": overrides},
        "base_model": cfg.get("model", {}).get("base_model"),
        "base_model_revision": cfg.get("model", {}).get("base_model_revision"),
        "base_model_inventory_hash": base_before["root_hash"] if base_before else None,
        "train_file": cfg["dataset"]["train_file"],
        "train_hash": cfg["dataset"].get("train_checksum"),
        "system_prompt_hash": cfg["dataset"].get("system_prompt_checksum"),
        "seed": seed, "backend": backend_name,
        "git_head": repo_before["head"], "git_branch": repo_before["branch"],
        "requested_steps": max_steps, "completed_steps": 0,
        "checkpoint_reload_results": [], "output_files": [],
        "backend_diagnostics": getattr(backend, "diagnostics", {}) if backend else {},
    }

    if dry_run:
        manifest.update({"status": "dry_run_ok", "stop_reason": "dry_run",
                         "completed_steps": 0})
        _finish(manifest, writer, out_dir, integ_dir, base_before, base_dir, repo_before)
        return manifest, 0

    grad_mon = runtime.GradientMonitor(
        **(cfg.get("gradient_monitor") or {"max_global_norm": 100.0,
                                           "consecutive_step_limit": 2}))
    stall = runtime.StallMonitor()
    status, stop_reason = "completed", "max_steps_reached"
    completed = 0
    step_metrics = []
    try:
        for step in range(1, max_steps + 1):
            loss, grad_norm = backend.train_step(step, inject=inject)
            batch_ids = getattr(backend, "last_batch_ids", None) or ["<stub-batch>"]
            runtime.check_loss_finite(loss, step=step, lr=cfg["optimization"].get("learning_rate"),
                                      batch_ids=batch_ids)
            grad_mon.observe(grad_norm, step=step)     # raw-norm rail (abort BEFORE step)
            stall.observe(step, loss_available=True)
            # all rails passed on the RAW gradient -> apply the (clipped) optimizer step
            if hasattr(backend, "optimizer_step"):
                backend.optimizer_step()
            entry = {"step": step, "loss": round(float(loss), 6),
                     "grad_norm": round(float(grad_norm), 6), "batch_ids": batch_ids}
            entry.update(getattr(backend, "last_step_meta", {}) or {})
            step_metrics.append(entry)
            manifest["step_metrics"] = step_metrics
            completed = step
            if step % ckpt_int == 0 or step == max_steps:
                ck = writer.resolve(os.path.join(out_dir, "checkpoints", f"step-{step}"))
                backend.save_checkpoint(ck, writer=writer)
                reload_result = runtime.verify_checkpoint_reload(ck, backend=backend_name)
                manifest["checkpoint_reload_results"].append(
                    {"step": step, "checkpoint": os.path.relpath(ck, C.REPO_ROOT),
                     **reload_result})
                if not reload_result.get("ok"):
                    raise runtime.StopCondition("checkpoint_reload_failure",
                                                {"step": step, "checkpoint": ck})
    except runtime.StopCondition as sc:
        status, stop_reason = "aborted", sc.reason
        manifest["stop_detail"] = sc.detail

    manifest.update({"status": status, "stop_reason": stop_reason,
                     "completed_steps": completed,
                     "gradient_warnings": grad_mon.warnings})
    _finish(manifest, writer, out_dir, integ_dir, base_before, base_dir, repo_before)
    return manifest, (0 if status == "completed" else 2)


def _finish(manifest, writer, out_dir, integ_dir, base_before, base_dir, repo_before):
    # ---- integrity: capture AFTER + verify ----
    if base_before and base_dir and os.path.isdir(base_dir):
        base_after = integrity.capture_inventory(base_dir)
        integrity.write_json(writer.resolve(os.path.join(integ_dir, "base-model-after.json")),
                             base_after)
        base_verify = integrity.verify_inventory(base_before, base_after)
        integrity.write_json(writer.resolve(os.path.join(integ_dir, "base-model-verification.json")),
                             base_verify)
        manifest["base_model_verification"] = base_verify
    repo_after = integrity.capture_repository(C.REPO_ROOT, PROTECTED_GLOBS)
    integrity.write_json(writer.resolve(os.path.join(integ_dir, "repository-after.json")),
                         repo_after)
    repo_verify = integrity.verify_repository(
        repo_before, repo_after,
        authorized_prefixes=[r.replace("\\", "/") for r in C.AUTHORIZED_OUTPUT_ROOTS])
    integrity.write_json(writer.resolve(os.path.join(integ_dir, "repository-verification.json")),
                         repo_verify)
    manifest["repository_verification"] = repo_verify
    full = runtime.build_run_manifest(**manifest)
    man_path = writer.resolve(os.path.join(out_dir, "run-manifest.json"))
    with writer.open(man_path, "w") as fh:
        json.dump(full, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print(f"[{manifest['target']}] status={manifest['status']} "
          f"reason={manifest['stop_reason']} steps={manifest['completed_steps']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--validate-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-steps-override", type=int)
    ap.add_argument("--backend", default="stub")
    ap.add_argument("--inject", help="failure injection: nan_loss|inf_loss|nan_grad|inf_grad|explode_grad")
    ap.add_argument("--base-model-dir", help="override base-model dir to inventory (rehearsal)")
    args = ap.parse_args()
    _manifest, code = run(args.config, validate_only=args.validate_only,
                          dry_run=args.dry_run, max_steps_override=args.max_steps_override,
                          backend_name=args.backend, inject=args.inject,
                          base_model_dir=args.base_model_dir)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
