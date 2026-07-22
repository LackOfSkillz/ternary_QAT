"""Dispatch 25 — diagnostic findings, packet profile, blind access-separation, checkpoint
curve, dataset audit, and decision invariants. Analysis-time invariants (thresholds frozen)."""
import hashlib
import json
import os

import pytest

yaml = pytest.importorskip("yaml")

HERE = os.path.dirname(__file__)
REPO = os.path.abspath(os.path.join(HERE, ".."))
D24 = os.path.join(REPO, "benchmarks", "runs", "lwdb-fast-v1-20260722")
CURVE = os.path.join(REPO, "benchmarks", "runs", "lwdb-checkpoint-curve-v0")
AUDIT = os.path.join(REPO, "training", "reports", "dataset-a-a2-audit-v1")


def _j(p):
    return json.load(open(p, encoding="utf-8"))


# ---- diagnostic findings (observation / cause / intervention separation) ----

def test_pair_findings_separate_layers():
    f = _j(os.path.join(D24, "diagnostic-findings.json"))
    assert f["controlled_pairs_analyzed"] == 7 and len(f["findings"]) == 7
    for fd in f["findings"]:
        assert fd["observation"]["observation_confidence"] in ("mechanical", "high", "moderate", "low", "inconclusive")
        for h in fd["causal_hypotheses"]:
            assert h["confidence"] in ("high", "moderate", "low", "speculative")
            assert h["required_disambiguating_test"] and h["competing_explanations"]
        for iv in fd["proposed_interventions"]:
            assert iv["confidence"] in ("high", "moderate", "low", "speculative")
            assert iv["validation_plan"] and "benchmark_items_that_would_be_burned" in iv


def test_findings_stamped_with_threshold_lock():
    f = _j(os.path.join(D24, "diagnostic-findings.json"))
    lock = _j(os.path.join(REPO, "benchmarks", "thresholds", "threshold-lock-v0.json"))
    assert f["threshold_lock"]["research_sha256"] == lock["research_threshold_sha256"]


# ---- packet token profile ----

def test_packet_profile_real_tokens_and_classification():
    p = _j(os.path.join(D24, "packet-token-profile.json"))
    assert p["tokenizer_revision"] == "4485fae7a00129467b9329b738110d88b2942a1a"
    prof = p["packet_token_profile"]
    assert prof["bare"]["total_prompt_tokens"] > 0 and prof["compiled"]["total_prompt_tokens"] > 0
    comp = prof["compiled"]
    assert comp["total_prompt_tokens"] == sum(v for k, v in comp.items() if k != "total_prompt_tokens")
    assert any(p["packet_realism"].values())
    assert p["missing_components"]                 # honest: a partial packet has missing components
    assert p["future_packet_curve_required"]


# ---- blind access separation ----

def test_blind_scoring_cannot_access_identity(tmp_path):
    from linewright.evaluation.battery import blind
    units = [{"unit_id": "u1", "output_text": "x", "review_form": {"a": None}},
             {"unit_id": "u2", "output_text": "y", "review_form": {"a": None}}]
    review = str(tmp_path / "review")
    private = str(tmp_path / "private-unblinding")
    blind.build_review_bundle(units, {"u1": {"model_role": "target_base"}},
                              {"i1": {}}, review, private)
    # private dir must be OUTSIDE the review dir
    assert not os.path.abspath(private).startswith(os.path.abspath(review) + os.sep)
    forms = [{"unit_id": "u1", "score": 4}, {"unit_id": "u2", "score": 3}]
    # scoring runs with reads of the private dir DENIED — must succeed (never touches it)
    locks = blind.assert_scoring_is_blind(private, lambda: blind.finalize_scores(review, forms))
    assert set(locks) == {"u1", "u2"}
    # a reviewer trying to open the identity key under the guard fails
    with pytest.raises(blind.IdentityAccessError):
        blind.assert_scoring_is_blind(private, lambda: open(os.path.join(private, "identity-key.json")))


def test_unblind_requires_score_locks(tmp_path):
    from linewright.evaluation.battery import blind
    units = [{"unit_id": "u1", "output_text": "x", "review_form": {}}]
    review = str(tmp_path / "review"); private = str(tmp_path / "private-unblinding")
    blind.build_review_bundle(units, {"u1": {"model_role": "base"}}, {}, review, private)
    with pytest.raises(blind.UnblindError):
        blind.unblind(review, private, ["u1"])            # no score locks yet
    blind.finalize_scores(review, [{"unit_id": "u1"}])
    key = blind.unblind(review, private, ["u1"])
    assert key["u1"]["model_role"] == "base"


