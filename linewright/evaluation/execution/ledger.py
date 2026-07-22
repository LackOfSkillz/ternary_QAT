"""Durable SQLite run ledger (Dispatch 23, Workstream C2).

Transactional, inspectable, dependency-free (sqlite3 is stdlib). Completed jobs are
persisted immediately. Timestamps are numeric (caller-supplied ``now``) so tests are
deterministic and clock-independent; lease expiry is a numeric comparison. Migrations are
versioned via ``PRAGMA user_version``.
"""
import json
import sqlite3

SCHEMA_VERSION = 1

RUN_STATES = ("created", "validating", "running", "pause_requested", "paused", "resuming",
              "completed", "completed_with_failures", "cancelled", "failed")
JOB_STATES = ("pending", "leased", "running", "completed", "failed_retryable",
              "failed_terminal", "interrupted", "cancelled")


class Ledger:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def _migrate(self):
        v = self.conn.execute("PRAGMA user_version").fetchone()[0]
        if v < 1:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                  run_id TEXT PRIMARY KEY, plan_id TEXT, plan_hash TEXT, status TEXT,
                  execution_mode TEXT, controller_mode TEXT, created_at REAL, started_at REAL,
                  paused_at REAL, resumed_at REAL, completed_at REAL, failure_reason TEXT);
                CREATE TABLE IF NOT EXISTS jobs (
                  job_id TEXT PRIMARY KEY, run_id TEXT, benchmark_item_id TEXT, model_role TEXT,
                  status TEXT, attempt_count INTEGER DEFAULT 0, worker_id TEXT,
                  lease_expires_at REAL, input_hash TEXT, output_path TEXT, output_hash TEXT,
                  started_at REAL, completed_at REAL, last_error TEXT);
                CREATE TABLE IF NOT EXISTS workers (
                  worker_id TEXT PRIMARY KEY, host_id TEXT, endpoint_id TEXT, status TEXT,
                  current_job_id TEXT, last_heartbeat REAL, capabilities TEXT);
                CREATE TABLE IF NOT EXISTS events (
                  event_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, job_id TEXT,
                  event_type TEXT, timestamp REAL, details TEXT);
                """)
            self.conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
            self.conn.commit()

    def close(self):
        self.conn.close()

    # ---- runs ----
    def create_run(self, run_id, plan_id, plan_hash, execution_mode, controller_mode, now):
        self.conn.execute(
            "INSERT INTO runs (run_id, plan_id, plan_hash, status, execution_mode, "
            "controller_mode, created_at) VALUES (?,?,?,?,?,?,?)",
            (run_id, plan_id, plan_hash, "created", execution_mode, controller_mode, now))
        self.conn.commit()
        self.record_event(run_id, None, "run_created", now, {})

    def set_run_state(self, run_id, state, now, **stamps):
        assert state in RUN_STATES, state
        cols = ", ".join(f"{k}=?" for k in stamps)
        params = list(stamps.values())
        sql = "UPDATE runs SET status=?" + (", " + cols if cols else "") + " WHERE run_id=?"
        self.conn.execute(sql, [state] + params + [run_id])
        self.conn.commit()
        self.record_event(run_id, None, f"run_{state}", now, {})

    def get_run(self, run_id):
        r = self.conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        return dict(r) if r else None

    # ---- jobs ----
    def add_jobs(self, run_id, tuples, input_hashes=None):
        input_hashes = input_hashes or {}
        for item_id, role in tuples:
            job_id = f"{run_id}::{item_id}::{role}"
            self.conn.execute(
                "INSERT OR IGNORE INTO jobs (job_id, run_id, benchmark_item_id, model_role, "
                "status, input_hash) VALUES (?,?,?,?,?,?)",
                (job_id, run_id, item_id, role, "pending", input_hashes.get(item_id)))
        self.conn.commit()

    def get_job(self, job_id):
        r = self.conn.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        return dict(r) if r else None

    def list_jobs(self, run_id, status=None):
        if status:
            rows = self.conn.execute("SELECT * FROM jobs WHERE run_id=? AND status=? "
                                     "ORDER BY job_id", (run_id, status)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM jobs WHERE run_id=? ORDER BY job_id",
                                     (run_id,)).fetchall()
        return [dict(r) for r in rows]

    def counts(self, run_id):
        rows = self.conn.execute("SELECT status, COUNT(*) c FROM jobs WHERE run_id=? "
                                 "GROUP BY status", (run_id,)).fetchall()
        return {r["status"]: r["c"] for r in rows}

    def _set_job(self, job_id, now, event, **cols):
        assign = ", ".join(f"{k}=?" for k in cols)
        self.conn.execute(f"UPDATE jobs SET {assign} WHERE job_id=?",
                          list(cols.values()) + [job_id])
        self.conn.commit()
        j = self.get_job(job_id)
        self.record_event(j["run_id"], job_id, event, now, {"status": cols.get("status")})

    def lease_job(self, job_id, worker_id, now, lease_seconds):
        self._set_job(job_id, now, "job_leased", status="leased", worker_id=worker_id,
                      lease_expires_at=now + lease_seconds)

    def mark_running(self, job_id, now):
        self._set_job(job_id, now, "job_running", status="running", started_at=now)

    def complete_job(self, job_id, output_path, output_hash, now):
        # never overwrite an existing valid completed result silently
        j = self.get_job(job_id)
        if j["status"] == "completed" and j["output_hash"]:
            return False
        self._set_job(job_id, now, "job_completed", status="completed",
                      output_path=output_path, output_hash=output_hash,
                      completed_at=now, worker_id=j["worker_id"])
        return True

    def fail_job(self, job_id, error, retryable, now):
        state = "failed_retryable" if retryable else "failed_terminal"
        j = self.get_job(job_id)
        self._set_job(job_id, now, "job_" + state, status=state,
                      attempt_count=(j["attempt_count"] or 0) + 1, last_error=error)

    def interrupt_job(self, job_id, now, reason="interrupted"):
        self._set_job(job_id, now, "job_interrupted", status="interrupted",
                      last_error=reason, worker_id=None, lease_expires_at=None)

    def requeue_job(self, job_id, now):
        self._set_job(job_id, now, "job_requeued", status="pending", worker_id=None,
                      lease_expires_at=None)

    def cancel_job(self, job_id, now):
        self._set_job(job_id, now, "job_cancelled", status="cancelled")

    def demote_completed(self, job_id, now, reason):
        self._set_job(job_id, now, "job_integrity_failed", status="interrupted",
                      last_error=reason, output_hash=None)

    def reclaim_expired_leases(self, now):
        rows = self.conn.execute(
            "SELECT job_id FROM jobs WHERE status IN ('leased','running') "
            "AND lease_expires_at IS NOT NULL AND lease_expires_at < ?", (now,)).fetchall()
        reclaimed = [r["job_id"] for r in rows]
        for jid in reclaimed:
            self.interrupt_job(jid, now, reason="expired_lease")
        return reclaimed

    # ---- workers ----
    def upsert_worker(self, worker_id, host_id, endpoint_id, capabilities, now, status="idle"):
        self.conn.execute(
            "INSERT INTO workers (worker_id, host_id, endpoint_id, status, last_heartbeat, "
            "capabilities) VALUES (?,?,?,?,?,?) ON CONFLICT(worker_id) DO UPDATE SET "
            "host_id=excluded.host_id, endpoint_id=excluded.endpoint_id, status=excluded.status, "
            "last_heartbeat=excluded.last_heartbeat, capabilities=excluded.capabilities",
            (worker_id, host_id, endpoint_id, status, now, json.dumps(capabilities)))
        self.conn.commit()

    def heartbeat(self, worker_id, now, current_job_id=None, status="busy"):
        self.conn.execute("UPDATE workers SET last_heartbeat=?, current_job_id=?, status=? "
                          "WHERE worker_id=?", (now, current_job_id, status, worker_id))
        self.conn.commit()

    def list_workers(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM workers").fetchall()]

    # ---- events ----
    def record_event(self, run_id, job_id, event_type, now, details):
        self.conn.execute(
            "INSERT INTO events (run_id, job_id, event_type, timestamp, details) "
            "VALUES (?,?,?,?,?)", (run_id, job_id, event_type, now, json.dumps(details)))
        self.conn.commit()

    def events(self, run_id):
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM events WHERE run_id=? ORDER BY event_id", (run_id,)).fetchall()]
