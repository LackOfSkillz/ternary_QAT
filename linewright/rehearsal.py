"""One-step execution rehearsal (Part 10).

python -m linewright.rehearsal

Generates a tiny DISPOSABLE synthetic dataset + config + stub base-model directory
in a temp dir, runs exactly one optimizer step through the guarded stub trainer,
saves + reloads a disposable checkpoint, and confirms the (stub) base-model
inventory is unchanged. The real 28-record Dataset A train file is NEVER used for
gradients here. Lightweight evidence (run manifest + integrity JSON) is retained
under training/runs/dataset-a-smoke-v1/; the synthetic temp dir is removed.
"""
import hashlib
import json
import os
import shutil
import tempfile

import yaml

from linewright import config as C
from linewright import train

REAL_SYSTEM_PROMPT = "datasets/dataset-a/prompts/linewright-training-system-v1.txt"


def _row(rid, task, user, assistant):
    return {"id": rid, "task_type": task, "style_profile": "none",
            "messages": [{"role": "system", "content": "sys"},
                         {"role": "user", "content": user},
                         {"role": "assistant", "content": assistant}],
            "metadata": {"split": "train", "source_hash": "synthetic"}}


def _write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def build_and_run():
    work = tempfile.mkdtemp(prefix="lw-rehearsal-")
    try:
        # tiny synthetic train (2) + eval (1), disjoint
        train_rows = [_row("syn-001", "focused_revision", "revise A", "A'"),
                      _row("syn-002", "focused_revision", "revise B", "B'")]
        eval_rows = [_row("syn-eval-001", "focused_revision", "revise C", "C'")]
        tp = os.path.join(work, "syn-train.jsonl")
        ep = os.path.join(work, "syn-eval.jsonl")
        train_h = _write_jsonl(tp, train_rows)
        eval_h = _write_jsonl(ep, eval_rows)

        # disposable stub "base model" directory to inventory + protect
        base = os.path.join(work, "stub-base")
        os.makedirs(base)
        for name, content in [("config.json", '{"model":"stub"}\n'),
                              ("weights.txt", "deterministic stub weights\n")]:
            open(os.path.join(base, name), "w", encoding="utf-8", newline="\n").write(content)

        sys_prompt = C.abs_repo(REAL_SYSTEM_PROMPT)
        cfg = {
            "experiment_id": "dataset-a-rehearsal-onestep",
            "production_approved": False, "experimental_use_only": True,
            "model": {"base_model": "stub-base",
                      "base_model_revision": "rehearsal",
                      "base_model_path": base},
            "paths": {"output_dir": "training/runs/dataset-a-smoke-v1/rehearsal"},
            "dataset": {"train_file": tp, "evaluation_file": ep,
                        "system_prompt_file": REAL_SYSTEM_PROMPT,
                        "train_checksum": train_h, "evaluation_checksum": eval_h,
                        "system_prompt_checksum": C.sha256_file(sys_prompt)},
            "reproducibility": {"seed": 20260721},
            "sequence": {"max_sequence_length": 2048},
            "optimization": {"max_steps": 1, "micro_batch_size": 1,
                             "gradient_accumulation_steps": 8},
            "intervals": {"checkpoint_interval_steps": 1},
        }
        cfg_path = os.path.join(work, "syn-config.yaml")
        with open(cfg_path, "w", encoding="utf-8", newline="\n") as fh:
            yaml.safe_dump(cfg, fh, sort_keys=False)

        manifest, code = train.run(cfg_path, max_steps_override=1,
                                   backend_name="stub", base_model_dir=base)
        result = {
            "rehearsal_config": cfg_path,
            "completed_steps": manifest.get("completed_steps"),
            "status": manifest.get("status"),
            "stop_reason": manifest.get("stop_reason"),
            "checkpoint_reload": manifest.get("checkpoint_reload_results"),
            "base_model_verification_ok": (manifest.get("base_model_verification") or {}).get("ok"),
            "repository_verification_ok": (manifest.get("repository_verification") or {}).get("ok"),
            "used_real_train_file_for_gradients": False,
            "exit_code": code,
        }
        # retain a small rehearsal summary under the authorized run root
        summ = C.abs_repo("training/runs/dataset-a-smoke-v1/rehearsal/rehearsal-summary.json")
        os.makedirs(os.path.dirname(summ), exist_ok=True)
        with open(summ, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(result, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        return result
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    build_and_run()
