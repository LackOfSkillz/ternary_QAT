"""Dispatch 28A — validate the frozen-candidate task layer and emit reports/task-validation.{json,md}.

Confirms structure, JSON-schema conformance, machine-check completeness, instruction-position
design, benchmark-exclusion flags, grounding (via validators.checks), no duplicate IDs, and NO
overlap with the training datasets OR the Dispatch-28 Prompt-Effect benchmark. Outcome is one of
valid / valid_with_documented_warning / invalid_freeze_blocked. An invalid outcome blocks the freeze.
"""
import json
import os
import re
import sys
from collections import Counter

import jsonschema

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(BENCH, "..", ".."))
sys.path.insert(0, BENCH)
from validators import checks as C  # noqa: E402

REPORTS = os.path.join(BENCH, "reports")
FAMILIES = {"multi_constraint_focused_revision": 12, "protected_text_revision": 5,
            "no_change_judgment": 4, "canon_continuation": 3, "voice_preserving_revision": 3,
            "constraint_bound_scene": 2, "structured_protocol": 1}
REVISION = C.REVISION_FAMILIES
# corpora that a fresh benchmark task must NOT overlap
OVERLAP_ROOTS = [
    os.path.join(REPO, "datasets", "dataset-a"),
    os.path.join(REPO, "datasets", "dataset-a.2"),
    os.path.join(REPO, "datasets", "dataset-a.3"),
    os.path.join(REPO, "benchmarks", "linewright-prompt-effect-v1"),  # Dispatch-28 benchmark
]
TEXT_EXT = (".json", ".jsonl", ".yaml", ".yml", ".md", ".txt")
SHINGLE = 10


def _jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def _norm_words(text):
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split()


def _shingles(text, n=SHINGLE):
    w = _norm_words(text)
    return {" ".join(w[i:i + n]) for i in range(0, max(0, len(w) - n + 1))}


def _corpus_shingles():
    shs = set()
    for root in OVERLAP_ROOTS:
        for dp, _, fns in os.walk(root):
            for fn in fns:
                if fn.lower().endswith(TEXT_EXT):
                    try:
                        txt = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
                    except Exception:
                        continue
                    shs |= _shingles(txt)
    return shs


