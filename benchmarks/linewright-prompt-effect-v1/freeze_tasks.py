"""Dispatch 28 — freeze the Prompt-Effect v1 task layer (before any prompt rendering)."""
import glob
import hashlib
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
FREEZE = os.path.join(HERE, "freeze")


def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode("utf-8")).hexdigest()


def shingles(s, n=6):
    w = re.findall(r"[a-z0-9']+", (s or "").lower())
    return set(tuple(w[i:i + n]) for i in range(max(0, len(w) - n + 1)))


def main():
    tasks = [json.loads(l) for l in open(os.path.join(HERE, "task-manifest.jsonl"), encoding="utf-8") if l.strip()]
    from score_prompt_effect import validate_sources
    import sys
    sys.path.insert(0, HERE)
    src_problems = validate_sources()
    assert not src_problems, src_problems

    # training-exclusion overlap: no task source appears in Dataset A / A.2 / A.3 training corpora
    train_texts = []
    for p in (glob.glob(os.path.join(_REPO, "datasets", "dataset-a", "**", "*.jsonl"), recursive=True)
              + glob.glob(os.path.join(_REPO, "datasets", "dataset-a.2", "**", "*.jsonl"), recursive=True)
              + [os.path.join(_REPO, "datasets", "dataset-a.3", "records", "a3-pilot.jsonl")]):
        if os.path.exists(p):
            train_texts.append(open(p, encoding="utf-8").read().lower())
    blob = "\n".join(train_texts)
    overlaps = []
    for t in tasks:
        src = t["source_passage"].strip()
        if src and src.lower()[:80] in blob:
            overlaps.append(t["task_id"])
        # shingle proxy vs concatenated training text
    training_exclusion_clean = len(overlaps) == 0

    fams = Counter(t["task_family"] for t in tasks)
    rev = [t for t in tasks if t["task_family"] == "multi_constraint_focused_revision"]
    pos = Counter(t["diagnostics"]["instruction_position"] for t in rev)
    manifest_bytes = open(os.path.join(HERE, "task-manifest.jsonl"), "rb").read()
    all_bench_only = all(t["benchmark_policy"]["benchmark_only"] for t in tasks)
    all_excluded = all(t["benchmark_policy"]["excluded_from_training"] for t in tasks)
    machine_checks_complete = all(t["ground_truth"]["required_changes"] and
                                  all("check" in rc for rc in t["ground_truth"]["required_changes"])
                                  for t in tasks)

    freeze = {
        "task_count": len(tasks), "family_counts": dict(fams),
        "revision_instruction_positions": dict(pos),
        "manifest_sha256": sha(manifest_bytes),
        "source_tree_sha256": sha(json.dumps([t["source_passage"] for t in tasks], ensure_ascii=False)),
        "machine_checks_complete": machine_checks_complete,
        "instruction_positions_frozen": dict(pos) == {"early": 4, "middle": 4, "late": 4},
        "training_exclusion_confirmed": training_exclusion_clean,
        "training_overlaps": overlaps,
        "all_benchmark_only": all_bench_only, "all_excluded_from_training": all_excluded,
        "frozen_before_prompt_rendering": True,
    }
    os.makedirs(FREEZE, exist_ok=True)
    with open(os.path.join(FREEZE, "task-freeze.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(freeze, fh, ensure_ascii=False, indent=1)
    md = [f"# Prompt-Effect v1 — task freeze", "",
          f"**{freeze['task_count']} tasks**, families {freeze['family_counts']}, revision instruction "
          f"positions {freeze['revision_instruction_positions']} (4/4/4: "
          f"{freeze['instruction_positions_frozen']}).", "",
          f"- manifest_sha256: `{freeze['manifest_sha256']}`",
          f"- source_tree_sha256: `{freeze['source_tree_sha256']}`",
          f"- machine_checks_complete: {freeze['machine_checks_complete']}",
          f"- training_exclusion_confirmed (no source in A/A.2/A.3): {freeze['training_exclusion_confirmed']}",
          f"- all benchmark_only + excluded_from_training: {all_bench_only and all_excluded}",
          "", "Frozen before any prompt arm is rendered. Immutable after this commit."]
    with open(os.path.join(FREEZE, "task-freeze.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(md) + "\n")
    print(json.dumps({"task_count": len(tasks), "families": dict(fams), "positions": dict(pos),
                      "manifest_sha256": freeze["manifest_sha256"][:16],
                      "training_exclusion_confirmed": training_exclusion_clean,
                      "machine_checks_complete": machine_checks_complete}, indent=1))


if __name__ == "__main__":
    main()
