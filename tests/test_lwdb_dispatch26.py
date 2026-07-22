"""Dispatch 26 — validate stronger-base plan integrity, packet family, identity, blindness."""
import hashlib
import json
import os

import pytest
import yaml

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PF = os.path.join(REPO, "benchmarks", "active-core", "packet-family-v1")
RESEARCH_SHA = "2be4fddb1aed87c6500dac2a5cdf11e6209b80d2a6d32fa35aa4d63bef131712"
STARTER_SHA = "98a57af32fff4d4349466f7877acb5c16ce0e4fae4f376570cfff4407fd1d8b7"


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _read_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def load_manifest():
    with open(os.path.join(REPO, "benchmarks", "manifests", "stronger-base-extension-v1.yaml"),
              encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# ---- plan integrity ------------------------------------------------------

def test_fast_battery_v1_unchanged():
    m = load_manifest()
    actual = _sha(os.path.join(REPO, "benchmarks", "manifests", "fast-battery-v1.yaml"))
    assert m["references"]["fast_battery_v1"]["manifest_sha256"] == actual
    assert m["references"]["fast_battery_v1"]["modified"] is False


def test_extension_manifest_records_frozen_threshold_hashes():
    m = load_manifest()
    ft = m["frozen_thresholds"]
    assert ft["research_continuation_sha256"] == RESEARCH_SHA
    assert ft["starter_model_acceptance_sha256"] == STARTER_SHA
    assert ft["thresholds_unchanged"] is True


def test_frozen_threshold_files_unchanged():
    import hashlib as h
    r = h.sha256(open(os.path.join(REPO, "benchmarks", "thresholds", "research-continuation-v0.yaml"), "rb").read()).hexdigest()
    s = h.sha256(open(os.path.join(REPO, "benchmarks", "thresholds", "starter-model-acceptance-v0.yaml"), "rb").read()).hexdigest()
    assert r == RESEARCH_SHA and s == STARTER_SHA


def test_plan_hash_verifies_and_94_jobs():
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from linewright.evaluation.execution.plan import verify_plan_hash
    plan = json.load(open(os.path.join(REPO, "benchmarks", "runs", "lwdb-stronger-base-v1",
                                       "generation-plan.json"), encoding="utf-8"))
    assert verify_plan_hash(plan)
    assert sorted(plan["model_roles"]) == ["ministral_3_8b_instruct", "qwen3_8b_non_thinking", "target_base_4b"]
    n_jobs = sum(len(plan["items"][i]["model_roles"]) for i in plan["item_ids"])
    assert n_jobs == 94
    # 4B is NOT on fast-battery items (reused); IS on packet items
    fast = [i for i in plan["item_ids"] if not i.startswith("pf-")]
    pf = [i for i in plan["item_ids"] if i.startswith("pf-")]
    assert len(fast) == 20 and len(pf) == 18
    for i in fast:
        assert "target_base_4b" not in plan["items"][i]["model_roles"]
    for i in pf:
        assert set(plan["items"][i]["model_roles"]) == {"target_base_4b", "ministral_3_8b_instruct", "qwen3_8b_non_thinking"}


def test_qwen_non_thinking_and_greedy():
    plan = json.load(open(os.path.join(REPO, "benchmarks", "runs", "lwdb-stronger-base-v1",
                                       "generation-plan.json"), encoding="utf-8"))
    assert plan["model_descriptors"]["qwen3_8b_non_thinking"]["enable_thinking"] is False
    assert plan["generation_settings"]["temperature"] == 0.0


# ---- packet family -------------------------------------------------------

def test_packet_family_six_arms_three_tasks():
    items = _read_jsonl(os.path.join(PF, "packet-items.jsonl"))
    assert len(items) == 18
    arms = sorted({i["packet_arm"] for i in items})
    assert arms == sorted(["bare", "compact", "realistic", "long", "long_noisy", "long_salience_repaired"])
    tasks = sorted({i["task_family"] for i in items})
    assert tasks == sorted(["scene_drafting", "focused_revision", "canon_sensitive_continuation"])


def test_noisy_and_repaired_identical_content():
    comp = json.load(open(os.path.join(PF, "packet-composition.json"), encoding="utf-8"))
    by = {c["item_id"]: c for c in comp["items"]}
    for task in ["scene_drafting", "focused_revision", "canon_sensitive_continuation"]:
        noisy = sorted(by[f"pf-{task}-long_noisy"]["components"])
        repaired = sorted(c for c in by[f"pf-{task}-long_salience_repaired"]["components"]
                          if c != "appendix_header")
        assert noisy == repaired, task


def test_monotone_context_growth():
    comp = json.load(open(os.path.join(PF, "packet-composition.json"), encoding="utf-8"))
    for task, chars in comp["monotone_char_growth_per_task"].items():
        assert chars[0] < chars[1] < chars[2] < chars[3], (task, chars)


# ---- candidate identity --------------------------------------------------

def test_candidate_record_apache_and_revisions():
    with open(os.path.join(REPO, "training", "reports", "dispatch-26-model-candidate-record.yaml"),
              encoding="utf-8") as fh:
        rec = yaml.safe_load(fh)
    c = rec["candidates"]
    assert c["qwen3_8b_non_thinking"]["revision"] == "b968826d9c46dd6066d109eabc6255188de91218"
    assert c["ministral_3_8b_instruct"]["revision"] == "5b26027e7b19eeb4b7352e1fed3926375dd2cb4d"
    assert c["qwen3_8b_non_thinking"]["license"] == "apache-2.0"
    assert c["ministral_3_8b_instruct"]["license"] == "apache-2.0"
    assert c["ministral_3_8b_instruct"]["modality"].startswith("MULTIMODAL")


# ---- blindness -----------------------------------------------------------

def test_blind_separation_and_unblind_gating(tmp_path):
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from linewright.evaluation.battery import blind
    units = [{"unit_id": "unit-abc123", "review_form": {"prose_quality": None}, "text": "x"},
             {"unit_id": "unit-def456", "review_form": {"prose_quality": None}, "text": "y"}]
    review_root = str(tmp_path / "run" / "review_area")
    private_root = str(tmp_path / "run" / "private-unblinding")
    key = {"units": {"unit-abc123": {"model_role": "ministral_3_8b_instruct"},
                     "unit-def456": {"model_role": "qwen3_8b_non_thinking"}}}
    blind.build_review_bundle(units, key, {}, review_root, private_root)
    # no identity in reviewer-facing ids
    for u in units:
        assert "ministral" not in u["unit_id"] and "qwen" not in u["unit_id"]
    # unblinding refuses before scores are locked
    with pytest.raises(blind.UnblindError):
        blind.unblind(review_root, private_root, [u["unit_id"] for u in units])
    # scoring cannot open the identity key
    with pytest.raises(blind.IdentityAccessError):
        blind.assert_scoring_is_blind(
            private_root, lambda: open(os.path.join(private_root, "identity-key.json")).read())
    # after locking, unblind works
    blind.finalize_scores(review_root, [{"unit_id": u["unit_id"], "scores": {}} for u in units])
    revealed = blind.unblind(review_root, private_root, [u["unit_id"] for u in units])
    assert "units" in revealed


# ---- threshold lock ------------------------------------------------------

def test_threshold_lock_valid():
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from linewright.evaluation.thresholds import freeze
    v = freeze.verify_lock()
    assert v.get("threshold_precommit_valid") is True


# ---- results validation (frozen threshold applied honestly) ---------------

RUN = os.path.join(REPO, "benchmarks", "runs", "lwdb-stronger-base-v1")


def test_run_integrity_clean_94_jobs():
    s = json.load(open(os.path.join(RUN, "run-summary.json"), encoding="utf-8"))
    integ = s["integrity"]
    assert integ["expected_jobs"] == 94 and integ["got_jobs"] == 94 and integ["missing"] == 0
    assert integ["problems"] == []
    assert integ["mechanical_replay_identical"] is True


def test_qwen_no_reasoning_trace_leak():
    s = json.load(open(os.path.join(RUN, "run-summary.json"), encoding="utf-8"))
    assert s["per_role"]["qwen3_8b_non_thinking"]["reasoning_trace_rate"] == 0.0


def test_core_prose_feasibility_applies_frozen_floor():
    with open(os.path.join(REPO, "training", "reports", "dispatch-26-core-prose-feasibility.yaml"),
              encoding="utf-8") as fh:
        f = yaml.safe_load(fh)["core_prose_feasibility"]
    assert f["frozen_floor"] == 0.5
    pm = f["per_model"]
    # both stronger bases clear the core-prose floor; the 4B does not
    assert pm["qwen3_8b_non_thinking"]["clears_floor"] is True
    assert pm["ministral_3_8b_instruct"]["clears_floor"] is True
    assert pm["target_base_4b"]["clears_floor"] is False
    # Qwen clears ALL floors; Ministral fails module coverage
    assert pm["qwen3_8b_non_thinking"]["clears_all_floors"] is True
    assert pm["ministral_3_8b_instruct"]["clears_all_floors"] is False


def test_foundation_decision_threshold_locked_and_valid_branch():
    with open(os.path.join(REPO, "training", "reports", "dispatch-26-foundation-decision.yaml"),
              encoding="utf-8") as fh:
        d = yaml.safe_load(fh)["foundation_decision"]
    assert d["threshold_lock"]["valid"] is True
    assert d["threshold_lock"]["research_sha256"] == RESEARCH_SHA
    assert d["branch"] in ("select_Ministral_3_8B", "select_Qwen3_8B", "retain_current_4B",
                           "run_one_bounded_confirmation", "test_another_base", "insufficient_evidence")
    assert d["final_commercial_ship_certification"] is False


def test_blind_review_scores_locked_and_no_pairwise_override():
    s = json.load(open(os.path.join(RUN, "blind-review-summary.json"), encoding="utf-8"))
    assert s["scores_locked_before_unblinding"] is True
    assert s["pairwise_preference_cannot_override_fatal"] is True
    assert "Gary" in s["reviewers"]["external_humans_pending"]
