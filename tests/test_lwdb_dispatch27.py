"""Dispatch 27 Phase A — validate Qwen Q4 confirmation manifest, floor, and preservation."""
import hashlib
import json
import os

import yaml

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESEARCH_SHA = "2be4fddb1aed87c6500dac2a5cdf11e6209b80d2a6d32fa35aa4d63bef131712"
STARTER_SHA = "98a57af32fff4d4349466f7877acb5c16ce0e4fae4f376570cfff4407fd1d8b7"
Q4_SHA = "d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785"
Q4_SIZE = 5027783488
RUN = os.path.join(REPO, "benchmarks", "runs", "qwen-prose-confirmation-v1")


def _load(p):
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def test_frozen_thresholds_unchanged():
    for f, sha in (("research-continuation-v0.yaml", RESEARCH_SHA),
                   ("starter-model-acceptance-v0.yaml", STARTER_SHA)):
        actual = hashlib.sha256(open(os.path.join(REPO, "benchmarks", "thresholds", f), "rb").read()).hexdigest()
        assert actual == sha


def test_confirmation_manifest_records_threshold_hashes_and_q4_identity():
    m = _load(os.path.join(REPO, "benchmarks", "manifests", "qwen-prose-confirmation-v1.yaml"))
    ft = m["frozen_thresholds"]
    assert ft["research_continuation_sha256"] == RESEARCH_SHA
    assert ft["starter_model_acceptance_sha256"] == STARTER_SHA
    q4 = next(r for r in m["roles"] if r["role"] == "qwen3_8b_q4_k_m")
    assert q4["artifact_sha256"] == Q4_SHA
    assert q4["artifact_size_bytes"] == Q4_SIZE
    assert q4["official_artifact"] is True
    assert q4["thinking_disabled"] is True
    assert m["confirmation_set"]["total_tasks"] == 15


def test_confirmation_floor_frozen_before_scoring_and_not_ship_gate():
    fl = _load(os.path.join(REPO, "benchmarks", "thresholds", "qwen-q4-confirmation-floor-v0.yaml"))
    assert fl["authorship"] == "agent_proposed" and fl["authority"] == "delegated_by_gary"
    assert fl["created_before_scoring"] is True and fl["frozen_before_unblinding"] is True
    assert fl["final_product_ship_threshold"] is False
    # human gate declared
    assert "gary" in [str(x).lower() for x in fl["reference_qwen_confirmation"]["human_reviewers_required"]]


def test_q4_mechanical_preservation_summary():
    p = os.path.join(RUN, "q4-preservation-summary.json")
    if not os.path.exists(p):
        import pytest
        pytest.skip("q4 preservation summary not generated in this environment")
    s = json.load(open(p, encoding="utf-8"))
    # official Q4 must not materially regress vs BF16, and must not leak reasoning traces
    assert s["deltas_q4_vs_bf16"]["q4_reasoning_leak"] == 0.0
    assert s["mechanical_floor_checks"]["no_reasoning_leak"] is True
    assert s["mechanical_preservation_pass"] is True


def test_q4_outputs_present_and_non_thinking():
    d = os.path.join(RUN, "normalized-results", "q4")
    if not os.path.isdir(d):
        import pytest
        pytest.skip("q4 outputs not present in this environment")
    recs = [json.load(open(os.path.join(d, f), encoding="utf-8")) for f in os.listdir(d) if f.endswith(".json")]
    assert len(recs) == 15
    assert all(r["reasoning_trace_detected"] is False for r in recs)
    assert all(r["reasoning_mode"] == "non_thinking" for r in recs)
