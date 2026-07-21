"""Evaluation entry point (Part 8).

python -m linewright.eval --harness <harness.yaml> --target <base|lora|ternary-qat> --out <json>

Loads the held-out evaluation records, generates with the selected backend (stub on
the CPU host), runs deterministic structural checks, and stores raw+parsed output
for later rubric review. Invalid model output is REPORTED, never silently repaired.
"""
import argparse
import hashlib
import json
import os
import re

import yaml

from linewright import config as C
from linewright.backends import get_backend
from linewright import runtime


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _try_json(s):
    try:
        return json.loads(s)
    except Exception:
        return None


def _try_yaml_map(s):
    try:
        obj = yaml.safe_load(s)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def expected_format(task_type, gold):
    if _try_json(gold) is not None:
        return "json"
    if task_type == "scene_contract" and _try_yaml_map(gold) is not None:
        return "yaml"
    return "prose"


def structural_check(task_type, gold, output):
    """Deterministic checks on the model output vs the expected structure."""
    fmt = expected_format(task_type, gold)
    checks = {"expected_format": fmt}
    parsed = None
    if fmt == "json":
        parsed = _try_json(output)
        checks["format_valid"] = parsed is not None
        gold_obj = _try_json(gold)
        # structured no-change: gold has changed:false with a text field
        if isinstance(gold_obj, dict) and gold_obj.get("changed") is False:
            checks["no_change_case"] = True
            ok = (isinstance(parsed, dict) and parsed.get("changed") is False
                  and "text" in parsed and parsed.get("text") == gold_obj.get("text"))
            checks["no_change_preserved"] = bool(ok)
    elif fmt == "yaml":
        parsed = _try_yaml_map(output)
        checks["format_valid"] = parsed is not None
    else:
        checks["format_valid"] = bool(output and output.strip())
    return checks, parsed


def evaluate(harness_path, target, out_path, backend_name="stub"):
    harness = yaml.safe_load(open(harness_path, encoding="utf-8"))
    ds = harness["dataset"]
    eval_file = C.abs_repo(ds["evaluation_file"])
    # pinned hash gate
    if ds.get("evaluation_checksum"):
        actual = C.sha256_file(eval_file)
        if actual != ds["evaluation_checksum"]:
            raise SystemExit(f"evaluation hash mismatch: {actual[:12]}… != pinned")
    gen = harness.get("generation", {})
    rows = [json.loads(l) for l in open(eval_file, encoding="utf-8") if l.strip()]

    if backend_name == "hf":
        # deterministic single-example generation (batch size 1)
        import torch
        if gen.get("seed") is not None:
            torch.manual_seed(int(gen["seed"]))
        model_cfg = dict(harness.get("model", {}))
        cfg = {"model": model_cfg,
               "paths": {"cache_dir": model_cfg.get("cache_dir")},
               "reproducibility": {"seed": gen.get("seed", 0)},
               "sequence": {"max_sequence_length": harness.get("max_sequence_length", 2048)}}
        backend = get_backend("hf").from_config(cfg, target=target, for_training=False)
        env_meta = dict(backend.diagnostics)
    else:
        backend = get_backend(backend_name).from_config(
            {"reproducibility": {"seed": gen.get("seed", 0)}}, target=target)
        env_meta = {}

    records = []
    for row in sorted(rows, key=lambda r: r["id"]):
        msgs = {m["role"]: m["content"] for m in row["messages"]}
        prompt_messages = [{"role": "system", "content": msgs.get("system", "")},
                           {"role": "user", "content": msgs.get("user", "")}]
        gold = msgs.get("assistant", "")
        output = backend.generate(prompt_messages, gen)
        checks, parsed = structural_check(row["task_type"], gold, output)
        gm = {"temperature": gen.get("temperature"), "top_p": gen.get("top_p"),
              "seed": gen.get("seed"), "max_new_tokens": gen.get("max_new_tokens"),
              "backend": backend_name, "target": target}
        gm.update(getattr(backend, "last_gen_meta", {}) or {})
        records.append({
            "record_id": row["id"], "task_type": row["task_type"],
            "input_hash": _sha(msgs.get("system", "") + "\n\n" + msgs.get("user", "")),
            "raw_output": output, "parsed_output": parsed,
            "format_valid": checks.get("format_valid"),
            "deterministic_checks": checks, "generation_metadata": gm,
        })

    if backend_name == "hf" and hasattr(backend, "unload"):
        backend.unload()

    report = {
        "eval_id": harness.get("eval_id"),
        "target": target, "backend": backend_name,
        "evaluation_checksum": ds.get("evaluation_checksum"),
        "record_count": len(records),
        "format_valid_count": sum(1 for r in records if r["format_valid"]),
        "environment": env_meta,
        "records": records,
    }
    writer = runtime.AuthorizedWriter(harness_authorized_roots())
    safe = writer.resolve(C.abs_repo(out_path))
    os.makedirs(os.path.dirname(safe), exist_ok=True)
    with open(safe, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return report, safe


def harness_authorized_roots():
    return [os.path.join(C.REPO_ROOT, r) for r in C.AUTHORIZED_OUTPUT_ROOTS]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", required=True)
    ap.add_argument("--target", required=True, choices=["base", "lora", "ternary-qat"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--backend", default="stub")
    args = ap.parse_args()
    report, path = evaluate(args.harness, args.target, args.out, args.backend)
    print(f"eval target={args.target} records={report['record_count']} "
          f"format_valid={report['format_valid_count']} -> {os.path.relpath(path, C.REPO_ROOT)}")


if __name__ == "__main__":
    main()
