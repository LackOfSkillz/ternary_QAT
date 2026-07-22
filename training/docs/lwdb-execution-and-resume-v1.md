# LWDB Execution & Resume (v1)

How the LineWright Diagnostic Battery runs — portably across dual-model and single-model
hardware — and survives pauses, shutdowns, network changes, and worker loss. Implemented in
[`linewright/evaluation/execution/`](../../linewright/evaluation/execution/). Dispatch 23
does not execute a real fast battery; the orchestration is exercised end-to-end with
deterministic stub workers.

## 1. Execution modes

`parallel_multi_host`, `parallel_single_host`, `sequential_single_host`,
`sequential_multi_host`. All modes consume the **same frozen plan** and produce the **same
normalized results**; only scheduling and wall-clock differ. Users never need two
high-memory machines to reproduce the benchmark.

## 2. Frozen generation plan

`plan.create_plan(...)` builds a plan and hashes it. The `plan_hash` covers benchmark
semantics — item prompts, behavior contracts, model descriptors/revisions, generation
settings, seeds, token limits — and **excludes** `execution_mode`, `scheduling_policy`,
timing, `plan_id`, and the output directory (so the same plan runs parallel *or* sequential
with an identical hash). A changed plan no longer verifies (`verify_plan_hash`) and requires
a **new plan_id + plan_hash + run_id**. Secrets are never serialized (a secret-like field
raises).

## 3. Endpoint configuration

`endpoint-descriptor-schema`: `openai_compatible_http`, `local_huggingface`,
`local_subprocess`, `test_stub`. API keys are referenced by env/secret name
(`authentication_source: ENV:NAME`) — never stored literally. `unsupported_parameters`
lets the planner reject (terminally) a plan needing a parameter an endpoint cannot honor.

## 4. SQLite ledger

`ledger.Ledger` (stdlib `sqlite3`, WAL, `PRAGMA user_version` migrations). Tables: `runs`,
`jobs`, `workers`, `events`. Timestamps are numeric (caller-supplied) so tests are
clock-independent; lease expiry is a numeric comparison. Completed jobs are persisted
**immediately** — the run never waits for the whole queue to save.

## 5. Run & job state machines

Run: `created → validating → running → pause_requested → paused → resuming → completed |
completed_with_failures | cancelled | failed`. Job:
`pending → leased → running → completed | failed_retryable | failed_terminal | interrupted |
cancelled`. See `benchmarks/schemas/run-state-schema.yaml` and `job-state-schema.yaml`; no
ambiguous states.

## 6. Graceful pause

Stops new assignment, lets active generations finish, persists completed results, flushes
logs/db, releases/expires leases cleanly, enters `paused`, preserves every completed job.
`Runner.pause_graceful()` / `lwdb run pause <id>`.

## 7. Immediate pause

Stops new assignment, attempts to cancel active requests, marks incomplete active jobs
`interrupted`, preserves completed jobs, enters `paused`. `Runner.pause_immediate()` /
`lwdb run pause <id> --immediate`. An interrupted generation restarts from the beginning of
that one item on resume.

## 8. Resume verification

`recovery.resume_prep`: load the frozen plan, verify the plan hash, verify the ledger's
plan_hash, verify completed output files/hashes, requeue interrupted jobs, reclaim expired
leases, and continue. `Runner.resume()`. The user does not reconstruct the original command
line — the ledger holds the plan reference and state.

## 9. Worker leases

Workers lease jobs and heartbeat (`worker-lease-schema`). On controller start, a
running/leased job whose `lease_expires_at` has passed becomes `interrupted → pending`. A
lost worker never strands a job.

## 10. Network-change behavior

The run does not depend on the client laptop keeping the same IP. Reconnecting workers
resume leasing; state lives in the ledger, not the client.

## 11. Persistent remote controller

The coordinator stays on a persistent host (e.g. a GX10). Closing the laptop or changing
networks does not stop workers — the laptop is a control client only.

## 12. Local resumable controller

The controller stops with the laptop; a later restart restores the run from the SQLite
ledger and continues without rerunning completed jobs. (The Dispatch-23 integration test
models exactly this: pause → close ledger → fresh `Ledger`+`Runner` on the same db → resume
→ finish, with no completed job rerun.)

## 13. Retry policy

`retry.RetryPolicy` (bounded `max_attempts`). Retryable: transient network, worker
disconnect, endpoint timeout, expired lease, controller interruption. Terminal/manual:
invalid plan, model-revision/prompt-hash mismatch, unsupported required parameter, repeated
OOM, invalid result schema. `attempt_count` is recorded; a retry never overwrites a valid
completed result.

## 14. Output integrity

Before resume skips a completed job (`integrity.verify_completed_job`): result record +
output file exist, output hash matches, item + behavior-contract + generation-settings
hashes match the frozen plan, model-role matches, record structurally complete. Any failure
demotes `completed → interrupted`. Never silently trust a missing/corrupted output.

## 15. Single-machine model switching

Sequential single-host: complete part of one model role's queue, pause, unload/switch the
served model, resume the same run, complete the other role — both result sets feed the same
anonymization + scoring pipeline. (`test_sequential_model_switch_preserves_run`.)

## 16. Dual-GX10 parallel setup

Two workers (`base_worker → target_base`, `candidate_worker → new_candidate`) process their
queues simultaneously against the same frozen plan. Partial completion on either worker
remains resumable.

**First-run topology (Dispatch 24, `benchmarks/runs/lwdb-fast-v1-20260722/`):**

```
GX10 A (gx10-9141, 100.92.130.112) → target_base    (prism-ml/Ternary-Bonsai-4B-unpacked)
GX10 B (gx10-5611, 100.97.81.71)   → new_candidate  (base + LoRA step-20 adapter)
```

Both endpoints are `local_huggingface` (in-process HF generation per node — no HTTP server,
no serialized secrets). The base host is fully provisioned; the candidate host has Python +
torch and needs the base model (transfer over the 192.168.10.0/24 jumbo link), the adapter,
`transformers`/`peft`, and the code. If a node is unavailable, pause and resume or fall back
to `sequential_single_host` — the `plan_hash` is unchanged.

## 17. Limitations of mid-generation recovery

Recovery is **item-level, not token-level**. We do NOT claim arbitrary inference backends
can preserve and restore a partially generated KV cache; an interrupted generation restarts
that one item from the beginning.

## CLI

`lwdb plan create | run start | run status | run pause [--immediate] | run resume | run
cancel | run verify | run retry-failed | run export | worker status`
([`cli.py`](../../linewright/evaluation/execution/cli.py)). `run start`/`run resume` require
configured workers/endpoints; the Runner API is used directly (with stub workers) in tests.