def main():
    errors, warnings = [], []
    tasks = _jsonl(os.path.join(BENCH, "task-manifest.jsonl"))
    schema = json.load(open(os.path.join(BENCH, "schemas", "task-manifest.schema.json"), encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)

    # 1. schema conformance
    for t in tasks:
        for e in validator.iter_errors(t):
            errors.append(f"{t.get('task_id','?')}: schema: {e.message} at {list(e.path)}")

    # 2. counts + families
    if len(tasks) != 30:
        errors.append(f"task count {len(tasks)} != 30")
    fams = Counter(t["task_family"] for t in tasks)
    if dict(fams) != FAMILIES:
        errors.append(f"family distribution {dict(fams)} != {FAMILIES}")
    ids = [t["task_id"] for t in tasks]
    if len(ids) != len(set(ids)):
        errors.append("duplicate task ids present")

    # 3. instruction positions 4/4/4 among focused-revision
    rev = [t for t in tasks if t["task_family"] == "multi_constraint_focused_revision"]
    pos = Counter(t["diagnostics"]["instruction_position"] for t in rev)
    if dict(pos) != {"early": 4, "middle": 4, "late": 4}:
        errors.append(f"focused-revision instruction positions {dict(pos)} != 4/4/4")
    ctypes = Counter(t["diagnostics"]["critical_instruction_type"] for t in rev)
    if any(v != 3 for v in ctypes.values()) or len(ctypes) != 4:
        warnings.append(f"focused-revision critical_instruction_type spread {dict(ctypes)} (expected 4 types x3)")

    # 4. per-task structural + flag + check-completeness rules
    for t in tasks:
        tid = t["task_id"]
        bp = t["benchmark_policy"]
        for flag in ("benchmark_only", "excluded_from_training", "excluded_from_teacher_examples",
                     "excluded_from_dataset_revision_examples", "excluded_from_preference_data",
                     "immutable_after_freeze"):
            if bp.get(flag) is not True:
                errors.append(f"{tid}: benchmark_policy.{flag} is not True")
        gt = t["evaluation_ground_truth"]
        mc = t["machine_checks"]
        # every required change has a machine check
        if len(mc["required_change_checks"]) != len(gt["required_changes"]):
            errors.append(f"{tid}: required_change_checks count != required_changes")
        # every protected element has a check
        if len(mc["protected_text_checks"]) != len(gt["protected_elements"]):
            errors.append(f"{tid}: protected_text_checks count != protected_elements")
        # returned-unchanged behaviour defined
        ruc = mc["returned_unchanged_check"]
        if ruc.get("comparison") != "exact_after_normalization":
            errors.append(f"{tid}: returned_unchanged_check not defined")
        # focused-revision: 3-5 required, >=1 protected, >=2 forbidden
        if t["task_family"] == "multi_constraint_focused_revision":
            n = len(gt["required_changes"])
            if not (3 <= n <= 5):
                errors.append(f"{tid}: focused-revision has {n} required changes (need 3-5)")
            if not gt["protected_elements"]:
                errors.append(f"{tid}: focused-revision needs >=1 protected element")
            if len(gt["forbidden_changes"]) < 2:
                errors.append(f"{tid}: focused-revision needs >=2 forbidden changes")
        # revision families define authorized + unaffected scope
        if t["task_family"] in REVISION:
            if not gt["authorized_spans"]:
                errors.append(f"{tid}: revision task missing authorized_spans")
            if not gt["unaffected_spans"]:
                errors.append(f"{tid}: revision task missing unaffected_spans")
        # no-change tasks: valid_no_change_case True and no required changes
        if t["task_family"] == "no_change_judgment":
            if not gt["valid_no_change_case"]:
                errors.append(f"{tid}: no-change task must set valid_no_change_case True")
            if gt["required_changes"]:
                errors.append(f"{tid}: no-change task must have no required changes")
        # leakage separation
        ci = json.dumps(t["compiler_inputs"])
        for banned in ("evaluation_ground_truth", "machine_checks", "required_change_checks",
                       "protected_text_checks"):
            if banned in ci:
                errors.append(f"{tid}: compiler_inputs leaks '{banned}'")

    # 5. comprehension probes <= 6
    probes = [t["task_id"] for t in tasks if t.get("comprehension_probe", {}).get("enabled")]
    if len(probes) > 6:
        errors.append(f"{len(probes)} comprehension probes (> 6)")

    # 6. grounding (defects real, protected/unaffected present)
    for t in tasks:
        errors += C.ground_task(t)

    # 7. per-task files exist and match manifest
    for t in tasks:
        fp = os.path.join(BENCH, "tasks", t["task_family"].replace("_", "-"), t["task_id"] + ".json")
        if not os.path.exists(fp):
            errors.append(f"{t['task_id']}: per-task file missing at {os.path.relpath(fp, BENCH)}")
        elif json.load(open(fp, encoding="utf-8"))["task_id"] != t["task_id"]:
            errors.append(f"{t['task_id']}: per-task file mismatch")

    # 8. dataset + Dispatch-28 overlap
    corpus = _corpus_shingles()
    overlaps = []
    for t in tasks:
        for field in ("source_passage",):
            txt = t.get(field) or ""
            if len(_norm_words(txt)) < SHINGLE:
                continue
            hit = _shingles(txt) & corpus
            if hit:
                overlaps.append({"task_id": t["task_id"], "field": field,
                                 "shared_span": sorted(hit)[0]})
    if overlaps:
        for o in overlaps:
            errors.append(f"{o['task_id']}: overlaps existing corpus on span '{o['shared_span']}'")

    outcome = "valid" if not errors else "invalid_freeze_blocked"
    if not errors and warnings:
        outcome = "valid_with_documented_warning"

    report = {
        "dispatch": "28A", "instrument": "linewright-prompt-execution-v1",
        "task_count": len(tasks), "family_distribution": dict(fams),
        "instruction_positions": dict(pos),
        "critical_instruction_types": dict(ctypes),
        "comprehension_probes": probes,
        "machine_checks_complete": all("required_change_checks" in t["machine_checks"] for t in tasks),
        "dataset_overlap": overlaps, "dataset_overlap_checked_roots": [os.path.relpath(r, REPO) for r in OVERLAP_ROOTS],
        "corpus_shingle_count": len(corpus),
        "errors": errors, "warnings": warnings, "outcome": outcome,
    }
    os.makedirs(REPORTS, exist_ok=True)
    with open(os.path.join(REPORTS, "task-validation.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    lines = [f"# Task validation — Prompt-Execution v1 (Dispatch 28A)", "",
             f"- Outcome: **{outcome}**", f"- Tasks: {len(tasks)} (expected 30)",
             f"- Families: {dict(fams)}", f"- Instruction positions: {dict(pos)}",
             f"- Critical-instruction types: {dict(ctypes)}",
             f"- Comprehension probes ({len(probes)}): {probes}",
             f"- Dataset/D28 overlap: {len(overlaps)} (roots: {[os.path.relpath(r, REPO) for r in OVERLAP_ROOTS]}; "
             f"{len(corpus)} corpus shingles)",
             f"- Errors: {len(errors)}", f"- Warnings: {len(warnings)}", ""]
    if errors:
        lines += ["## Errors"] + [f"- {e}" for e in errors] + [""]
    if warnings:
        lines += ["## Warnings"] + [f"- {w}" for w in warnings] + [""]
    with open(os.path.join(REPORTS, "task-validation.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print(json.dumps({"outcome": outcome, "errors": len(errors), "warnings": len(warnings),
                      "overlaps": len(overlaps), "probes": len(probes)}, indent=1))
    return outcome


if __name__ == "__main__":
    sys.exit(0 if main() != "invalid_freeze_blocked" else 1)
