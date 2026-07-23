"""Dispatch 28A — freeze the task layer. Records content hashes of the manifest, the per-task tree,
the schema, and the validation report, plus the design invariants. MUST run (and be committed)
before any prompt rendering. Refuses to freeze unless validation outcome != invalid_freeze_blocked.
"""
import hashlib
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def tree_sha(root):
    h = hashlib.sha256()
    for dp, _, fns in sorted(os.walk(root)):
        for fn in sorted(fns):
            p = os.path.join(dp, fn)
            h.update(os.path.relpath(p, root).replace("\\", "/").encode())
            h.update(open(p, "rb").read())
    return h.hexdigest()


def main():
    tasks = [json.loads(l) for l in open(os.path.join(HERE, "task-manifest.jsonl"), encoding="utf-8") if l.strip()]
    val = json.load(open(os.path.join(HERE, "reports", "task-validation.json"), encoding="utf-8"))
    if val["outcome"] == "invalid_freeze_blocked":
        raise SystemExit("FREEZE BLOCKED: task validation is invalid_freeze_blocked")
    fams = Counter(t["task_family"] for t in tasks)
    rev = [t for t in tasks if t["task_family"] == "multi_constraint_focused_revision"]
    pos = Counter(t["diagnostics"]["instruction_position"] for t in rev)

    freeze = {
        "dispatch": "28A", "instrument": "linewright-prompt-execution-v1",
        "task_count": len(tasks), "family_distribution": dict(fams),
        "task_manifest_sha256": sha(os.path.join(HERE, "task-manifest.jsonl")),
        "task_manifest_yaml_sha256": sha(os.path.join(HERE, "task-manifest.yaml")),
        "task_tree_sha256": tree_sha(os.path.join(HERE, "tasks")),
        "schema_sha256": sha(os.path.join(HERE, "schemas", "task-manifest.schema.json")),
        "checks_module_sha256": sha(os.path.join(HERE, "validators", "checks.py")),
        "validation_report_sha256": sha(os.path.join(HERE, "reports", "task-validation.json")),
        "validation_outcome": val["outcome"],
        "instruction_positions": dict(pos),
        "comprehension_probes": [t["task_id"] for t in tasks if t.get("comprehension_probe", {}).get("enabled")],
        "machine_checks_complete": True,
        "benchmark_exclusion_confirmed": all(
            t["benchmark_policy"]["benchmark_only"] and t["benchmark_policy"]["excluded_from_training"]
            and t["benchmark_policy"]["immutable_after_freeze"] for t in tasks),
        "dataset_and_dispatch28_overlap": len(val["dataset_overlap"]),
        "frozen_before_prompt_rendering": True,
        "frozen_at": "2026-07-23",
        "commit_sha": None,  # recorded in the follow-up docs record after commit
    }
    with open(os.path.join(HERE, "freeze", "task-freeze.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(freeze, fh, ensure_ascii=False, indent=1)
    md = [
        "# Task freeze — LineWright Prompt-Execution v1 (Dispatch 28A)", "",
        f"- Frozen: {freeze['frozen_at']} — **before any prompt rendering**",
        f"- Tasks: {freeze['task_count']} — {freeze['family_distribution']}",
        f"- Instruction positions (focused-revision): {freeze['instruction_positions']}",
        f"- Comprehension probes: {freeze['comprehension_probes']}",
        f"- Validation outcome: **{freeze['validation_outcome']}**",
        f"- Benchmark-exclusion confirmed: {freeze['benchmark_exclusion_confirmed']}",
        f"- Dataset/Dispatch-28 overlap: {freeze['dataset_and_dispatch28_overlap']}", "",
        "## Hashes",
        f"- task-manifest.jsonl: `{freeze['task_manifest_sha256']}`",
        f"- task-manifest.yaml: `{freeze['task_manifest_yaml_sha256']}`",
        f"- tasks/ tree: `{freeze['task_tree_sha256']}`",
        f"- schema: `{freeze['schema_sha256']}`",
        f"- checks module: `{freeze['checks_module_sha256']}`",
        f"- validation report: `{freeze['validation_report_sha256']}`", "",
        "The task layer is immutable after this freeze. Prompt rendering consumes it read-only.",
    ]
    with open(os.path.join(HERE, "freeze", "task-freeze.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(md))
    print(json.dumps({"task_manifest_sha256": freeze["task_manifest_sha256"],
                      "task_tree_sha256": freeze["task_tree_sha256"],
                      "outcome": freeze["validation_outcome"],
                      "positions": freeze["instruction_positions"]}, indent=1))


if __name__ == "__main__":
    main()
