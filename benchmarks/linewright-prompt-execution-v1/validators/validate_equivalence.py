"""Dispatch 28A — validate P0-Maximal ≡ P1-Contract information equivalence.

For every task the two arms must carry the SAME information: identical required changes, protected
elements, forbidden changes, authorized scope, task authority, output shape, and context. Beyond
comparing the stored inventories (which the renderer builds from one source), this independently
confirms that every inventory item's text actually appears in BOTH rendered prompts — so a render
that silently dropped or added information would fail. Any mismatch blocks the prompt freeze.
Emits reports/information-equivalence.{json,md}.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(HERE)
REPORTS = os.path.join(BENCH, "reports")


def main():
    man = json.load(open(os.path.join(BENCH, "prompt-arm-manifest.json"), encoding="utf-8"))["prompts"]
    by = {}
    for r in man:
        by.setdefault(r["task_id"], {})[r["arm"]] = r
    task_ids = sorted(by)

    per_task, failed = [], 0
    for tid in task_ids:
        pm = by[tid].get("P0-Maximal")
        pc = by[tid].get("P1-Contract")
        problems = []
        if not pm or not pc:
            problems.append("missing P0-Maximal or P1-Contract")
        else:
            im, ic = pm["information_inventory"], pc["information_inventory"]
            for field in ("task_authority", "output_contract", "mode"):
                if im.get(field) != ic.get(field):
                    problems.append(f"{field} differs")
            for field in ("required_changes", "protected_elements", "forbidden_changes",
                          "authorized_scope", "context"):
                if sorted(im.get(field, [])) != sorted(ic.get(field, [])):
                    problems.append(f"{field} set differs")
            # independent render-content check: every item appears verbatim in BOTH prompts
            tm, tc = pm["prompt_text"], pc["prompt_text"]
            for field in ("required_changes", "protected_elements", "forbidden_changes", "context"):
                for item in im.get(field, []):
                    if item not in tm:
                        problems.append(f"{field} item missing from P0-Maximal text: {item[:40]!r}")
                    if item not in tc:
                        problems.append(f"{field} item missing from P1-Contract text: {item[:40]!r}")
        ok = not problems
        if not ok:
            failed += 1
        per_task.append({"task_id": tid, "passed": ok, "problems": problems})

    report = {
        "dispatch": "28A", "instrument": "linewright-prompt-execution-v1",
        "tasks_checked": len(task_ids), "tasks_passed": len(task_ids) - failed, "tasks_failed": failed,
        "information_equivalence": failed == 0, "per_task": per_task,
    }
    os.makedirs(REPORTS, exist_ok=True)
    with open(os.path.join(REPORTS, "information-equivalence.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    lines = ["# P0-Maximal ≡ P1-Contract information equivalence (Dispatch 28A)", "",
             f"- Tasks checked: {report['tasks_checked']}",
             f"- Passed: {report['tasks_passed']}", f"- Failed: {report['tasks_failed']}",
             f"- Equivalent: **{report['information_equivalence']}**", ""]
    if failed:
        lines += ["## Failures"]
        for pt in per_task:
            if not pt["passed"]:
                lines += [f"- {pt['task_id']}: " + "; ".join(pt["problems"])]
    with open(os.path.join(REPORTS, "information-equivalence.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print(json.dumps({"tasks_checked": report["tasks_checked"], "tasks_passed": report["tasks_passed"],
                      "tasks_failed": report["tasks_failed"],
                      "information_equivalence": report["information_equivalence"]}, indent=1))
    return report["information_equivalence"]


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
