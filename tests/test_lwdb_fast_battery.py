"""Dispatch 24 — fast battery construction, plan, dual-worker routing, scoring, packets.

No real model is run here (deterministic stubs only). Covers the dispatch test lists for
construction, generation-plan, dual-GX10 routing, mechanical+slop, and reviewer packets.
"""
import importlib.util
import json
import os
import tempfile
import glob

import pytest

yaml = pytest.importorskip("yaml")

HERE = os.path.dirname(__file__)
REPO = os.path.abspath(os.path.join(HERE, ".."))
FASTV1 = os.path.join(REPO, "benchmarks", "active-core", "fast-v1")
MANIFEST = os.path.join(REPO, "benchmarks", "manifests", "fast-battery-v1.yaml")

_spec = importlib.util.spec_from_file_location("validate_fast_battery",
                                               os.path.join(FASTV1, "validate_fast_battery.py"))
val = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(val)

from linewright.evaluation.battery.plan_builder import build_plan, endpoint_descriptor
from linewright.evaluation.battery.score import score_run, load_battery, score_output
from linewright.evaluation.battery import packets as pk
from linewright.evaluation.execution.plan import verify_plan_hash
from linewright.evaluation.execution.ledger import Ledger
from linewright.evaluation.execution.worker import StubWorker
from linewright.evaluation.execution.scheduler import Runner, Counter
from linewright.evaluation.calibration.records import load_calibration_set


def _items():
    return {r["item_id"]: r for r in (json.loads(l) for l in
            open(os.path.join(FASTV1, "items.jsonl"), encoding="utf-8") if l.strip())}


# ---------------- construction ----------------

def test_battery_validates_clean():
    problems, stats = val.validate()
    assert problems == [], f"battery invalid: {problems}"


def test_item_count_in_range():
    m = yaml.safe_load(open(MANIFEST, encoding="utf-8"))
    total = m["item_count"] + m["hidden_grader_calibration_seeded"]
    assert 24 <= total <= 30, f"total {total} outside 24-30"


def test_required_modules_and_families_present():
    _, stats = val.validate()
    assert set("ABCDEFGHI").issubset(set(stats["modules"]))   # J embedded
    assert val.REQUIRED_FAMILY_TYPES.issubset(set(stats["family_types"]))


def test_every_item_benchmark_only_and_excluded():
    for it in _items().values():
        assert it["benchmark_only"] is True and it["excluded_from_training"] is True


def test_no_numeric_threshold_in_contracts():
    for line in open(os.path.join(FASTV1, "contracts.jsonl"), encoding="utf-8"):
        if line.strip():
            c = json.loads(line)
            for v in c["required_behaviors"] + c["forbidden_failures"]:
                assert not isinstance(v, (int, float))


def test_manifest_is_hashed():
    m = yaml.safe_load(open(MANIFEST, encoding="utf-8"))
    assert m["battery_hash"] and m["status"] == "frozen"
    assert m["production_approved"] is False and m["experimental_use_only"] is True


# ---------------- generation plan ----------------

def _plan(tmp, mode="parallel_multi_host", sched="round_robin"):
    return build_plan(
        base_descriptor={"identity": "base", "revision": "r1", "endpoint_id": "ep-base"},
        candidate_descriptor={"identity": "cand", "checkpoint": "lora/step-20", "revision": "r2",
                              "endpoint_id": "ep-cand"},
        generation_settings={"temperature": 0, "top_p": 1},
        seeds={"target_base": 7, "new_candidate": 7}, max_new_tokens=512,
        output_directory=os.path.join(tmp, "out"), execution_mode=mode, scheduling_policy=sched)


def test_plan_deterministic_and_verifies(tmp_path):
    a = _plan(str(tmp_path))
    b = _plan(str(tmp_path))
    assert a["plan_hash"] == b["plan_hash"] and verify_plan_hash(a)


def test_base_and_candidate_share_item_and_contract_hashes(tmp_path):
    p = _plan(str(tmp_path))
    # every job (item x role) references the SAME item + contract hashes regardless of role
    assert set(p["item_hashes"]) == set(p["behavior_contract_hashes"])
    assert "target_base" in p["model_roles"] and "new_candidate" in p["model_roles"]


def test_parallel_and_sequential_same_plan_hash(tmp_path):
    par = _plan(str(tmp_path), "parallel_multi_host", "round_robin")
    seq = _plan(str(tmp_path), "sequential_single_host", "model_sequential")
    assert par["plan_hash"] == seq["plan_hash"]


def test_secrets_not_serialized(tmp_path):
    with pytest.raises(AssertionError):
        build_plan(base_descriptor={"identity": "b", "api_key": "SECRET", "endpoint_id": "e"},
                   candidate_descriptor={"identity": "c", "endpoint_id": "e2"},
                   generation_settings={}, seeds={}, max_new_tokens=8,
                   output_directory=str(tmp_path))


def test_endpoint_descriptor_references_secret_not_literal():
    d = endpoint_descriptor("ep", "openai_compatible_http", "m", "gx10-9141",
                            base_url="http://x", auth_env="LWDB_TOKEN")
    assert d["authentication_source"] == "ENV:LWDB_TOKEN"
    assert "SECRET" not in json.dumps(d)


# ---------------- dual-GX10 worker routing ----------------

