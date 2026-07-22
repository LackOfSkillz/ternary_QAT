# Changelog

Notable changes to this LineWright research fork. Dates are absolute; the active branch is
`linewright-experiments`.

## [Unreleased]

### Dispatch 24 continuation — first LIVE dual-GX10 execution completed (2026-07-22)

Ran the real base-vs-candidate fast battery on the two GX10 systems. **No training, no dataset
change, no empirical thresholds, no winner declared.**

- Provisioned `gx10-5611` over the jumbo inter-node link (image 19.7 GB, base model 7.6 GB,
  LoRA-20 adapter hash-verified); both endpoints passed a non-benchmark `READY` health check.
- Executed the frozen plan `lwdb-fast-v1-20260722` in `parallel_multi_host` (base @ gx10-9141,
  LoRA-20 candidate @ gx10-5611): **40/40 jobs, 0 integrity problems, mechanical replay
  identical → instrument-valid.**
- Scored all outputs (mechanical gates + Module-J slop + 2 corpus summaries) and built blind
  reviewer packets (44 identity-free absolute units incl. 4 hidden calibration seeds; 20
  pairwise; **0 identity leaks**). Preliminary signal: candidate degenerates far more than base
  (severe slop 9 vs 1; token-cap 9 vs 3; both surface arms fail → model/training, not compiler).
  **Advancement deferred to Dispatch 25.**
- Added the real HF generation worker + finalize pipeline; committed the completed run report,
  summary, compact item-level verdicts, corpus summaries, and provisioning record (raw outputs
  git-ignored). Superseded the preliminary report.

### Dispatch 24 — Fast battery construction & first dual-GX10 execution setup (2026-07-22)

Built and froze the first fast diagnostic battery and the full run pipeline; configured the
first execution as a dual-GX10 parallel run (base vs tuned candidate). **No model training,
no dataset change, no empirical thresholds, no winner declared.** The real dual-GX10 model
generation is execution-ready but was not run in this dispatch, so the verdict is
`insufficient_evidence` and advancement is deferred to Dispatch 25.

- **Fast battery v1** (`benchmarks/active-core/fast-v1/`): 20 benchmark items + 4 hidden
  grader-calibration seeds across modules A–J (J embedded), 7 controlled pair families
  (surface/restraint/canon/voice/length/constraint/turn), a locked behavior contract +
  provenance per item, and a frozen hashed manifest (`benchmarks/manifests/fast-battery-v1.yaml`).
  Synthetic, distributable, `benchmark_only`, excluded from training. Pre-run validation
  passes (max Dataset A/A.2 source overlap 51 chars).
- **Run pipeline** (`linewright/evaluation/battery/`): generation-plan builder (base +
  candidate share every benchmark-semantic hash), endpoint descriptors (secrets referenced,
  never serialized), mechanical + Module-J slop scoring per output + per-role corpus
  summaries, and blind reviewer packets (absolute-first, calibration-seeded, identity-stripped,
  content-shuffled — zero identity leaks).
- **First-run artifacts** (`benchmarks/runs/lwdb-fast-v1-20260722/`): frozen generation plan
  (40 jobs), endpoint manifest, run manifest (candidate = LoRA-20; QAT-20 excluded), real
  preflight health-check (both GX10s reachable; base host provisioned; candidate host has
  Python/torch, needs base+adapter+transformers/peft), and the preliminary report.
- **Added** the fast-battery manifest schema and 20 tests (construction, plan freezing,
  dual-GX10 routing, scoring, packets, invariants); `.gitignore` for bulky run outputs.

### Dispatch 23 — Instrument calibration, hardware-agnostic execution, durable pause/resume, slop foundation (2026-07-22)

Foundations that make the diagnostic battery trustworthy, portable, resumable, and
slop-aware. **No model training, no real model generation, no fast/full benchmark run, no
empirical capability floors, no validated slop thresholds, no Dataset A / A.2 change.**

