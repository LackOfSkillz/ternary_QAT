"""Dispatch 27B/C — validate LoRA training, checkpoint curve, focused-revision audit, blind
review, and advancement-decision invariants."""
import hashlib
import json
import os

import pytest
import yaml

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RUN = os.path.join(REPO, "benchmarks", "runs", "qwen3-lora-checkpoint-curve-v1")
REPORTS = os.path.join(REPO, "training", "reports")
BASE_REV = "b968826d9c46dd6066d109eabc6255188de91218"
RESEARCH_SHA = "2be4fddb1aed87c6500dac2a5cdf11e6209b80d2a6d32fa35aa4d63bef131712"


def _y(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _j(path):
    return json.load(open(path, encoding="utf-8"))


# ---- training integrity ----

def test_training_integrity_valid():
    t = _y(os.path.join(REPORTS, "dispatch-27-lora-training-integrity.yaml"))["lora_training_integrity"]
    assert t["integrity_outcome"] == "valid"
    assert t["base_revision"] == BASE_REV and t["base_revision_correct"] is True
    assert t["dataset_hash_matches_frozen"] is True
    assert t["train_records"] == 42 and t["validation_records"] == 6
    assert t["trainable_parameter_count"] == 43646976
    assert t["thinking"] == "disabled"
    assert t["loss_finite"] is True and t["gradient_norms_finite"] is True and t["no_nan_or_inf"] is True
    assert t["qat_launched"] is False
    assert len(t["checkpoints"]) == 7
    for c in t["checkpoints"]:
        assert c["adapter_sha256"] and c["grad_norm"] is not None


def test_dataset_a3_train_hash_unchanged():
    recs = [json.loads(l) for l in open(os.path.join(REPO, "datasets", "dataset-a.3", "records",
                                                     "a3-pilot.jsonl"), encoding="utf-8") if l.strip()]
    train = [r for r in recs if r["pool"] == "training"]
    h = hashlib.sha256("\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in train).encode()).hexdigest()
    fz = _j(os.path.join(REPORTS, "dataset-a3-audit-v1", "freeze.json"))
    assert h == fz["train_sha256"]


# ---- evaluation + curve ----

def test_evaluation_integrity_9_roles_14_items():
    e = _j(os.path.join(RUN, "evaluation-integrity.json"))
    assert e["roles_present"] == 9 and e["expected_roles"] == 9
    assert e["total_results"] == 126 and e["all_roles_14_items"] is True
    assert all(v == 0.0 for v in e["reasoning_trace_findings"].values())


def test_curve_base_and_all_checkpoints_present_zero_regressions():
    s = _j(os.path.join(RUN, "checkpoint-curve-summary.json"))
    assert "qwen3_8b_base" in s["curve"]
    ck = [r for r in s["curve"] if r != "qwen3_8b_base"]
    assert len(ck) == 8  # 7 steps + final
    assert all(v == 0 for v in s["critical_regressions_vs_base"].values())
    # neutral: every checkpoint matches base mechanical + core-prose
    b = s["curve"]["qwen3_8b_base"]
    for r in ck:
        assert s["curve"][r]["mechanical_pass_rate"] == b["mechanical_pass_rate"]
        assert s["curve"][r]["core_prose_pass_rate"] == b["core_prose_pass_rate"]


# ---- focused-revision audit ----

def test_focused_revision_audit_neutral():
    a = _y(os.path.join(REPORTS, "dispatch-27-focused-revision-audit.yaml"))["focused_revision_audit"]
    base = a["base"]["unchanged_return_rate"]
    assert base == 0.667
    for r, s in a["per_checkpoint"].items():
        assert s["unchanged_return_rate"] == base  # no checkpoint reduces it
        assert s["protected_preserved_rate"] == 1.0
    assert a["converts_unchanged_to_valid"] is False


# ---- provisional best (pre-blind) ----

def test_provisional_best_selected_before_blind_and_not_final():
    p = _y(os.path.join(REPORTS, "dispatch-27-provisional-best-checkpoint.yaml"))["provisional_best"]
    assert p["selected_before_blind_review"] is True
    assert p["checkpoint"] is not None
    assert p["checkpoint"] not in ("lora_final",)  # final not privileged
    assert p["critical_regressions"] == 0
    assert p["checkpoint"] in p["eligible_alternatives"]


# ---- blind review + floor ----

def test_blind_review_floor_and_calibration():
    s = _j(os.path.join(RUN, "lora-blind-review-summary.json"))
    assert s["reviewers"]["human_review_submitted"] is False
    assert s["reviewers"]["independently_human_confirmed"] is False  # honest waiver
    assert s["advancement_floor"]["min_prose_gain"] == 0.25  # unchanged
    assert s["scores_locked_before_unblinding"] is True
    for rv in ("A", "B"):
        c = s["reviewer_calibration"][rv]
        assert c["broken_caught"] == c["broken_total"]
    # neutral result recorded honestly
    assert s["effect_floor_passed"] is False


# ---- decision + QAT gate ----

def test_decision_branch_and_qat_denied():
    d = _y(os.path.join(REPORTS, "dispatch-27-lora-decision.yaml"))["lora_decision"]
    assert d["branch"] in ("select_LoRA_checkpoint", "retain_Qwen_base", "revise_Dataset_A3",
                           "revise_LoRA_recipe", "run_one_bounded_confirmation", "stop_Qwen_tuning_direction")
    assert d["lora_advances"] is False
    assert d["qat_authorized"] is False and d["qat_started"] is False
    # QAT spec must NOT exist when not authorized
    assert not os.path.exists(os.path.join(REPO, "training", "specs", "qwen3-linewright-qat-v0.yaml"))


def test_no_qat_spec_since_not_authorized():
    assert not os.path.exists(os.path.join(REPO, "training", "specs", "qwen3-linewright-qat-v0.md"))


# ---- repository invariants ----

def test_frozen_artifacts_unchanged():
    r = hashlib.sha256(open(os.path.join(REPO, "benchmarks", "thresholds", "research-continuation-v0.yaml"), "rb").read()).hexdigest()
    assert r == RESEARCH_SHA
    fb = hashlib.sha256(open(os.path.join(REPO, "benchmarks", "manifests", "fast-battery-v1.yaml"), "rb").read()).hexdigest()
    assert fb == "e906213df98c5b58d58a67f901b2de50f829e389fcf80e6915b231a6bdf8ab20"
