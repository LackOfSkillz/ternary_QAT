"""Dispatch 25 — provisional thresholds, freeze enforcement, diagnostic schema, decision.

The freeze/lock/decision tests assume the threshold files are committed (they are, before any
analysis artifact). They verify that thresholds are agent-proposed/provisional, that a lock
ties a decision to exact hashes, that any post-lock modification invalidates the decision, and
that the decision engine applies the frozen floors + ambiguous-middle rule.
"""
import copy
import json
import os

import pytest

yaml = pytest.importorskip("yaml")

HERE = os.path.dirname(__file__)
REPO = os.path.abspath(os.path.join(HERE, ".."))

from linewright.evaluation.thresholds import loader, freeze, decision
from linewright.evaluation.thresholds import RESEARCH_THRESHOLD, STARTER_THRESHOLD, LOCK_PATH


# ---- threshold files ----

def test_both_thresholds_parse_and_metadata_valid():
    for path in (RESEARCH_THRESHOLD, STARTER_THRESHOLD):
        doc = loader.load(path)
        assert loader.validate_metadata(doc) == []


def test_thresholds_are_agent_proposed_provisional_and_not_final():
    r = loader.load(RESEARCH_THRESHOLD)
    assert r["authorship"] == "agent_proposed" and r["authority"] == "delegated_by_gary"
    assert r["status"] == "provisional" and r["final_product_ship_threshold"] is False
    s = loader.load(STARTER_THRESHOLD)
    assert s["final_commercial_ship_gate"] is False and s["requires_future_gary_review"] is True


# ---- freeze / lock ----

def test_threshold_files_are_committed():
    for path in (RESEARCH_THRESHOLD, STARTER_THRESHOLD):
        assert freeze.is_tracked(path), f"{path} must be committed before analysis"
        assert freeze.is_clean(path), f"{path} must have no uncommitted modifications"


def test_lock_exists_and_verifies():
    assert os.path.exists(os.path.join(REPO, LOCK_PATH)), "threshold lock must exist"
    v = freeze.verify_lock()
    assert v["threshold_precommit_valid"] is True
    assert v["decision_status"] == "valid" and v["modified_after_lock"] is False


def test_lock_records_hashes_and_commit():
    lock = freeze.load_lock()
    assert lock["research_threshold_sha256"] == freeze.content_hash(RESEARCH_THRESHOLD)
    assert lock["starter_threshold_sha256"] == freeze.content_hash(STARTER_THRESHOLD)
    assert lock["git_commit"] and lock["locked_before_analysis"] is True


def test_tampered_hash_invalidates_decision():
    lock = copy.deepcopy(freeze.load_lock())
    lock["research_threshold_sha256"] = "0" * 64      # simulate a post-lock change
    v = freeze.verify_lock(lock)
    assert v["threshold_precommit_valid"] is False
    assert v["decision_status"] == "invalidated" and v["modified_after_lock"] is True


def test_require_locked_before_analysis_raises_on_tamper(monkeypatch):
    bad = copy.deepcopy(freeze.load_lock())
    bad["starter_threshold_sha256"] = "f" * 64
    monkeypatch.setattr(freeze, "load_lock", lambda path=LOCK_PATH: bad)
    with pytest.raises(RuntimeError):
        freeze.require_locked_before_analysis()


# ---- decision engine ----

def _evidence(**over):
    base = {"mechanical_pass_rate": 0.45, "core_prose_pass_rate": 0.55, "modules_with_usable": 8,
            "severe_slop_rate": 0.05, "token_cap_rate": 0.15, "bare_success_rate": 0.5,
            "packet_success_rate": 0.4}
    base.update(over.pop("base", {}))
    ev = {"base": base, "improvements": 0, "critical_regressions": 0, "curve": {}}
    ev.update(over)
    return ev


def test_decision_records_locked_hashes():
    d = decision.decide(_evidence())
    lock = freeze.load_lock()
    assert d["threshold_lock"]["research_sha256"] == lock["research_threshold_sha256"]
    assert d["threshold_lock"]["threshold_precommit_valid"] is True


def test_decision_test_stronger_base_when_core_floors_fail():
    d = decision.decide(_evidence(base={"mechanical_pass_rate": 0.20, "core_prose_pass_rate": 0.20}))
    assert d["branch"] == "test_stronger_base" and d["threshold_result"] == "fail"


def test_decision_revise_objective_on_critical_regression():
    d = decision.decide(_evidence(improvements=3, critical_regressions=1))
    assert d["branch"] == "revise_training_objective" and d["threshold_result"] == "fail"


def test_decision_ambiguous_middle_is_not_improvement():
    d = decision.decide(_evidence(improvements=0, critical_regressions=0))
    assert d["threshold_result"] == "ambiguous"
    assert "not counted as improvement" in d["ambiguous_middle_action"].lower() or \
           "confirmation" in d["ambiguous_middle_action"].lower()


def test_decision_continue_when_feasible_and_improving():
    d = decision.decide(_evidence(improvements=2, critical_regressions=0, curve={"monotone_worsening": False}))
    assert d["branch"] == "continue_scaled_dataset" and d["threshold_result"] == "pass"


# ---- diagnostic-finding schema ----

def test_diagnostic_finding_schema_separates_layers():
    s = yaml.safe_load(open(os.path.join(REPO, "benchmarks", "schemas", "diagnostic-finding-v1.yaml"),
                            encoding="utf-8"))
    f = s["fields"]
    assert "observation" in f and "causal_hypotheses" in f and "proposed_interventions" in f
    assert f["observation"]["observation_confidence"]["enum"][0] == "mechanical"
    assert any("never propagates" in r or "never inherits" in r or "propagate" in r for r in s["rules"])