# ---- checkpoint curve ----

def test_checkpoint_curve_frozen_subset_and_no_winner():
    man = _j(os.path.join(CURVE, "checkpoint-manifest.json"))
    assert man["subset_frozen_before_generation"] is True and len(man["subset_item_ids"]) == 9
    s = _j(os.path.join(CURVE, "checkpoint-curve-summary.json"))
    assert s["no_winner_declared"] is True
    rows = _j(os.path.join(CURVE, "item-level-results.json"))
    assert len(rows) == 27 and {r["checkpoint"] for r in rows} == {"target_base", "lora_10", "lora_20"}
    for r in rows:
        assert r["output_hash"]


# ---- decision ----

def test_decision_uses_locked_hashes_and_documents_rejected_branches():
    d = yaml.safe_load(open(os.path.join(REPO, "training", "reports", "dispatch-25-decision-v1.yaml"),
                            encoding="utf-8"))["decision"]
    lock = _j(os.path.join(REPO, "benchmarks", "thresholds", "threshold-lock-v0.json"))
    assert d["threshold_lock"]["research_sha256"] == lock["research_threshold_sha256"]
    assert d["threshold_lock"]["threshold_precommit_valid"] is True
    assert d["branch"] in ("continue_scaled_dataset", "checkpoint_selection_only", "test_stronger_base",
                           "revise_training_objective", "pause_current_direction", "insufficient_evidence")
    assert d["rejected_branches"] and all("reason" in b for b in d["rejected_branches"])
    assert d["ambiguous_middle_action"]
    assert d["required_next_experiment"]


def test_next_experiment_gated_no_training():
    y = yaml.safe_load(open(os.path.join(REPO, "training", "specs", "next-linewright-experiment-v1.yaml"),
                            encoding="utf-8"))["next_experiment"]
    assert y["primary"]["training_started"] is False
    assert y["secondary_separately_authorized"]["training_started"] is False
    assert y["primary"]["controlled_variables"] == ["base_model"]


# ---- dataset audit + invariants ----

def test_audit_reports_examples_and_tokens_both():
    td = _j(os.path.join(AUDIT, "task-distribution.json"))
    for ds in ("dataset_a", "dataset_a2"):
        assert td[ds]["examples_by_task"] and td[ds]["tokens_by_task"]


def test_audit_provenance_recorded_not_guessed():
    p = _j(os.path.join(AUDIT, "provenance-summary.json"))
    assert "not inferred" in p["note"].lower() or "as recorded" in p["note"].lower()
    assert any("claude-opus-4-8" in k for k in p["dataset_a"])


def test_dataset_a_and_a2_unchanged():
    cfg = yaml.safe_load(open(os.path.join(REPO, "training", "configs",
                        "dataset-a-lora-full-comparison-v1.yaml"), encoding="utf-8"))["dataset"]
    base = os.path.join(REPO, "datasets", "dataset-a", "compiled", "experimental-v1")
    for fname, pinned in (("train.jsonl", cfg["train_checksum"]),
                          ("evaluation.jsonl", cfg["evaluation_checksum"])):
        assert hashlib.sha256(open(os.path.join(base, fname), "rb").read()).hexdigest() == pinned
    man = _j(os.path.join(REPO, "datasets", "dataset-a.2", "pilot", "manifest.json"))
    pilot = os.path.join(REPO, "datasets", "dataset-a.2", "pilot")
    for fname, key in (("train.jsonl", "train_sha256"), ("evaluation.jsonl", "evaluation_sha256")):
        rows = [json.loads(l) for l in open(os.path.join(pilot, fname), encoding="utf-8") if l.strip()]
        digest = hashlib.sha256("".join(json.dumps(r, ensure_ascii=False) for r in rows).encode("utf-8")).hexdigest()
        assert digest == man[key]


def test_voice_p0a_status_recorded():
    v = yaml.safe_load(open(os.path.join(REPO, "training", "reports", "voice-p0a-status-v1.yaml"),
                            encoding="utf-8"))["voice_p0a"]
    assert v["found"] is True and v["blocked"] is False
    assert "ROADMAP" in v["authoritative_reference"]
