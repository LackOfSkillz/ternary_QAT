"""Threshold freeze + decision enforcement (Dispatch 25).

Thresholds are authored and COMMITTED before any Dispatch-25 analysis. This package loads
them, validates their metadata, hashes their content, verifies they are committed and
unmodified, and writes/verifies a lock record. Analysis and the branch decision refuse to run
unless the lock is valid — so thresholds cannot move after results are inspected.
"""
RESEARCH_THRESHOLD = "benchmarks/thresholds/research-continuation-v0.yaml"
STARTER_THRESHOLD = "benchmarks/thresholds/starter-model-acceptance-v0.yaml"
LOCK_PATH = "benchmarks/thresholds/threshold-lock-v0.json"
