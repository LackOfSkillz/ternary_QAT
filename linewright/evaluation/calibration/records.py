"""Hidden grader-calibration records (Dispatch 23, Workstream A1).

A small controlled set of known-good and known-broken outputs used to prove the instrument
recognizes obvious success and failure. Records are ``benchmark_only`` and
``excluded_from_training`` and use distributable text only (never author manuscripts). Each
record declares its known expected result; ``verify_record_against_gates`` DOGFOODS it — the
Dispatch-21 mechanical gates must actually produce that result, or the instrument is broken.
"""
import json
import os

from linewright.evaluation.gates import evaluate_response, gate_summary, GateResult
from linewright.evaluation.slop.report import build_slop_report
from linewright.evaluation import contracts as contract_mod

CALIBRATION_KINDS = [
    "mechanically_perfect_output", "schema_invalid_output", "canon_violating_output",
    "severe_exact_repetition", "severe_semantic_repetition",
    "polished_but_out_of_scope_rewrite", "correct_no_change_response",
    "incorrect_no_change_response", "attractive_prose_violating_hard_constraint",
    "unauthorized_negative_space_damage", "ordinary_dark_fiction_should_not_refuse",
    "harmful_operational_guidance_disguised_as_fiction",
]
REQUIRED_FIELDS = ("calibration_id", "calibration_kind", "source_item_shape",
                   "candidate_output", "known_expected_result", "benchmark_only",
                   "excluded_from_training")


def load_calibration_set(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def validate_record(rec):
    problems = []
    for f in REQUIRED_FIELDS:
        if f not in rec:
            problems.append(f"missing field {f}")
    if rec.get("calibration_kind") not in CALIBRATION_KINDS:
        problems.append(f"unknown calibration_kind {rec.get('calibration_kind')!r}")
    if rec.get("benchmark_only") is not True:
        problems.append("benchmark_only must be true")
    if rec.get("excluded_from_training") is not True:
        problems.append("excluded_from_training must be true")
    ker = rec.get("known_expected_result")
    if ker not in ("accept", "reject"):
        problems.append("known_expected_result must be 'accept' or 'reject'")
    return problems


def _mechanical(rec):
    """Run the Dispatch-21 gates over the candidate output using the record's item shape."""
    shape = rec["source_item_shape"]
    oc = shape.get("output_contract", {"type": "prose", "schema_id": "prose-v1"})
    # resolve a bare {schema_id: ...} against the dataset-a.2 registry
    if "schema_id" in oc and "type" not in oc:
        oc = contract_mod.resolve(oc)
    spec = {
        "output_contract": oc,
        "source": shape.get("source", ""),
        "gold": shape.get("gold", ""),
        "validation_expectations": shape.get("validation_expectations", {}),
        "train_targets": shape.get("train_targets", []),
    }
    if spec["validation_expectations"].get("changed") is False:
        spec["output_contract"] = dict(spec["output_contract"], expects_no_change=True)
    gm = evaluate_response(rec["candidate_output"], spec)
    return gm, gate_summary(gm)


def verify_record_against_gates(rec):
    """Return problems if the instrument does NOT recognize this record as declared.

    known_expected_result 'reject' => a mechanical fatal flaw OR a severe slop verdict must
    appear; 'accept' => mechanical gates pass and no severe slop.
    """
    problems = []
    gm, summ = _mechanical(rec)
    slop = build_slop_report(rec["candidate_output"], output_id=rec["calibration_id"],
                             detector_manifest_id="calibration",
                             source=rec["source_item_shape"].get("source"))
    severe_slop = slop["summary"]["severity"] in ("severe",)
    mech_pass = summ["mechanical_pass"]
    got_labels = set()
    for v in gm.values():
        if isinstance(v, GateResult):
            got_labels |= set(v.failure_labels)

    # Reviewer-enforced categories (ordinary dark fiction that must NOT be refused; harmful
    # operational guidance disguised as fiction that must NOT be answered) are decided by the
    # reviewer/refusal layer, not the mechanical gates — coherent harmful prose passes the
    # mechanical gates by design. We validate their shape but never assert a mechanical verdict.
    if rec.get("enforced_by", "mechanical") == "reviewer":
        for lab in rec.get("expected_fatal_flaws", []) or []:
            if lab not in got_labels:
                problems.append(f"{rec['calibration_id']}: declared mechanical fatal flaw "
                                f"{lab!r} not detected")
        return problems

    expect = rec["known_expected_result"]
    is_rejected = (not mech_pass) or severe_slop
    if expect == "reject" and not is_rejected:
        problems.append(f"{rec['calibration_id']}: expected REJECT but instrument accepted "
                        f"(mech_pass={mech_pass}, severe_slop={severe_slop})")
    if expect == "accept" and is_rejected:
        problems.append(f"{rec['calibration_id']}: expected ACCEPT but instrument rejected "
                        f"(labels={sorted(got_labels)}, severe_slop={severe_slop})")
    for lab in rec.get("expected_fatal_flaws", []) or []:
        if lab not in got_labels:
            problems.append(f"{rec['calibration_id']}: declared fatal flaw {lab!r} not detected")
    return problems


def verify_calibration_set(path):
    """Validate + dogfood the whole set. Returns (problems, counts)."""
    recs = load_calibration_set(path)
    problems, good, broken = [], 0, 0
    ids = set()
    for rec in recs:
        rid = rec.get("calibration_id", "?")
        if rid in ids:
            problems.append(f"duplicate calibration_id {rid}")
        ids.add(rid)
        problems += [f"[{rid}] {p}" for p in validate_record(rec)]
        problems += verify_record_against_gates(rec)
        if rec.get("known_expected_result") == "accept":
            good += 1
        elif rec.get("known_expected_result") == "reject":
            broken += 1
    return problems, {"total": len(recs), "known_good": good, "known_broken": broken}
