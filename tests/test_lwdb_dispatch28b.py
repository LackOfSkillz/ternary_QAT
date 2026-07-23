"""Dispatch 28B — validate generation, scoring, review, and decision invariants for the
Prompt-Execution v1 run. Reads committed summaries/reports (raw outputs are gitignored)."""
import hashlib
import json
import os

import pytest
import yaml

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BENCH = os.path.join(REPO, "benchmarks", "linewright-prompt-execution-v1")
RUN = os.path.join(REPO, "benchmarks", "runs", "linewright-prompt-execution-v1")
FROZEN = {
    "task_manifest": "9a1bbe3cbd58ac79a5b25084fb6d5eea26dd630134827283c297fde3a0c945d2",
    "prompt_manifest": "13fbbeabad108b0cf33601db086bf0014d2c5961ad512b736f719d10c0ee7316",
}


def _j(p):
    return json.load(open(p, encoding="utf-8"))


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ---- frozen instrument unchanged (28A) ----

def test_frozen_instrument_hashes_unchanged():
    assert _sha(os.path.join(BENCH, "task-manifest.jsonl")) == FROZEN["task_manifest"]
    assert _sha(os.path.join(BENCH, "prompt-arm-manifest.json")) == FROZEN["prompt_manifest"]
    eq = _j(os.path.join(BENCH, "reports", "information-equivalence.json"))
    assert eq["tasks_passed"] == 30 and eq["information_equivalence"] is True


# ---- generation integrity ----

def test_generation_integrity_valid():
    g = _j(os.path.join(RUN, "generation-integrity.json"))
    assert g["outcome"] in ("valid", "valid_with_documented_exact_retries")
    assert g["actual_outputs"] == 100
    assert g["missing_outputs"] == 0 and g["duplicate_outputs"] == 0
    assert g["prompt_hash_mismatches"] == 0 and g["model_revision_mismatches"] == 0
    assert g["generation_setting_mismatches"] == 0
    assert g["technical_failures"] <= 5
    assert g["comprehension_outputs"] == 6


def test_generation_plan_no_p3_compiled():
    plan = _j(os.path.join(RUN, "generation-plan.json"))
    assert plan["actual_records"] == 100 and plan["p3_compiled_records"] == 0
    assert plan["missing_task_arm_pairs"] == 0 and plan["duplicate_task_arm_pairs"] == 0
    assert plan["comprehension_count"] == 6


def test_environment_revision_and_thinking():
    e = _j(os.path.join(RUN, "environment-manifest.json"))
    assert e["model_revision"] == "b968826d9c46dd6066d109eabc6255188de91218"
    assert e["thinking"] == "disabled" and e["seed"] == 20260723


# ---- mechanical scoring ----

def test_mechanical_metrics_present_all_arms():
    m = _j(os.path.join(RUN, "mechanical-results.json"))
    for arm in ("P0-Realistic", "P0-Maximal", "P1-Contract", "P3-Ideal"):
        b = m["mechanical_by_arm"][arm]
        for k in ("clean_execution", "all_required_completed", "invalid_unchanged",
                  "protected_text_accuracy", "unauthorized_edit_rate", "no_change_accuracy"):
            assert k in b
    assert "p1_minus_p0_maximal" in m["effects"] and "p3ideal_minus_p1" in m["effects"]
    for k in ("structure_success", "practical_product_success", "ideal_packet_signal"):
        assert "PASS" in m["effect_floors"][k]


def test_returned_unchanged_is_separate_metric():
    m = _j(os.path.join(RUN, "mechanical-results.json"))
    # invalid unchanged tracked for revision arms; no-change accuracy tracked separately
    assert m["mechanical_by_arm"]["P0-Maximal"]["invalid_unchanged"]["rate"] is not None
    assert m["mechanical_by_arm"]["P0-Maximal"]["no_change_accuracy"] is not None


def test_frozen_check_evaluator_used():
    import sys
    if BENCH not in sys.path:
        sys.path.insert(0, BENCH)
    from validators import checks as C
    assert C.check({"t": "absent", "v": "x"}, "y") is True
    assert C.returned_unchanged("a\r\n", "a") is True


def test_comprehension_execution_reported():
    c = _j(os.path.join(RUN, "comprehension-execution-analysis.json"))
    assert set(c["grid"]) == {"pass_pass", "fail_fail", "pass_fail", "fail_pass"}
    assert c["probes"] == 6


# ---- blind review ----

def test_blind_review_calibration_and_lock():
    s = _j(os.path.join(RUN, "soft-review-summary.json"))
    assert s["scores_locked_before_unblinding"] is True
    assert s["calibration_controls_excluded_from_arm_means"] is True
    for rv in ("A", "B"):
        c = s["reviewer_calibration"][rv]
        assert c["broken_caught"] == c["broken_total"]  # both caught all broken controls
    assert s["reviewers"]["human_review_submitted"] is False
    assert s["reviewers"]["evidence_status"] == "model_review_only"
    for arm in ("P0-Realistic", "P0-Maximal", "P1-Contract", "P3-Ideal"):
        assert "prose_quality" in s["per_arm_means"][arm]


def test_private_unblinding_not_committed():
    # blind-review integrity: the identity key must never be tracked in git
    import subprocess
    tracked = subprocess.run(["git", "ls-files", "benchmarks/runs/linewright-prompt-execution-v1/private-unblinding"],
                             cwd=REPO, capture_output=True, text=True).stdout.strip()
    assert tracked == ""


# ---- decision ----

def test_decision_branch_thesis_and_gates():
    p = os.path.join(REPO, "training", "reports", "dispatch-28b-prompt-execution-decision.yaml")
    d = yaml.safe_load(open(p, encoding="utf-8"))["prompt_execution_decision"]
    assert d["primary_branch"] in (
        "prioritize_contract_compiler", "prioritize_requirement_elicitation",
        "prioritize_richer_packet_context", "shift_training_to_packet_executor",
        "continue_prompt_and_training_tracks", "model_capability_is_primary_bottleneck",
        "revise_prompt_instrument", "run_full_100_task_multimodel_benchmark",
        "hold_for_real_product_compiler")
    assert d["product_thesis"] in ("supported", "partially_supported", "not_supported", "instrument_inconclusive")
    assert d["dataset_a3_generation_authorized"] is False
    assert d["final_commercial_ship_certification"] is False
    assert d["future_training_target"] in ("packet_executor", "generic_prose_stylist", "hybrid", "no_custom_training_yet")


# ---- repository invariants ----

def test_dispatch27_28_28a_and_datasets_unchanged():
    # Dispatch-28 decision + Dispatch-28A frozen task-freeze remain present and untouched
    assert os.path.exists(os.path.join(REPO, "training", "reports", "dispatch-28-prompt-effect-decision.yaml"))
    tf = _j(os.path.join(BENCH, "freeze", "task-freeze.json"))
    assert tf["task_manifest_sha256"] == FROZEN["task_manifest"]
    for dset in ("dataset-a", "dataset-a.2", "dataset-a.3"):
        assert os.path.isdir(os.path.join(REPO, "datasets", dset))
    r = _sha(os.path.join(REPO, "benchmarks", "thresholds", "research-continuation-v0.yaml"))
    assert r == "2be4fddb1aed87c6500dac2a5cdf11e6209b80d2a6d32fa35aa4d63bef131712"