def test_dual_worker_routing():
    base_worker = StubWorker("w-base", "gx10-9141", ["target_base"])
    cand_worker = StubWorker("w-cand", "gx10-5611", ["new_candidate"])
    assert base_worker.can_handle("target_base") and not base_worker.can_handle("new_candidate")
    assert cand_worker.can_handle("new_candidate") and not cand_worker.can_handle("target_base")


def test_dual_worker_run_routes_by_role(tmp_path):
    plan = _plan(str(tmp_path))
    lg = Ledger(os.path.join(tmp_path, "r.db"))
    r = Runner(lg, plan, [StubWorker("w-base", "gx10-9141", ["target_base"]),
                          StubWorker("w-cand", "gx10-5611", ["new_candidate"])],
               os.path.join(tmp_path, "res"), clock=Counter())
    r.start("run"); r.run()
    jobs = lg.list_jobs("run")
    for j in jobs:
        # base jobs completed by the base host, candidate jobs by the candidate host
        res = json.load(open(j["output_path"], encoding="utf-8"))
        expected_host = "gx10-9141" if j["model_role"] == "target_base" else "gx10-5611"
        assert res["host_id"] == expected_host
    assert lg.counts("run").get("completed") == 40
    lg.close()


# ---------------- mechanical + slop scoring ----------------

def test_scoring_produces_mechanical_and_slop_per_output(tmp_path):
    plan = _plan(str(tmp_path))
    lg = Ledger(os.path.join(tmp_path, "s.db"))
    r = Runner(lg, plan, [StubWorker("wb", "gx10-9141", ["target_base"]),
                          StubWorker("wc", "gx10-5611", ["new_candidate"])],
               os.path.join(tmp_path, "res"), clock=Counter())
    r.start("run"); r.run()
    norm = [json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(tmp_path, "res", "*.json"))]
    scored = score_run(norm)
    assert len(scored["per_output"]) == 40
    for o in scored["per_output"]:
        assert "mechanical_pass" in o["mechanical"]
        assert o["slop"]["summary"]["severity"] in ("none", "low", "moderate", "high", "severe", "inconclusive")
    assert set(scored["corpus_summaries"]) == {"target_base", "new_candidate"}
    lg.close()


def test_severe_repetition_detected_and_evidence_retained():
    items, contracts = load_battery()
    it = items["lwdb-a-length-long"]
    c = contracts[it["behavior_contract_id"]]
    s = score_output(it, c, "The door creaks. " * 30)
    assert s["slop"]["summary"]["severity"] in ("high", "severe")
    assert s["slop"]["deterministic"]["evidence_spans"]


def test_slop_thresholds_unvalidated():
    items, contracts = load_battery()
    it = items["lwdb-a-quiet-scene"]
    c = contracts[it["behavior_contract_id"]]
    s = score_output(it, c, "A calm short passage about a beekeeper at dusk in the cold.")
    assert s["slop"]["summary"]["semantic_confidence"] == "unvalidated"


# ---------------- reviewer packets ----------------

def _run_and_norm(tmp_path):
    plan = _plan(str(tmp_path))
    lg = Ledger(os.path.join(tmp_path, "p.db"))
    r = Runner(lg, plan, [StubWorker("wb", "gx10-9141", ["target_base"]),
                          StubWorker("wc", "gx10-5611", ["new_candidate"])],
               os.path.join(tmp_path, "res"), clock=Counter())
    r.start("run"); r.run(); lg.close()
    return [json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(tmp_path, "res", "*.json"))]


def test_absolute_packets_no_identity_leak_and_calibration_blind(tmp_path):
    norm = _run_and_norm(tmp_path)
    cal = load_calibration_set(os.path.join(REPO, "benchmarks", "calibration",
                                            "grader-calibration-set-v1.jsonl"))[:4]
    units, key = pk.build_absolute_packets(norm, _items(), calibration_records=cal)
    assert pk.identity_leak_check(units) == []
    assert all("model_role" not in u and "kind" not in u for u in units)
    # calibration items indistinguishable in the units; only the key knows
    assert sum(1 for v in key.values() if v["kind"] == "calibration") == 4
    assert len(units) == 44


def test_candidate_order_shuffled_not_role_ordered(tmp_path):
    norm = _run_and_norm(tmp_path)
    pw, keys = pk.build_pairwise_packets(norm, _items())
    # not every item maps Candidate A -> target_base (order is content-derived)
    a_is_base = []
    for iid, key in keys.items():
        first = key["unblinding"]["Candidate A"]["identity"]
        a_is_base.append(first == "target_base")
    assert not all(a_is_base) and any(a_is_base)      # shuffled, not constant


def test_absolute_built_before_pairwise():
    # API contract: pairwise packets require the same normalized results; absolute is the
    # first-class product (units carry a review_form; pairwise carries candidates A/B).
    from linewright.evaluation.battery import packets
    assert hasattr(packets, "build_absolute_packets") and hasattr(packets, "build_pairwise_packets")


# ---------------- invariants ----------------

def test_no_battery_item_in_training_dirs():
    for root in (os.path.join(REPO, "datasets"), os.path.join(REPO, "training", "runs")):
        for p in glob.glob(os.path.join(root, "**", "*lwdb*"), recursive=True):
            raise AssertionError(f"battery artifact in a training/data dir: {p}")
