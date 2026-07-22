"""Dispatch 23 — hardware-agnostic execution + durable pause/resume (Workstreams B/C).

Plan freezing, parallel/sequential equivalence, graceful + immediate pause, controller
restart recovery, expired-lease recovery, output-integrity verification, retry bounds, and
the full pause -> shutdown -> resume integration scenario, all with deterministic stubs.
"""
import json
import os

import pytest

from linewright.evaluation.execution.plan import create_plan, verify_plan_hash, job_tuples
from linewright.evaluation.execution.ledger import Ledger
from linewright.evaluation.execution.worker import StubWorker, normalized_result, to_anonymous
from linewright.evaluation.execution.scheduler import Runner, Counter
from linewright.evaluation.execution.retry import RetryPolicy
from linewright.evaluation.execution import recovery, integrity, cli


def make_plan(tmp, mode="parallel_single_host", sched="round_robin", n=3, plan_id="p1"):
    items = [{"item_id": f"it{i}", "prompt": f"write scene {i}",
              "behavior_contract": {"schema_id": "prose-v1"}} for i in range(n)]
    return create_plan(
        battery_version="v1", battery_profile="calibration", execution_mode=mode,
        scheduling_policy=sched, items=items,
        model_descriptors={"target_base": {"identity": "base", "revision": "r1", "endpoint_id": "eA"},
                           "new_candidate": {"identity": "cand", "revision": "r2", "endpoint_id": "eB"}},
        generation_settings={"temperature": 0, "top_p": 1},
        seeds={"target_base": 1, "new_candidate": 1}, max_new_tokens=64,
        retry_policy_id="default", output_directory=os.path.join(tmp, "out"), plan_id=plan_id)


def workers_dual():
    return [StubWorker("w-base", "hostA", ["target_base"]),
            StubWorker("w-cand", "hostB", ["new_candidate"])]


def _run_all(tmp, plan, tag, workers=None):
    lg = Ledger(os.path.join(tmp, tag + ".db"))
    r = Runner(lg, plan, workers or workers_dual(), os.path.join(tmp, tag), clock=Counter())
    r.start("run-" + tag)
    r.run()
    jobs = lg.list_jobs("run-" + tag)
    lg.close()
    return jobs


# ---- plan ----

def test_plan_hashes_deterministically(tmp_path):
    a = make_plan(str(tmp_path))
    b = make_plan(str(tmp_path))
    assert a["plan_hash"] == b["plan_hash"] and verify_plan_hash(a)


def test_plan_cannot_mutate_silently(tmp_path):
    p = make_plan(str(tmp_path))
    p["generation_settings"]["temperature"] = 0.9  # tamper
    assert verify_plan_hash(p) is False  # a changed plan no longer verifies -> new run required


def test_parallel_and_sequential_same_hashes_and_results(tmp_path):
    par = make_plan(str(tmp_path), "parallel_single_host", "round_robin")
    seq = make_plan(str(tmp_path), "sequential_single_host", "model_sequential")
    assert par["plan_hash"] == seq["plan_hash"]
    assert par["item_hashes"] == seq["item_hashes"]
    assert par["generation_settings_hash"] == seq["generation_settings_hash"]
    jp = {(j["benchmark_item_id"], j["model_role"]): j["output_hash"] for j in _run_all(str(tmp_path), par, "par")}
    js = {(j["benchmark_item_id"], j["model_role"]): j["output_hash"] for j in _run_all(str(tmp_path), seq, "seq")}
    assert jp == js and len(jp) == 6


def test_model_role_and_endpoint_stay_out_of_anonymous(tmp_path):
    plan = make_plan(str(tmp_path))
    w = workers_dual()[0]
    gen = w.generate(plan, "it0", "target_base")
    res = normalized_result(plan, "r", "j", "it0", "target_base", gen, w,
                            "parallel_single_host", 1, 2)
    anon = to_anonymous(res, "Candidate A")
    for forbidden in ("model_role", "model_identity_ref", "host_id", "execution_mode", "worker_id"):
        assert forbidden not in anon


def test_secrets_not_serialized(tmp_path):
    with pytest.raises(AssertionError):
        create_plan(battery_version="v", battery_profile="calibration",
                    execution_mode="parallel_single_host", scheduling_policy="round_robin",
                    items=[{"item_id": "i", "prompt": "p"}],
                    model_descriptors={"target_base": {"identity": "b", "api_key": "SECRET"}},
                    generation_settings={}, seeds={}, max_new_tokens=8,
                    retry_policy_id="d", output_directory=str(tmp_path))


