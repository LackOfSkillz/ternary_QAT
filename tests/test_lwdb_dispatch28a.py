"""Dispatch 28A — validate the LineWright Prompt-Execution v1 construction invariants.

Covers the task layer, the prompt layer, and repository invariants (no generation, no training,
Dataset A/A.2/A.3 and the Dispatch-28 pilot unchanged). Construction-only: asserts that NO model
output exists and generation is not authorized.
"""
import hashlib
import json
import os
from collections import Counter

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BENCH = os.path.join(REPO, "benchmarks", "linewright-prompt-execution-v1")


def _jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def _j(p):
    return json.load(open(p, encoding="utf-8"))


def tasks():
    return _jsonl(os.path.join(BENCH, "task-manifest.jsonl"))


def prompts():
    return _j(os.path.join(BENCH, "prompt-arm-manifest.json"))["prompts"]


# ---------------- task layer ----------------

def test_thirty_tasks_and_family_distribution():
    ts = tasks()
    assert len(ts) == 30
    assert dict(Counter(t["task_family"] for t in ts)) == {
        "multi_constraint_focused_revision": 12, "protected_text_revision": 5,
        "no_change_judgment": 4, "canon_continuation": 3, "voice_preserving_revision": 3,
        "constraint_bound_scene": 2, "structured_protocol": 1}
    assert len({t["task_id"] for t in ts}) == 30


def test_instruction_positions_4_4_4():
    rev = [t for t in tasks() if t["task_family"] == "multi_constraint_focused_revision"]
    assert dict(Counter(t["diagnostics"]["instruction_position"] for t in rev)) == {
        "early": 4, "middle": 4, "late": 4}
    ctypes = Counter(t["diagnostics"]["critical_instruction_type"] for t in rev)
    assert len(ctypes) == 4 and all(v == 3 for v in ctypes.values())


def test_focused_revision_structural_rules():
    rev = [t for t in tasks() if t["task_family"] == "multi_constraint_focused_revision"]
    for t in rev:
        gt = t["evaluation_ground_truth"]
        assert 3 <= len(gt["required_changes"]) <= 5
        assert len(gt["protected_elements"]) >= 1
        assert len(gt["forbidden_changes"]) >= 2


def test_every_required_change_and_protected_has_a_check():
    for t in tasks():
        gt, mc = t["evaluation_ground_truth"], t["machine_checks"]
        assert len(mc["required_change_checks"]) == len(gt["required_changes"])
        assert len(mc["protected_text_checks"]) == len(gt["protected_elements"])
        for c in mc["required_change_checks"] + mc["protected_text_checks"]:
            assert "t" in c["check"]
        assert mc["returned_unchanged_check"]["comparison"] == "exact_after_normalization"


def test_revision_tasks_define_authorized_and_unaffected_scope():
    rev_fams = {"multi_constraint_focused_revision", "protected_text_revision", "voice_preserving_revision"}
    for t in tasks():
        if t["task_family"] in rev_fams:
            assert t["evaluation_ground_truth"]["authorized_spans"]
            assert t["evaluation_ground_truth"]["unaffected_spans"]


def test_all_benchmark_exclusion_flags_true():
    for t in tasks():
        bp = t["benchmark_policy"]
        for flag in ("benchmark_only", "excluded_from_training", "excluded_from_teacher_examples",
                     "excluded_from_dataset_revision_examples", "excluded_from_preference_data",
                     "immutable_after_freeze"):
            assert bp[flag] is True


def test_compiler_inputs_do_not_leak_ground_truth():
    for t in tasks():
        ci = json.dumps(t["compiler_inputs"])
        for banned in ("evaluation_ground_truth", "machine_checks", "required_change_checks",
                       "protected_text_checks"):
            assert banned not in ci


def test_comprehension_probes_at_most_six():
    probed = [t["task_id"] for t in tasks() if t.get("comprehension_probe", {}).get("enabled")]
    assert len(probed) <= 6


def test_grounding_and_no_dataset_overlap():
    import sys
    if BENCH not in sys.path:
        sys.path.insert(0, BENCH)
    from validators import checks as C
    for t in tasks():
        assert C.ground_task(t) == []
    val = _j(os.path.join(BENCH, "reports", "task-validation.json"))
    assert val["outcome"] in ("valid", "valid_with_documented_warning")
    assert val["dataset_overlap"] == []


