"""``lwdb`` run-control CLI foundation (Dispatch 23, Workstream C11).

Deterministic-stub-testable command surface for run control. Dispatch 23 does not execute a
real fast battery, but the orchestration layer is exercisable end-to-end with stub workers.
The user never has to reconstruct the original command line to resume — the ledger holds the
plan reference and state.

Commands:
  lwdb plan create --spec <json> --out <plan.json>
  lwdb run start   --db <ledger.db> --plan <plan.json> --run-id <id> [--output-dir DIR]
  lwdb run status  --db <ledger.db> --run-id <id>
  lwdb run pause   --db <ledger.db> --run-id <id> [--immediate]
  lwdb run resume  --db <ledger.db> --plan <plan.json> --run-id <id> [--output-dir DIR]
  lwdb run cancel  --db <ledger.db> --run-id <id>
  lwdb run verify  --db <ledger.db> --plan <plan.json> --run-id <id> [--output-dir DIR]
  lwdb run retry-failed --db <ledger.db> --run-id <id>
  lwdb run export  --db <ledger.db> --run-id <id> [--out <json>]
  lwdb worker status --db <ledger.db>
"""
import argparse
import json

from linewright.evaluation.execution.ledger import Ledger
from linewright.evaluation.execution import recovery


def _ledger(args):
    return Ledger(args.db)


def cmd_run_status(args):
    lg = _ledger(args)
    out = {"run": lg.get_run(args.run_id), "job_counts": lg.counts(args.run_id)}
    lg.close()
    return out


def cmd_run_pause(args):
    lg = _ledger(args)
    now = _peek_now(lg)
    lg.set_run_state(args.run_id, "pause_requested", now)
    if args.immediate:
        for st in ("leased", "running"):
            for j in lg.list_jobs(args.run_id, status=st):
                lg.interrupt_job(j["job_id"], now, reason="immediate_pause")
    lg.set_run_state(args.run_id, "paused", now, paused_at=now)
    out = {"run_id": args.run_id, "state": "paused", "immediate": bool(args.immediate)}
    lg.close()
    return out


def cmd_run_cancel(args):
    lg = _ledger(args)
    now = _peek_now(lg)
    for st in ("pending", "leased", "running", "interrupted", "failed_retryable"):
        for j in lg.list_jobs(args.run_id, status=st):
            lg.cancel_job(j["job_id"], now)
    lg.set_run_state(args.run_id, "cancelled", now)
    lg.close()
    return {"run_id": args.run_id, "state": "cancelled"}


def cmd_run_verify(args):
    lg = _ledger(args)
    plan = json.load(open(args.plan, encoding="utf-8"))
    now = _peek_now(lg)
    demoted = recovery.verify_completed(lg, plan, args.run_id, args.output_dir, now)
    lg.close()
    return {"run_id": args.run_id, "demoted_completed": demoted,
            "verified_ok": not demoted}


def cmd_run_retry_failed(args):
    lg = _ledger(args)
    now = _peek_now(lg)
    requeued = []
    for j in lg.list_jobs(args.run_id, status="failed_retryable"):
        lg.requeue_job(j["job_id"], now)
        requeued.append(j["job_id"])
    lg.close()
    return {"run_id": args.run_id, "requeued": requeued}


def cmd_run_export(args):
    lg = _ledger(args)
    data = {"run": lg.get_run(args.run_id), "jobs": lg.list_jobs(args.run_id),
            "events": lg.events(args.run_id)}
    lg.close()
    if getattr(args, "out", None):
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    return data


def cmd_worker_status(args):
    lg = _ledger(args)
    out = {"workers": lg.list_workers()}
    lg.close()
    return out


def cmd_plan_create(args):
    from linewright.evaluation.execution.plan import create_plan
    spec = json.load(open(args.spec, encoding="utf-8"))
    plan = create_plan(**spec)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(plan, fh, ensure_ascii=False, indent=2)
    return {"plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"], "out": args.out}


def _peek_now(lg):
    # a coarse monotonic tick derived from the event count keeps CLI actions ordered without
    # a wall clock (the real timing is not part of any hash).
    row = lg.conn.execute("SELECT COALESCE(MAX(timestamp),0)+1 t FROM events").fetchone()
    return row["t"]


def build_parser():
    p = argparse.ArgumentParser(prog="lwdb")
    sub = p.add_subparsers(dest="group", required=True)

    plan = sub.add_parser("plan").add_subparsers(dest="cmd", required=True)
    pc = plan.add_parser("create"); pc.add_argument("--spec", required=True); pc.add_argument("--out", required=True)
    pc.set_defaults(fn=cmd_plan_create)

    run = sub.add_parser("run").add_subparsers(dest="cmd", required=True)
    for name in ("status", "pause", "cancel", "verify", "resume", "start", "retry-failed", "export"):
        sp = run.add_parser(name)
        sp.add_argument("--db", required=True)
        sp.add_argument("--run-id", required=True, dest="run_id")
        sp.add_argument("--plan", required=False)
        sp.add_argument("--output-dir", dest="output_dir", default=None)
        if name == "pause":
            sp.add_argument("--immediate", action="store_true")
        if name == "export":
            sp.add_argument("--out", required=False)
    run.choices["status"].set_defaults(fn=cmd_run_status)
    run.choices["pause"].set_defaults(fn=cmd_run_pause)
    run.choices["cancel"].set_defaults(fn=cmd_run_cancel)
    run.choices["verify"].set_defaults(fn=cmd_run_verify)
    run.choices["retry-failed"].set_defaults(fn=cmd_run_retry_failed)
    run.choices["export"].set_defaults(fn=cmd_run_export)
    run.choices["start"].set_defaults(fn=lambda a: {"note": "run start requires configured "
                                                    "workers/endpoints; use the Runner API or "
                                                    "a stub worker in tests"})
    run.choices["resume"].set_defaults(fn=lambda a: {"note": "run resume requires configured "
                                                     "workers; use the Runner API or a stub in tests"})

    wk = sub.add_parser("worker").add_subparsers(dest="cmd", required=True)
    ws = wk.add_parser("status"); ws.add_argument("--db", required=True)
    ws.set_defaults(fn=cmd_worker_status)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    result = args.fn(args)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