# ---- pause / resume ----

def test_graceful_pause_stops_new_assignment(tmp_path):
    plan = make_plan(str(tmp_path), n=4)
    lg = Ledger(os.path.join(tmp_path, "g.db"))
    r = Runner(lg, plan, [StubWorker("w", "h", ["target_base", "new_candidate"])],
               os.path.join(tmp_path, "g"), clock=Counter())
    r.start("rg")
    r.run(pause_after_completed=3, pause_mode="graceful")
    c = lg.counts("rg")
    assert lg.get_run("rg")["status"] == "paused"
    assert c.get("completed") == 3 and c.get("pending", 0) > 0  # remaining left pending
    lg.close()


def test_immediate_pause_interrupts_active_job(tmp_path):
    plan = make_plan(str(tmp_path))
    lg = Ledger(os.path.join(tmp_path, "i.db"))
    r = Runner(lg, plan, [StubWorker("w", "h", ["target_base", "new_candidate"])],
               os.path.join(tmp_path, "i"), clock=Counter())
    r.start("ri")
    jid = r.lease_one()
    assert lg.get_job(jid)["status"] == "running"
    r.pause_immediate()
    assert lg.get_job(jid)["status"] == "interrupted"
    assert lg.get_run("ri")["status"] == "paused"
    lg.close()


def test_expired_lease_recovers(tmp_path):
    plan = make_plan(str(tmp_path))
    lg = Ledger(os.path.join(tmp_path, "e.db"))
    r = Runner(lg, plan, [StubWorker("w", "h", ["target_base", "new_candidate"])],
               os.path.join(tmp_path, "e"), lease_seconds=5, clock=Counter())
    r.start("re")
    jid = r.lease_one()
    reclaimed = lg.reclaim_expired_leases(10_000)
    assert jid in reclaimed and lg.get_job(jid)["status"] == "interrupted"
    lg.close()


def test_retry_count_increments_and_terminal_not_retried(tmp_path):
    plan = make_plan(str(tmp_path), n=1)
    lg = Ledger(os.path.join(tmp_path, "rt.db"))
    lg.create_run("rr", plan["plan_id"], plan["plan_hash"], "parallel_single_host", "local_resumable", 1)
    lg.add_jobs("rr", job_tuples(plan))
    jid = lg.list_jobs("rr")[0]["job_id"]
    lg.fail_job(jid, "endpoint_timeout", retryable=True, now=2)
    assert lg.get_job(jid)["attempt_count"] == 1 and lg.get_job(jid)["status"] == "failed_retryable"
    pol = RetryPolicy(max_attempts=2)
    assert pol.should_retry(1, "endpoint_timeout") is True
    assert pol.should_retry(2, "endpoint_timeout") is False       # bounded
    assert pol.classify("prompt_hash_mismatch") == "terminal"
    lg.close()


def test_no_completed_job_duplicated_silently(tmp_path):
    plan = make_plan(str(tmp_path), n=1)
    lg = Ledger(os.path.join(tmp_path, "d.db"))
    lg.create_run("rd", plan["plan_id"], plan["plan_hash"], "parallel_single_host", "local_resumable", 1)
    lg.add_jobs("rd", job_tuples(plan))
    jid = lg.list_jobs("rd")[0]["job_id"]
    assert lg.complete_job(jid, "p", "hash1", 2) is True
    assert lg.complete_job(jid, "p2", "hash2", 3) is False       # not overwritten silently
    assert lg.get_job(jid)["output_hash"] == "hash1"
    lg.close()


def test_corrupted_completed_output_not_skipped(tmp_path):
    plan = make_plan(str(tmp_path), n=2)
    od = os.path.join(tmp_path, "c")
    lg = Ledger(os.path.join(tmp_path, "c.db"))
    r = Runner(lg, plan, [StubWorker("w", "h", ["target_base", "new_candidate"])], od, clock=Counter())
    r.start("rc")
    r.run()
    done = lg.list_jobs("rc", status="completed")
    victim = done[0]
    # corrupt the output file
    p = victim["output_path"]
    obj = json.load(open(p, encoding="utf-8"))
    obj["output_text"] = "TAMPERED"
    json.dump(obj, open(p, "w", encoding="utf-8"))
    demoted = recovery.verify_completed(lg, plan, "rc", od, now=9000)
    assert any(d["job_id"] == victim["job_id"] for d in demoted)
    assert lg.get_job(victim["job_id"])["status"] == "interrupted"
    lg.close()


