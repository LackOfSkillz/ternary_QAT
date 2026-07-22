"""Run orchestration (Dispatch 23, Workstreams B/C).

The Runner leases jobs to workers, executes them, and persists each completed result
IMMEDIATELY (job by job). It supports graceful and immediate pause, and resume via the
recovery module. Parallel and sequential scheduling produce identical normalized results
from the deterministic stub workers; only worker assignment and order differ.

A monotonic injectable clock keeps tests deterministic and clock-independent.
"""
from linewright.evaluation.execution import integrity, recovery
from linewright.evaluation.execution.plan import job_tuples
from linewright.evaluation.execution.worker import normalized_result

_ACTIVE = ("pending", "leased", "running", "interrupted", "failed_retryable")


class Counter:
    def __init__(self, start=1):
        self._n = start

    def __call__(self):
        v = self._n
        self._n += 1
        return v


class Runner:
    def __init__(self, ledger, plan, workers, output_dir, lease_seconds=1000, clock=None,
                 controller_mode="local_resumable"):
        self.ledger = ledger
        self.plan = plan
        self.workers = list(workers)
        self.output_dir = output_dir
        self.lease_seconds = lease_seconds
        self.clock = clock or Counter()
        self.controller_mode = controller_mode
        self.run_id = None
        self._paused = None

    def _now(self):
        return self.clock()

    # ---- lifecycle ----
    def start(self, run_id):
        self.run_id = run_id
        now = self._now()
        self.ledger.create_run(run_id, self.plan["plan_id"], self.plan["plan_hash"],
                               self.plan["execution_mode"], self.controller_mode, now)
        self.ledger.add_jobs(run_id, job_tuples(self.plan), input_hashes=self.plan["item_hashes"])
        for w in self.workers:
            self.ledger.upsert_worker(w.worker_id, w.host_id, w.endpoint_id,
                                      {"model_roles": w.roles}, now)
        self.ledger.set_run_state(run_id, "running", now, started_at=now)

    def _role_order(self):
        if self.plan.get("scheduling_policy") == "model_sequential":
            return list(self.plan["model_roles"])
        return None  # round-robin / fifo

    def _next_pending(self, roles):
        pend = self.ledger.list_jobs(self.run_id, status="pending")
        order = self._role_order()
        if order:
            pend.sort(key=lambda j: (order.index(j["model_role"]) if j["model_role"] in order
                                     else 99, j["job_id"]))
        else:
            pend.sort(key=lambda j: j["job_id"])
        for j in pend:
            if j["model_role"] in roles:
                return j
        return None

    def lease_one(self, worker=None):
        """Lease + mark running ONE job without executing (used for immediate-pause tests)."""
        worker = worker or self.workers[0]
        j = self._next_pending(worker.roles)
        if not j:
            return None
        now = self._now()
        self.ledger.lease_job(j["job_id"], worker.worker_id, now, self.lease_seconds)
        self.ledger.mark_running(j["job_id"], now)
        self.ledger.heartbeat(worker.worker_id, now, j["job_id"])
        return j["job_id"]

    def _execute(self, worker, job):
        item_id, role = job["benchmark_item_id"], job["model_role"]
        started = self._now()
        self.ledger.lease_job(job["job_id"], worker.worker_id, started, self.lease_seconds)
        self.ledger.mark_running(job["job_id"], started)
        gen = worker.generate(self.plan, item_id, role)
        completed = self._now()
        result = normalized_result(self.plan, self.run_id, job["job_id"], item_id, role, gen,
                                   worker, self.plan["execution_mode"], started, completed)
        path = integrity.write_result(self.output_dir, job["job_id"], result)
        self.ledger.complete_job(job["job_id"], path, result["output_hash"], completed)
        return job["job_id"]

    def _step(self):
        """Assign + execute at most one job per idle worker. Returns # executed."""
        executed = 0
        for w in self.workers:
            j = self._next_pending(w.roles)
            if j:
                self._execute(w, j)
                executed += 1
        return executed

    def run(self, pause_after_completed=None, pause_mode="graceful"):
        done = 0
        while not self._paused:
            self.ledger.reclaim_expired_leases(self._now())
            n = self._step()
            if n == 0:
                break
            done += n
            if pause_after_completed and done >= pause_after_completed:
                self.request_pause(pause_mode)
                return
        self._maybe_finalize()

    # ---- pause / resume ----
    def request_pause(self, mode="graceful"):
        now = self._now()
        self.ledger.set_run_state(self.run_id, "pause_requested", now)
        if mode == "immediate":
            for st in ("leased", "running"):
                for j in self.ledger.list_jobs(self.run_id, status=st):
                    self.ledger.interrupt_job(j["job_id"], now, reason="immediate_pause")
        self.ledger.set_run_state(self.run_id, "paused", now, paused_at=now)
        self._paused = mode

    def pause_graceful(self):
        self.request_pause("graceful")

    def pause_immediate(self):
        self.request_pause("immediate")

    def resume(self):
        now = self._now()
        info = recovery.resume_prep(self.ledger, self.plan, self.run_id, self.output_dir, now)
        self._paused = None
        self.run()
        return info

    def _maybe_finalize(self):
        c = self.ledger.counts(self.run_id)
        if any(c.get(s) for s in _ACTIVE):
            return
        now = self._now()
        state = "completed_with_failures" if c.get("failed_terminal") else "completed"
        self.ledger.set_run_state(self.run_id, state, now, completed_at=now)

    def cancel(self):
        now = self._now()
        for st in ("pending", "leased", "running", "interrupted", "failed_retryable"):
            for j in self.ledger.list_jobs(self.run_id, status=st):
                self.ledger.cancel_job(j["job_id"], now)
        self.ledger.set_run_state(self.run_id, "cancelled", now)

    def status(self):
        return {"run": self.ledger.get_run(self.run_id),
                "job_counts": self.ledger.counts(self.run_id)}