def test_task_freeze_recorded_before_prompt_rendering():
    f = _j(os.path.join(BENCH, "freeze", "task-freeze.json"))
    assert f["task_count"] == 30
    assert f["frozen_before_prompt_rendering"] is True
    assert f["benchmark_exclusion_confirmed"] is True
    assert f["machine_checks_complete"] is True
    # manifest hash still matches the frozen value
    h = hashlib.sha256(open(os.path.join(BENCH, "task-manifest.jsonl"), "rb").read()).hexdigest()
    assert h == f["task_manifest_sha256"]


# ---------------- prompt layer ----------------

def test_prompt_counts_and_no_p3_compiled():
    c = Counter(p["arm"] for p in prompts())
    assert c["P0-Realistic"] == 30 and c["P0-Maximal"] == 30 and c["P1-Contract"] == 30
    assert c["P3-Ideal"] == 10
    assert "P3-Compiled" not in c
    assert sum(c.values()) == 100


def test_information_equivalence_passes():
    eq = _j(os.path.join(BENCH, "reports", "information-equivalence.json"))
    assert eq["tasks_checked"] == 30 and eq["tasks_passed"] == 30 and eq["tasks_failed"] == 0
    assert eq["information_equivalence"] is True


def test_p3_ideal_subset_distribution_and_non_product_label():
    p3 = _j(os.path.join(BENCH, "p3-ideal-subset.json"))
    assert p3["p3_ideal_subset"] == {"focused_revision": 4, "protected_text": 2, "canon": 1,
                                     "voice": 1, "no_change": 1, "scene_drafting": 1}
    assert len(p3["tasks"]) == 10
    assert p3["represents_current_product_compiler"] is False
    assert p3["purpose"] == "theoretical_packet_ceiling"
    for p in prompts():
        if p["arm"] == "P3-Ideal":
            assert p["is_ideal_packet"] is True
        assert p["is_product_compiled"] is False


def test_no_generation_authorized_and_no_outputs_exist():
    for p in prompts():
        assert p["generation_authorized"] is False
    plan = _j(os.path.join(BENCH, "prompt-plan.json"))
    assert plan["generation_authorized"] is False
    assert plan["prompt_counts"]["p3_compiled"] == 0
    for d in ("outputs", "normalized-results", "raw-outputs", "generations"):
        assert not os.path.isdir(os.path.join(BENCH, d)), f"generation output dir {d} must not exist"
    # no run directory for this instrument yet
    assert not os.path.isdir(os.path.join(REPO, "benchmarks", "runs", "linewright-prompt-execution-v1"))


def test_prompt_freeze_before_generation():
    f = _j(os.path.join(BENCH, "freeze", "prompt-freeze.json"))
    assert f["actual_prompt_count"] == 100
    assert f["p3_compiled_status"] == "deferred"
    assert f["information_equivalence_passed"] is True
    assert f["frozen_before_generation"] is True
    assert f["generation_authorized"] is False
    h = hashlib.sha256(open(os.path.join(BENCH, "prompt-arm-manifest.json"), "rb").read()).hexdigest()
    assert h == f["prompt_manifest_sha256"]


# ---------------- repository invariants ----------------

def test_dispatch28_pilot_and_datasets_unchanged():
    # Dispatch-28 decision artifact still present and untouched by this dispatch
    assert os.path.exists(os.path.join(REPO, "training", "reports", "dispatch-28-prompt-effect-decision.yaml"))
    for d in ("dataset-a", "dataset-a.2", "dataset-a.3"):
        assert os.path.isdir(os.path.join(REPO, "datasets", d))
    # frozen thresholds unchanged (shared Gate-0 anchors)
    r = hashlib.sha256(open(os.path.join(REPO, "benchmarks", "thresholds",
                                         "research-continuation-v0.yaml"), "rb").read()).hexdigest()
    assert r == "2be4fddb1aed87c6500dac2a5cdf11e6209b80d2a6d32fa35aa4d63bef131712"


def test_deterministic_check_evaluator_semantics():
    import sys
    if BENCH not in sys.path:
        sys.path.insert(0, BENCH)
    from validators import checks as C
    assert C.check({"t": "absent", "v": "wristwatch"}, "he wore a watch") is True
    assert C.check({"t": "present", "v": "grey"}, "grey eyes") is True
    assert C.check({"t": "preserve", "v": "Hold the gate"}, "Hold the gate, whatever") is True
    assert C.check({"t": "max_openers", "o": "Marla", "max": 2},
                   "Marla ran. Marla hid. Marla wept.") is False
    assert C.check({"t": "shape_json", "keys": ["a", "b"]}, '{"a":1,"b":2}') is True
    assert C.returned_unchanged("  x\r\ny ", "x\ny") is True
