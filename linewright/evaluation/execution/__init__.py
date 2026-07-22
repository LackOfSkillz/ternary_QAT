"""Hardware-agnostic, durable battery execution (Dispatch 23, Workstreams B + C).

Parallel and sequential execution are SEMANTICALLY EQUIVALENT: both consume one frozen,
hashed generation plan and emit the same normalized results; only scheduling and wall-clock
differ. Run state is durable in a SQLite ledger so a run survives pause, shutdown, network
changes, and worker loss, and resumes without rerunning completed jobs. The atomic durable
unit is one model role x one benchmark item x one generation config = one job.
"""
