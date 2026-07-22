# Changelog

Notable changes to this LineWright research fork. Dates are absolute; the active branch is
`linewright-experiments`.

## [Unreleased]

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