- **Instrument calibration** (`linewright/evaluation/calibration/`): a hidden 12-kind
  grader-calibration set (`benchmarks/calibration/grader-calibration-set-v1.jsonl`) that
  dogfoods the Dispatch-21 gates; reviewer-reliability classification
  (`calibrated`/`conditionally_usable`/`unreliable_for_run`, **provisional/unvalidated**
  cutoffs); deterministic mechanical replay; and the instrument-valid rule (failed
  calibration → `insufficient_evidence`, findings quarantined).
- **Hardware-agnostic execution** (`linewright/evaluation/execution/`): frozen, hashed
  generation plan; normalized endpoint descriptors (secrets referenced, never serialized);
  deterministic stub workers; parallel and sequential modes proven to produce identical
  normalized results from one plan.
- **Durable pause/resume**: a versioned SQLite run ledger (runs/jobs/workers/events);
  graceful + immediate pause; controller-restart recovery; expired-lease recovery;
  output-integrity verification before skip; retry policy; `lwdb` CLI foundation.
- **Module J — slop detection** (`linewright/evaluation/slop/`): NOT an AI-authorship
  detector. Deterministic metrics (repetition, MATTR/MTLD/HD-D, sentence rhythm) implemented
  and versioned; semantic detectors **interface-only** (offline `NullSemanticDetector`,
  thresholds unvalidated); reviewer checklist; per-output slop report and per-run corpus
  summary that keep evidence families separate and never collapse to one score. A slop
  calibration set proves deliberate repetition / concise / lyrical known-good prose is not
  flagged.
- **Added** 14 schemas (execution-plan, endpoint-descriptor, run-state, job-state,
  worker-descriptor, worker-lease, retry-policy, pause-policy, normalized-generation-result,
  instrument-replay-result, slop-report, slop-detector-manifest, slop-reference-profile,
  slop-corpus-summary) + additive updates (anonymous-output, reviewer-calibration,
  benchmark-item Module J); **added** docs (research review, execution/resume, slop report)
  and updated README/ROADMAP/TRAINING_PILOT/architecture/evaluation guide; **added** 4 test
  files (slop, calibration, execution incl. pause/resume integration, docs invariants).


### Dispatch 22 — LineWright Diagnostic Battery architecture (2026-07-22)

Added the permanent evaluation-instrument **architecture** — the LineWright Model
Capability, Reliability, and Tuning Diagnostic Battery (LWDB). **Architecture only:** no
model training was performed, no benchmark prompts were generated, no numeric thresholds
were set, and the frozen Dataset A / Dataset A.2 corpora were not changed.

- **Added** the architecture specification
  `training/docs/linewright-diagnostic-battery-architecture-v1.md` (19 sections: purpose,
  non-goals, fast/full batteries, instrument calibration, capability modules, controlled
  pairs, prompt surfaces, mechanical & reviewer evaluation, confidence model, benchmark
  lifecycle, burned-item policy, reference-model calibration, checkpoint-curve testing,
  diagnosis-engine contract, roadmap, status, future boundaries).
- **Added** the machine-readable manifest
  `benchmarks/manifests/diagnostic-battery-architecture-v1.yaml` (no fabricated numeric
  performance thresholds).
- **Added** twelve field-contract schemas under `benchmarks/schemas/` (benchmark item,
  pair-family, behavior contract, model-role manifest, generation manifest, anonymous
  output, mechanical result, reviewer score, reviewer calibration, diagnostic finding,
  battery-run summary, benchmark provenance).
- **Added** the `benchmarks/` directory skeleton (`development/`, `active-core/`,
  `rotating/`, `reserve/`, `calibration/`, `burned/`, `manifests/`, `schemas/`) and its
  README.
- **Added** `docs/linewright-diagnostic-battery.md` (evaluation guide) and validation tests
  `tests/test_diagnostic_battery_architecture.py`.
- **Updated** `README.md` (battery section + link + status), `ROADMAP.md` (evaluation
  workstream, Dispatches 22–27, 22 marked current), and `TRAINING_PILOT.md` (fast/full
  battery timing, checkpoint-curve, burned-item flow, no-gradient rule).
- Builds on the Dispatch-21 hardened evaluation gates in `linewright/evaluation/`; does not
  recreate or bypass them.
