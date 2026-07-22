"""Dispatch 24 continuation — validate the completed live dual-GX10 run artifacts.

Asserts the run is instrument-valid, all 40 jobs are accounted for and integrity-clean,
mechanical replay was identical, reviewer packets leak no identity, and no winner is claimed.
"""
import json
import os

import pytest

HERE = os.path.dirname(__file__)
REPO = os.path.abspath(os.path.join(HERE, ".."))
RUN = os.path.join(REPO, "benchmarks", "runs", "lwdb-fast-v1-20260722")


@pytest.fixture(scope="module")
def summary():
    return json.load(open(os.path.join(RUN, "completed-run-summary.json"), encoding="utf-8"))


@pytest.fixture(scope="module")
def rows():
    return json.load(open(os.path.join(RUN, "item-level-results.json"), encoding="utf-8"))


def test_all_40_jobs_accounted_and_integrity_clean(summary):
    c = summary["completion"]
    assert c["expected"] == 40 and c["got"] == 40 and c["missing"] == 0
    assert c["job_counts"].get("completed") == 40
    assert summary["integrity_problems"] == []


def test_mechanical_replay_identical_and_instrument_valid(summary):
    inst = summary["instrument"]
    assert inst["mechanical_replay_identical"] is True
    assert inst["instrument_valid"] is True
    assert inst["overall"] == "ok"


def test_each_role_ran_and_scored(summary):
    for role in ("target_base", "new_candidate"):
        assert summary["mechanical"][role]["outputs"] == 20
    assert summary["slop"]["per_output_reports"] == 40
    assert set(summary["slop"]["corpus_summaries"]) == {"target_base", "new_candidate"}
    assert summary["slop"]["thresholds_status"] == "unvalidated"
    assert summary["slop"]["semantic_detector_status"] == "interface_only"


def test_review_packets_no_identity_leak_and_calibration_seeded(summary):
    r = summary["review"]
    assert r["identity_leaks"] == []
    assert r["absolute_units"] == 44          # 40 outputs + 4 hidden calibration
    assert r["pairwise_packets"] == 20
    assert r["calibration_items_seeded"] == 4


def test_item_level_results_complete(rows):
    assert len(rows) == 40
    for r in rows:
        assert r["output_hash"] and isinstance(r["mechanical_pass"], bool)
        assert r["slop_severity"] in ("none", "low", "moderate", "high", "severe", "inconclusive")
    assert {r["model_role"] for r in rows} == {"target_base", "new_candidate"}


def test_no_winner_claimed_and_deferred():
    rep = open(os.path.join(RUN, "completed-run-report.md"), encoding="utf-8").read()
    assert "deferred to Dispatch 25" in rep
    assert "No winner" in rep or "no winner" in rep
    assert "instrument-valid" in rep.lower()


def test_advancement_deferred_flag(summary):
    assert summary["advancement_decision_deferred_to_dispatch_25"] is True


def test_provisioning_recorded_with_verified_adapter():
    prov = json.load(open(os.path.join(RUN, "provisioning.json"), encoding="utf-8"))["candidate_provisioning"]
    assert prov["adapter_hash_verified"] == "MATCH"
    assert prov["health_check"]["gx10-9141_target_base"] == "READY"
    assert prov["health_check"]["gx10-5611_new_candidate"] == "READY"
