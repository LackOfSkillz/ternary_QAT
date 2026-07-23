"""Dispatch 28 — validate Prompt-Effect v1 task/prompt/generation/scoring/decision invariants."""
import hashlib
import json
import os

import pytest
import yaml

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BENCH = os.path.join(REPO, "benchmarks", "linewright-prompt-effect-v1")
RUN = os.path.join(REPO, "benchmarks", "runs", "linewright-prompt-effect-v1")
RESEARCH_SHA = "2be4fddb1aed87c6500dac2a5cdf11e6209b80d2a6d32fa35aa4d63bef131712"


def _jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def _j(p):
    return json.load(open(p, encoding="utf-8"))


# ---- task integrity ----

def test_thirty_tasks_family_distribution_and_flags():
    tasks = _jsonl(os.path.join(BENCH, "task-manifest.jsonl"))
    assert len(tasks) == 30
    from collections import Counter
    fams = Counter(t["task_family"] for t in tasks)
    assert dict(fams) == {"multi_constraint_focused_revision": 12, "protected_text_revision": 5,
                          "no_change_judgment": 4, "canon_continuation": 3, "voice_preserving_revision": 3,
                          "constraint_bound_scene": 2, "structured_protocol": 1}
    for t in tasks:
        assert t["benchmark_policy"]["benchmark_only"] is True
        assert t["benchmark_policy"]["excluded_from_training"] is True
        assert t["ground_truth"]["required_changes"]
        for rc in t["ground_truth"]["required_changes"]:
            assert "check" in rc and "t" in rc["check"]


def test_instruction_positions_4_4_4():
    tasks = _jsonl(os.path.join(BENCH, "task-manifest.jsonl"))
    from collections import Counter
    rev = [t for t in tasks if t["task_family"] == "multi_constraint_focused_revision"]
    pos = Counter(t["diagnostics"]["instruction_position"] for t in rev)
    assert dict(pos) == {"early": 4, "middle": 4, "late": 4}


def test_task_freeze_training_exclusion_and_machine_checks():
    f = _j(os.path.join(BENCH, "freeze", "task-freeze.json"))
    assert f["task_count"] == 30
    assert f["training_exclusion_confirmed"] is True
    assert f["machine_checks_complete"] is True
    assert f["instruction_positions_frozen"] is True
    assert f["frozen_before_prompt_rendering"] is True


def test_sources_self_consistent():
    import sys
    if BENCH not in sys.path:
        sys.path.insert(0, BENCH)
    from score_prompt_effect import validate_sources
    assert validate_sources() == []


# ---- prompt integrity ----

def test_prompt_counts_and_information_equivalence():
    plan = _j(os.path.join(BENCH, "prompt-plan.json"))
    from collections import Counter
    c = Counter(p["arm"] for p in plan["prompts"])
    assert c["P0-Realistic"] == 30 and c["P0-Maximal"] == 30 and c["P1-Contract"] == 30 and c["P3-Ideal"] == 10
    fz = _j(os.path.join(BENCH, "freeze", "prompt-freeze.json"))
    assert fz["p0max_p1_information_equivalence"] is True
    assert fz["frozen_before_generation"] is True


# ---- generation + scoring ----

def test_generation_integrity_100_no_leak():
    if not os.path.exists(os.path.join(RUN, "mechanical-results.json")):
        pytest.skip("results not generated")
    m = _j(os.path.join(RUN, "mechanical-results.json"))
    g = m["generation_integrity"]
    assert g["actual_outputs"] == 100
    assert g["reasoning_trace_count"] == 0 and g["token_cap_count"] == 0


def test_mechanical_reports_returned_unchanged_and_headline():
    if not os.path.exists(os.path.join(RUN, "mechanical-results.json")):
        pytest.skip("results not generated")
    m = _j(os.path.join(RUN, "mechanical-results.json"))
    assert "returned_unchanged" in m["focused_revision_by_arm"]["P1-Contract"]
    assert "p1_minus_p0_realistic" in m["headline_effects"]
    assert "anti_result_by_arm" in m


# ---- decision + gates ----

def test_decision_branch_and_a3_paused():
    p = os.path.join(REPO, "training", "reports", "dispatch-28-prompt-effect-decision.yaml")
    if not os.path.exists(p):
        pytest.skip("decision not generated")
    d = yaml.safe_load(open(p, encoding="utf-8"))["prompt_effect_decision"]
    assert d["primary_branch"] in ("prioritize_contract_compiler", "prioritize_requirement_elicitation",
                                   "prioritize_retrieval_and_canon", "prioritize_voice_packet",
                                   "improve_compiler_quality", "shift_training_to_packet_executor",
                                   "continue_prompt_and_training_tracks", "model_capability_is_primary_bottleneck",
                                   "run_full_100_task_multimodel_benchmark", "revise_pilot_instrument")
    assert d["dataset_a3_expansion_authorized"] is False   # A.3 gate: paused
    assert d["final_commercial_ship_certification"] is False


# ---- repository invariants ----

def test_frozen_thresholds_and_datasets_unchanged():
    r = hashlib.sha256(open(os.path.join(REPO, "benchmarks", "thresholds", "research-continuation-v0.yaml"), "rb").read()).hexdigest()
    assert r == RESEARCH_SHA
    fb = hashlib.sha256(open(os.path.join(REPO, "benchmarks", "manifests", "fast-battery-v1.yaml"), "rb").read()).hexdigest()
    assert fb == "e906213df98c5b58d58a67f901b2de50f829e389fcf80e6915b231a6bdf8ab20"
    for d in ("dataset-a", "dataset-a.2", "dataset-a.3"):
        assert os.path.isdir(os.path.join(REPO, "datasets", d))
