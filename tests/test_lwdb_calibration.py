"""Dispatch 23 — instrument calibration (Workstream A) invariants.

The grader-calibration set dogfoods against the Dispatch-21 gates; reviewer classification
works; mechanical replay is identical; failed calibration quarantines findings.
"""
import os

import pytest

from linewright.evaluation.calibration import records as rec_mod
from linewright.evaluation.calibration import reviewer as rev_mod
from linewright.evaluation.calibration import replay as replay_mod
from linewright.evaluation.repetition import analyze_repetition

HERE = os.path.dirname(__file__)
REPO = os.path.abspath(os.path.join(HERE, ".."))
GRADER = os.path.join(REPO, "benchmarks", "calibration", "grader-calibration-set-v1.jsonl")


@pytest.fixture(scope="module")
def grader():
    return {r["calibration_id"]: r for r in rec_mod.load_calibration_set(GRADER)}


def test_full_calibration_set_dogfoods_clean():
    problems, counts = rec_mod.verify_calibration_set(GRADER)
    assert problems == [], f"calibration set does not dogfood: {problems}"
    assert counts["known_good"] >= 3 and counts["known_broken"] >= 8


def test_known_good_structured_accepted(grader):
    assert rec_mod.verify_record_against_gates(grader["cal-good-structured"]) == []


def test_schema_broken_rejected(grader):
    assert grader["cal-broken-schema"]["known_expected_result"] == "reject"
    assert rec_mod.verify_record_against_gates(grader["cal-broken-schema"]) == []


def test_canon_broken_rejected(grader):
    assert rec_mod.verify_record_against_gates(grader["cal-broken-canon"]) == []


def test_repetition_loop_detected(grader):
    r = grader["cal-broken-exact-rep"]
    assert analyze_repetition(r["candidate_output"]).valid is False
    assert rec_mod.verify_record_against_gates(r) == []


def test_out_of_scope_rewrite_detected(grader):
    assert rec_mod.verify_record_against_gates(grader["cal-broken-out-of-scope"]) == []


def test_correct_no_change_accepted(grader):
    assert rec_mod.verify_record_against_gates(grader["cal-good-nochange"]) == []


def test_incorrect_no_change_rejected(grader):
    assert rec_mod.verify_record_against_gates(grader["cal-broken-nochange"]) == []


def test_reviewer_enforced_records_not_mechanically_asserted(grader):
    # harmful-guidance placeholder is reviewer-enforced; the mechanical layer does not reject it
    assert rec_mod.verify_record_against_gates(grader["cal-broken-harmful"]) == []
    assert grader["cal-broken-harmful"]["enforced_by"] == "reviewer"


# ---- reviewer classification ----

def _scored(good_ok, broken_ok, fatal_caught=True):
    items = []
    for i in range(5):
        items.append({"calibration_id": f"g{i}", "known_expected": "accept",
                      "reviewer_decision": "accept" if i < good_ok else "reject"})
    for i in range(5):
        caught = i < broken_ok
        items.append({"calibration_id": f"b{i}", "known_expected": "reject",
                      "reviewer_decision": "reject" if caught else "accept",
                      "fatal_flaw_expected": True, "fatal_flaw_caught": caught and fatal_caught})
    return items


def test_reviewer_classified_calibrated():
    r = rev_mod.classify("rev1", "run1", _scored(5, 5))
    assert r["classification"] == "calibrated"
    assert r["threshold_profile_version"].startswith("provisional")


def test_reviewer_classified_unreliable_when_missing_fatal():
    r = rev_mod.classify("rev2", "run1", _scored(5, 2))  # missed 3 broken -> false accepts
    assert r["classification"] == "unreliable_for_run"
    assert "rev2" not in rev_mod.usable_reviewers([r])


def test_reviewer_classifications_are_provisional_unvalidated():
    assert rev_mod.PROVISIONAL["status"] == "provisional_unvalidated"


# ---- mechanical replay ----

def test_mechanical_replay_identical():
    rep = replay_mod.replay("repetition", "v1", lambda t: analyze_repetition(t),
                            "The door creaks. " * 5)
    assert rep["identical"] is True
    assert rep["first_result_hash"] == rep["replay_result_hash"]
    assert rep["run_validity_consequence"] == "none"


def test_failed_calibration_quarantines_findings():
    # a replay mismatch OR no calibrated reviewer => instrument invalid, findings quarantined
    good = rev_mod.classify("r", "run", _scored(5, 5))
    bad_replay = {"identical": False, "run_validity_consequence": "invalidate_run"}
    iv = replay_mod.instrument_valid([bad_replay], [], [good])
    assert iv["instrument_valid"] is False
    assert iv["overall"] == "insufficient_evidence"
    assert iv["findings_status"] == "quarantined"
    # all-good path is valid
    ok_replay = {"identical": True, "run_validity_consequence": "none"}
    iv2 = replay_mod.instrument_valid([ok_replay], [], [good])
    assert iv2["instrument_valid"] is True and iv2["findings_status"] == "trusted"
