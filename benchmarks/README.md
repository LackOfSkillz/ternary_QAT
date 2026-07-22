# LineWright Diagnostic Battery — benchmarks

Home of the **LineWright Model Capability, Reliability, and Tuning Diagnostic Battery**
(short: *LineWright Diagnostic Battery*, *LWDB*). This directory holds benchmark items,
schemas, and manifests. **Dispatch 22 defines the architecture only** — no benchmark
prompts, model outputs, or thresholds are created here yet. The item directories are
skeletons (`.gitkeep` only) until Dispatch 23+.

The battery is a **diagnostic instrument, not a ranking test**: it says which capability
changed, in which direction, with what effect size, on what evidence, and with what
confidence — not merely "Model A > Model B". See the full specification:
[`training/docs/linewright-diagnostic-battery-architecture-v1.md`](../training/docs/linewright-diagnostic-battery-architecture-v1.md).

## Directory structure (lifecycle)

```text
benchmarks/
  development/    items being authored / not yet candidate
  active-core/    stable items used every routine run (rotate over time)
  rotating/       items swapped in/out of the active set on a schedule
  reserve/        held-back items, NOT visible during dataset development
  calibration/    instrument-validation items (known-good / known-broken graders)
  burned/         items that influenced a dataset/training change (regression-only)
  manifests/      machine-readable architecture + battery manifests
  schemas/        field contracts for every battery artifact
```

## Item lifecycle

```text
development → candidate → active → used_for_measurement → used_for_diagnosis
            → burned → retired
```

An item that **directly informs** a dataset or training change becomes **burned**: it may
remain a regression check but no longer counts as independent evidence of improvement for
the change it inspired. `reserve/` items stay unseen during routine dataset development.

## Hard rules

1. **Benchmark items are excluded from training by construction** — they never enter
   gradients (every item schema requires `benchmark_only: true`).
2. Every item carries **provenance and usage history** (see
   `schemas/benchmark-provenance-schema.yaml`).
3. **Mechanical and reviewer evidence stay separate**; a strong subjective score never
   cancels a mechanical fatal flaw (Dispatch 21 gates in `linewright/evaluation/`).
4. **No numeric capability floor is invented before calibration** (Dispatch 23).

## Status

`architecture_only` — Dispatch 22. See the manifest:
[`manifests/diagnostic-battery-architecture-v1.yaml`](manifests/diagnostic-battery-architecture-v1.yaml).