# ---- full integration: pause -> shutdown -> new controller -> resume ----

def test_pause_shutdown_resume_integration(tmp_path):
    plan = make_plan(str(tmp_path), n=4)
    db = os.path.join(tmp_path, "int.db")
    od = os.path.join(tmp_path, "int")
    total = len(job_tuples(plan))

    lg = Ledger(db)
    r = Runner(lg, plan, [StubWorker("w1", "h", ["target_base", "new_candidate"])], od, clock=Counter())
    r.start("rint")
    r.run(pause_after_completed=3, pause_mode="graceful")
    before = {j["job_id"]: j["output_hash"] for j in lg.list_jobs("rint", status="completed")}
    assert len(before) == 3
    lg.close()  # controller shutdown

    # brand-new controller process: fresh Ledger + Runner on the same durable db, new worker id
    lg2 = Ledger(db)
    r2 = Runner(lg2, plan, [StubWorker("w2", "h2", ["target_base", "new_candidate"])], od,
                clock=Counter(1000))
    r2.run_id = "rint"
    r2.resume()
    after = {j["job_id"]: j["output_hash"] for j in lg2.list_jobs("rint", status="completed")}
    assert len(after) == total                                   # all jobs done
    assert all(after[k] == v for k, v in before.items())         # prior work not rerun/changed
    # no job completed twice
    completes = [e for e in lg2.events("rint") if e["event_type"] == "job_completed"]
    per_job = {}
    for e in completes:
        per_job[e["job_id"]] = per_job.get(e["job_id"], 0) + 1
    assert all(v == 1 for v in per_job.values())
    assert lg2.get_run("rint")["status"] == "completed"
    lg2.close()


def test_sequential_model_switch_preserves_run(tmp_path):
    # sequential single-host: complete part of one role, pause, resume, finish other role
    plan = make_plan(str(tmp_path), "sequential_single_host", "model_sequential", n=3)
    db = os.path.join(tmp_path, "sw.db")
    od = os.path.join(tmp_path, "sw")
    lg = Ledger(db)
    r = Runner(lg, plan, [StubWorker("w", "h", ["target_base", "new_candidate"])], od, clock=Counter())
    r.start("rsw")
    r.run(pause_after_completed=2, pause_mode="graceful")
    lg.close()
    lg2 = Ledger(db)
    r2 = Runner(lg2, plan, [StubWorker("w", "h", ["target_base", "new_candidate"])], od, clock=Counter(500))
    r2.run_id = "rsw"
    r2.resume()
    assert lg2.get_run("rsw")["status"] == "completed"
    assert lg2.counts("rsw").get("completed") == len(job_tuples(plan))
    lg2.close()


# ---- CLI ----

def test_cli_status_and_worker_and_export(tmp_path):
    plan = make_plan(str(tmp_path), n=2)
    db = os.path.join(tmp_path, "cli.db")
    lg = Ledger(db)
    r = Runner(lg, plan, [StubWorker("w", "h", ["target_base", "new_candidate"])],
               os.path.join(tmp_path, "cli"), clock=Counter())
    r.start("rcli")
    r.run()
    lg.close()
    args = cli.build_parser().parse_args(["run", "status", "--db", db, "--run-id", "rcli"])
    out = args.fn(args)
    assert out["job_counts"].get("completed") == 4
    wargs = cli.build_parser().parse_args(["worker", "status", "--db", db])
    assert wargs.fn(wargs)["workers"]
    eargs = cli.build_parser().parse_args(["run", "export", "--db", db, "--run-id", "rcli"])
    exp = eargs.fn(eargs)
    assert exp["run"]["status"] == "completed" and len(exp["jobs"]) == 4


def test_cli_pause_immediate(tmp_path):
    plan = make_plan(str(tmp_path), n=2)
    db = os.path.join(tmp_path, "cp.db")
    lg = Ledger(db)
    r = Runner(lg, plan, [StubWorker("w", "h", ["target_base", "new_candidate"])],
               os.path.join(tmp_path, "cp"), clock=Counter())
    r.start("rcp")
    r.lease_one()
    lg.close()
    args = cli.build_parser().parse_args(["run", "pause", "--db", db, "--run-id", "rcp", "--immediate"])
    out = args.fn(args)
    assert out["state"] == "paused" and out["immediate"] is True
    lg2 = Ledger(db)
    assert not lg2.list_jobs("rcp", status="running")
    lg2.close()
