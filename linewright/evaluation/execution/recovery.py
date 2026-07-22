"""Controller-restart + worker-loss recovery (Dispatch 23, Workstreams C6/C8/C9).

Resume loads the frozen plan, verifies the plan hash and the ledger, reclaims expired
leases, verifies completed outputs, requeues interrupted jobs, and continues from the next
incomplete job — without the user reconstructing the original command line.
"""
from linewright.evaluation.execution import integrity
from linewright.evaluation.execution.plan import verify_plan_hash


def reclaim_and_requeue(ledger, run_id, now):
    """Reclaim expired leases (running/leased -> interrupted) then requeue interrupted."""
    reclaimed = ledger.reclaim_expired_leases(now)
    interrupted = ledger.list_jobs(run_id, status="interrupted")
    for j in interrupted:
        ledger.requeue_job(j["job_id"], now)
    return {"reclaimed_expired": reclaimed,
            "requeued_interrupted": [j["job_id"] for j in interrupted]}


def verify_completed(ledger, plan, run_id, output_dir, now):
    """Demote any completed job that fails integrity verification (completed -> interrupted)."""
    demoted = []
    for j in ledger.list_jobs(run_id, status="completed"):
        ok, reason = integrity.verify_completed_job(plan, j, output_dir)
        if not ok:
            ledger.demote_completed(j["job_id"], now, reason)
            demoted.append({"job_id": j["job_id"], "reason": reason})
    return demoted


def resume_prep(ledger, plan, run_id, output_dir, now):
    """Prepare a run for resume. Raises if the plan hash does not verify (benchmark semantics
    must not have changed silently)."""
    if not verify_plan_hash(plan):
        raise ValueError("plan hash does not verify; benchmark semantics changed — new run required")
    run = ledger.get_run(run_id)
    if not run or run["plan_hash"] != plan["plan_hash"]:
        raise ValueError("ledger plan_hash does not match the provided plan")
    ledger.set_run_state(run_id, "resuming", now, resumed_at=now)
    demoted = verify_completed(ledger, plan, run_id, output_dir, now)
    recl = reclaim_and_requeue(ledger, run_id, now)
    ledger.set_run_state(run_id, "running", now)
    return {"demoted_completed": demoted, **recl}
