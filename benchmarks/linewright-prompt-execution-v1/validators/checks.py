"""Dispatch 28A — deterministic, machine-checkable ground-truth evaluator for the LineWright
Prompt-Execution v1 instrument.

This module is the single source of truth for check semantics. It is imported by the task
builder (for grounding self-checks), the task/equivalence validators, and — in a LATER dispatch —
the scorer. No LLM grader is used for primary task correctness.

A check is a small typed dict with field "t":
  {"t": "absent",      "v": str}     phrase must be ABSENT (case-insensitive)
  {"t": "present",     "v": str}     phrase must be PRESENT (case-insensitive)
  {"t": "preserve",    "v": str}     span must appear VERBATIM (case-sensitive, exact)
  {"t": "absent_re",   "v": regex}   regex must NOT match (case-insensitive)
  {"t": "present_re",  "v": regex}   regex MUST match (case-insensitive)
  {"t": "max_openers", "o": str, "max": int}   repeated sentence-opener run <= max
  {"t": "shape_json",  "keys": [str]}          output parses as a JSON object with all keys
  {"t": "shape_list",  "min": int}             output is a numbered/bulleted list of >= min items
`check(c, text)` returns True when the condition HOLDS in `text`.
"""
import json
import re

# check-type families used for grounding + returned-unchanged semantics
REMOVAL_TYPES = ("absent", "absent_re", "max_openers")     # a defect the model must REMOVE/REDUCE
ADDITION_TYPES = ("present", "present_re")                  # a replacement/fact the model must ADD
SHAPE_TYPES = ("shape_json", "shape_list")
# families where the source IS the text being revised — only these get defect-in-source grounding.
# canon_continuation / constraint_bound_scene / structured_protocol legitimately reference or
# extract from their source, so an "addition present in source" is expected, not a defect.
REVISION_FAMILIES = ("multi_constraint_focused_revision", "protected_text_revision",
                     "voice_preserving_revision")


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
    if t == "absent_re":
        return re.search(c["v"], text, re.I) is None
    if t == "present_re":
        return re.search(c["v"], text, re.I) is not None
    if t == "max_openers":
        run = mx = 0
        for s in _sentences(text):
            if s.startswith(c["o"]):
                run += 1
                mx = max(mx, run)
            else:
                run = 0
        return mx <= c["max"]
    if t == "shape_json":
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return False
        try:
            obj = json.loads(m.group(0))
        except Exception:
            return False
        return isinstance(obj, dict) and all(k in obj for k in c.get("keys", []))
    if t == "shape_list":
        items = re.findall(r"(?m)^\s*(?:\d+[.)]|[-*•])\s+\S", text)
        return len(items) >= c.get("min", 1)
    raise ValueError(f"unknown check type: {c}")


def is_removal(c):
    return c["t"] in REMOVAL_TYPES


def is_addition(c):
    return c["t"] in ADDITION_TYPES


def is_shape(c):
    return c["t"] in SHAPE_TYPES


def normalize(text):
    """Normalization for the returned-unchanged comparison: normalize line endings + trim outer
    whitespace. Deliberately conservative — interior whitespace is preserved so real edits register."""
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def returned_unchanged(source, output):
    return normalize(source) == normalize(output)


def ground_task(task):
    """Return a list of grounding problems for one task. A trustworthy instrument requires that the
    planted defects really exist in the source and the protected/unaffected spans really appear.

    - every REMOVAL required check must FAIL on the source (defect present),
    - every ADDITION required check must FAIL on the source (replacement not already there),
    - every protected span + unaffected span must appear VERBATIM in the source,
    - no-change tasks carry no removal/addition required checks.
    """
    problems = []
    tid = task["task_id"]
    src = task.get("source_passage") or ""
    gt = task["evaluation_ground_truth"]
    valid_nc = gt.get("valid_no_change_case", False)
    revision = task["task_family"] in REVISION_FAMILIES

    for r in gt["required_changes"]:
        c = r["check"]
        if valid_nc:
            problems.append(f"{tid}: no-change task must not carry required change {r['id']}")
            continue
        if not src or not revision:
            continue
        if is_removal(c) and check(c, src):
            problems.append(f"{tid}: removal check {r['id']} PASSES on source (defect absent) — ungrounded")
        if is_addition(c) and check(c, src):
            problems.append(f"{tid}: addition check {r['id']} already PASSES on source (nothing to add) — ungrounded")

    for p in gt.get("protected_elements", []):
        if src and p["text"] not in src:
            problems.append(f"{tid}: protected element {p['id']} not present verbatim in source")
    for s in gt.get("unaffected_spans", []):
        if src and s["text"] not in src:
            problems.append(f"{tid}: unaffected span {s['id']} not present verbatim in source")
    # forbidden-change checks are framed so True == not-violated; the source (pre-edit) must satisfy them
    for f in gt.get("forbidden_changes", []):
        if src and not check(f["check"], src):
            problems.append(f"{tid}: forbidden-change guard {f['id']} already violated by source — mis-framed")
    return problems
