"""Dispatch 28A — freeze the prompt layer. Records counts, information-equivalence result, and
content hashes. MUST run (and be committed) before any generation. Refuses to freeze unless
P0-Maximal ≡ P1-Contract equivalence passed and no generation-output artifacts exist.
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
    man = json.load(open(os.path.join(HERE, "prompt-arm-manifest.json"), encoding="utf-8"))["prompts"]
    eq = json.load(open(os.path.join(HERE, "reports", "information-equivalence.json"), encoding="utf-8"))
    if not eq["information_equivalence"]:
        raise SystemExit("FREEZE BLOCKED: P0-Maximal != P1-Contract information equivalence failed")
    counts = Counter(r["arm"] for r in man)
    expected = {"P0-Realistic": 30, "P0-Maximal": 30, "P1-Contract": 30, "P3-Ideal": 10}
    if dict(counts) != expected:
        raise SystemExit(f"FREEZE BLOCKED: prompt counts {dict(counts)} != {expected}")
    if any(r["generation_authorized"] for r in man):
        raise SystemExit("FREEZE BLOCKED: a prompt record has generation_authorized True")
    # no generation outputs may exist yet
    stray = [d for d in ("outputs", "normalized-results", "raw-outputs", "generations")
             if os.path.isdir(os.path.join(HERE, d))]
    if stray:
        raise SystemExit(f"FREEZE BLOCKED: generation-output directories present: {stray}")

    freeze = {
        "dispatch": "28A", "instrument": "linewright-prompt-execution-v1",
        "expected_prompt_count": 100, "actual_prompt_count": len(man),
        "p0_realistic_count": counts["P0-Realistic"], "p0_maximal_count": counts["P0-Maximal"],
        "p1_contract_count": counts["P1-Contract"], "p3_ideal_count": counts["P3-Ideal"],
        "p3_compiled_status": "deferred",
        "information_equivalence_passed": eq["information_equivalence"],
        "information_equivalence_tasks": f"{eq['tasks_passed']}/{eq['tasks_checked']}",
        "prompt_manifest_sha256": sha(os.path.join(HERE, "prompt-arm-manifest.json")),
        "prompt_plan_sha256": sha(os.path.join(HERE, "prompt-plan.json")),
        "prompt_tree_sha256": tree_sha(os.path.join(HERE, "prompts")),
        "p3_ideal_subset_sha256": sha(os.path.join(HERE, "p3-ideal-subset.json")),
        "equivalence_report_sha256": sha(os.path.join(HERE, "reports", "information-equivalence.json")),
        "renderer_sha256": sha(os.path.join(HERE, "render_prompts.py")),
        "frozen_before_generation": True, "generation_authorized": False,
        "no_generation_outputs_present": True,
        "frozen_at": "2026-07-23", "commit_sha": None,
    }
    with open(os.path.join(HERE, "freeze", "prompt-freeze.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(freeze, fh, ensure_ascii=False, indent=1)
    md = [
        "# Prompt freeze — LineWright Prompt-Execution v1 (Dispatch 28A)", "",
        f"- Frozen: {freeze['frozen_at']} — **before any generation**",
        f"- Prompts: {freeze['actual_prompt_count']} (expected 100) — "
        f"P0-Realistic {freeze['p0_realistic_count']} / P0-Maximal {freeze['p0_maximal_count']} / "
        f"P1-Contract {freeze['p1_contract_count']} / P3-Ideal {freeze['p3_ideal_count']} / "
        f"P3-Compiled {freeze['p3_compiled_status']}",
        f"- P0-Maximal ≡ P1-Contract equivalence: **{freeze['information_equivalence_passed']}** "
        f"({freeze['information_equivalence_tasks']})",
        f"- generation_authorized: {freeze['generation_authorized']}",
        f"- Generation outputs present: {not freeze['no_generation_outputs_present']}", "",
        "## Hashes",
        f"- prompt-arm-manifest.json: `{freeze['prompt_manifest_sha256']}`",
        f"- prompt-plan.json: `{freeze['prompt_plan_sha256']}`",
        f"- prompts/ tree: `{freeze['prompt_tree_sha256']}`",
        f"- p3-ideal-subset.json: `{freeze['p3_ideal_subset_sha256']}`",
        f"- equivalence report: `{freeze['equivalence_report_sha256']}`",
        f"- renderer: `{freeze['renderer_sha256']}`", "",
        "The prompt layer is immutable after this freeze. Generation is NOT authorized in this "
        "dispatch; it requires a new, separately-authorized dispatch.",
    ]
    with open(os.path.join(HERE, "freeze", "prompt-freeze.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(md))
    print(json.dumps({"actual_prompt_count": len(man), "counts": dict(counts),
                      "equivalence": freeze["information_equivalence_passed"],
                      "prompt_tree_sha256": freeze["prompt_tree_sha256"]}, indent=1))


if __name__ == "__main__":
    main()
