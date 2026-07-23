"""Dispatch 28 — deterministic scorer for the Prompt-Effect v1 benchmark.

`check(c, text)` evaluates one typed ground-truth check. `score_output(task, text)` returns the
per-output mechanical result (required-change completion, returned-unchanged, protected accuracy,
unauthorized edits, output-shape, anti-results). Rules come ONLY from the frozen task manifest.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def _sentences(text):
    # split on sentence punctuation, consuming any closing quotes/brackets before the space
    return [s.strip() for s in re.split(r"(?<=[.!?])[\"'”’)\]]*\s+", text.strip()) if s.strip()]


def check(c, text):
    t = c["t"]
    if t == "absent":
        return c["v"].lower() not in text.lower()
    if t == "present":
        return c["v"].lower() in text.lower()
    if t == "preserve":
        return c["v"] in text
    if t == "max_openers":
        run = mx = 0
        for s in _sentences(text):
            if s.startswith(c["o"]):
                run += 1; mx = max(mx, run)
            else:
                run = 0
        return mx <= c["max"]
    if t == "absent_re":
        return re.search(c["v"], text, re.I) is None
    if t == "present_re":
        return re.search(c["v"], text, re.I) is not None
    raise ValueError(c)


def _is_removal(c):
    return c["t"] in ("absent", "max_openers", "absent_re")


def score_output(task, text):
    gt = task["ground_truth"]
    req = gt["required_changes"]
    req_results = [{"id": r["id"], "passed": check(r["check"], text)} for r in req]
    completed = sum(1 for r in req_results if r["passed"])
    all_completed = completed == len(req)

    # returned-unchanged: a revision task whose removal-type required changes ALL fail
    removals = [r for r in req if _is_removal(r["check"])]
    returned_unchanged = (bool(removals)
                          and all(not check(r["check"], text) for r in removals)
                          and not gt["valid_no_change_case"])

    prot = gt["protected_elements"]
    prot_results = [{"id": p["id"], "preserved": p["text"] in text} for p in prot]
    protected_ok = all(p["preserved"] for p in prot_results) if prot else True

    # unauthorized edits: an unaffected span dropped, or a forbidden change triggered
    unaffected = gt.get("unaffected_spans", [])
    unaffected_missing = [s for s in unaffected if s not in text]
    forb = gt["forbidden_changes"]
    forb_violations = [f["id"] for f in forb if not check(f["check"], text)]
    unauthorized_edit = bool(unaffected_missing) or bool(forb_violations)

    # output shape
    shape = gt["expected_output_shape"]
    shape_ok = True
    if shape == "json":
        m = re.search(r"\{.*\}", text, re.DOTALL)
        try:
            shape_ok = m is not None and isinstance(json.loads(m.group(0)), dict)
        except Exception:
            shape_ok = False

    return {
        "task_id": task["task_id"], "task_family": task["task_family"],
        "required_total": len(req), "required_completed": completed,
        "all_required_completed": all_completed, "required_results": req_results,
        "returned_unchanged": returned_unchanged,
        "protected_total": len(prot), "protected_ok": protected_ok,
        "protected_corruption": (not protected_ok) if prot else False,
        "unauthorized_edit": unauthorized_edit,
        "unaffected_missing": unaffected_missing, "forbidden_violations": forb_violations,
        "output_shape_ok": shape_ok,
        # a clean success = all required changes made AND nothing unauthorized AND protected intact AND shape ok
        "clean_success": all_completed and not unauthorized_edit and protected_ok and shape_ok,
    }


def load_tasks():
    p = os.path.join(HERE, "task-manifest.jsonl")
    return {t["task_id"]: t for t in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}


def validate_sources():
    """Self-consistency: for revision/protected tasks, each removal-type required check must FAIL on
    the SOURCE (the defect is really present), and protected text must be present in the source."""
    tasks = load_tasks()
    problems = []
    for tid, t in tasks.items():
        src = t["source_passage"]
        if not src:
            continue
        for r in t["ground_truth"]["required_changes"]:
            if _is_removal(r["check"]) and check(r["check"], src):
                problems.append(f"{tid}: removal check {r['id']} PASSES on source (defect absent) — check not grounded")
        for p in t["ground_truth"]["protected_elements"]:
            if p["text"] not in src:
                problems.append(f"{tid}: protected {p['id']} not present in source")
    return problems


if __name__ == "__main__":
    probs = validate_sources()
    if probs:
        print("SOURCE VALIDATION PROBLEMS:")
        for p in probs:
            print("  -", p)
    else:
        print("source self-consistency: OK (every removal check is grounded; protected text present)")
