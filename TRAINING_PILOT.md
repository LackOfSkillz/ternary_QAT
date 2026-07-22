# Training Pilot

Three staged runs prove the LineWright starter-model pipeline before any scaled
training. All values here are **provisional** and subject to the feasibility
gates and thresholds defined in [`ROADMAP.md`](ROADMAP.md). No run in this
document is a production training job.

Run 1 uses **one GX10 only** to minimize debugging complexity. The second GX10 is
available for dataset generation and evaluation in the meantime, but it is **not**
permanently reserved for support work: after Run 1, a single-node versus dual-node
throughput benchmark decides whether later long runs use one or both nodes.

## Run 1: Pipeline smoke test

- **Base:** `prism-ml/Ternary-Bonsai-4B-unpacked`
- **Method:** conventional LoRA
- **Dataset:** 50–100 synthetic examples
- **Benchmark:** 20–30 held-out examples
- **Maximum training duration:** approximately 50–200 steps
- **Objective:** prove the full mechanical pipeline — load, train, save, merge,
  export to GGUF, quantize (Q2_0), reload the final artifact, and evaluate.
- **Not** expected to prove any meaningful quality improvement. Success is
  defined purely as the pipeline completing end to end without error and the
  final packed artifact reloading and producing valid output.

## Single-node versus dual-node scaling benchmark

Run 1 uses one GX10 to minimize debugging complexity.

After Run 1 completes successfully, run a controlled throughput benchmark using:

1. One GX10
2. Both GX10s with data parallelism or DDP

The comparison must use the same:

- Base model
- Dataset
- Sequence length
- Number of training tokens
- Precision
- LoRA configuration
- Optimizer
- Effective global batch size where practical

Record:

- Training tokens per second
- Examples per second
- Seconds per optimizer step
- Peak unified-memory use per node
- GPU utilization per node
- NCCL communication time
- Checkpoint-write time
- Total elapsed time for a fixed number of training tokens

Use both GX10s for subsequent long-running jobs only when dual-node operation
provides a meaningful throughput improvement without instability.

The initial distributed method should be data parallelism or DDP. Do not
introduce model sharding unless a future workload cannot fit comfortably on one
GX10.

## Run 2: Small behavioral baseline

- **Base:** `prism-ml/Ternary-Bonsai-4B-unpacked`
- **Dataset:** approximately 300–500 reviewed synthetic examples
- **Method:** conventional LoRA
- **Required tasks:**
  - canon extraction
  - hard-constraint checking
  - focused anti-slop revision
  - fiction-permissive compliance
- **Evaluation:** measure both the untouched base and the final Q2_0 artifact on
  the held-out benchmark, per Required-tier and Optional-tier capability, using
  the precommitted procedures from `ROADMAP.md`.

## Run 3: Ternary-QAT comparison

- **Base:** same as Run 2 (`prism-ml/Ternary-Bonsai-4B-unpacked`)
- **Dataset:** same as Run 2
- **Split:** same as Run 2
- **Benchmark:** same as Run 2
- **Training budget:** similar to Run 2
- **Method:** ternary QAT (via `swap_linear()` fake-quant during training)
- **Comparison:** compare the **final Q2_0 artifacts** of the conventional-LoRA
  path (Run 2) and the ternary-QAT path. Retain QAT only if it yields a
  meaningful, repeatable gain on the same benchmark.

## Ordering and gates

Run 1 must pass (pipeline completes) before Run 2. Run 2 establishes the
conventional-LoRA baseline that Run 3 is measured against. No run proceeds to
scaled data before a PASS or qualifying PARTIAL feasibility result, per
`ROADMAP.md`.

## Diagnostic battery — training workflow

Every meaningful tuning experiment is evaluated with the **LineWright Diagnostic
Battery** (LWDB). Architecture:
[`training/docs/linewright-diagnostic-battery-architecture-v1.md`](training/docs/linewright-diagnostic-battery-architecture-v1.md)
(status `architecture_only` — no prompts or thresholds exist yet).

- **When the fast battery runs:** after each meaningful checkpoint, and across the
  25/50/75/100% checkpoint curve of a run, to catch catastrophic regressions and early
  overfitting and to decide whether a candidate earns the full battery.
- **When the full battery runs:** major dataset-version decisions, base-model selection,
  quantization changes, release candidates, and final checkpoint certification.
- **Checkpoint-curve expectations:** report earliest meaningful improvement, peak
  checkpoint, onset of regression, and capability-specific peaks — as **fractions**, never
  a fixed step count. Long-form prose and protocol compliance may peak at different points.
- **Evaluation → dataset changes:** findings feed dataset revision (coverage/balance) via
  the Dispatch-21 pilot workflow. When a benchmark item **directly informs** a dataset or
  training change it becomes **burned**: it may stay a regression check but no longer counts
  as independent evidence of improvement for the change it inspired.
- **Benchmark records never enter gradients:** every item is `benchmark_only: true` and is
  excluded from training by construction. Author content is likewise never a gradient input
  (inference-time context only). A model may not advance on lower loss or a higher parse
  rate — only on the battery's confidence-tagged findings and the reviewer advancement rule.

### Slop reports, checkpoint curves, and execution (Dispatch 23)

- **Fast and full runs require slop reports** (Module J): a per-output slop report plus a
  per-run corpus summary. Slop reports **never enter gradients**, and the grader/slop
  calibration items remain excluded from training.
- **Checkpoint-curve evaluation includes slop trends.** A checkpoint may improve protocol
  compliance while *worsening* slop; the curve reports both. Slop findings can implicate
  dataset coverage/balance, training duration, context compilation, decoding, or base-model
  capacity — but a causal cause still requires matched (pair/surface) evidence.
- **Parallel and sequential runs use the same frozen plan** and produce the same normalized
  results; pause/resume does not alter benchmark semantics (the `plan_hash` is verified on
  resume). See [`lwdb-execution-and-resume-v1.md`](training/docs/lwdb-execution-and-resume-v1.md).
- **Instrument-first:** a run produces trusted findings only after the instrument validates
  (mechanical replay + calibration set + ≥1 calibrated reviewer); otherwise the verdict is
  `insufficient_evidence` and findings are quarantined.

### First fast-battery execution (Dispatch 24)

- The **first execution ran as a live dual-GX10 parallel run**: the untouched base on
  `gx10-9141` and the tuned LoRA-20 candidate on `gx10-5611`, both consuming the **same frozen
  generation plan** (`benchmarks/runs/lwdb-fast-v1-20260722/`) — 40/40 jobs completed,
  0 integrity problems, mechanical replay identical (instrument-valid). Preliminary signal
  (not a verdict, deferred to Dispatch 25): the candidate degenerates markedly more than the
  base; both share a structured-protocol weakness.
- **Sequential single-host remains the fallback** if a GX10 or endpoint is unavailable; the
  `plan_hash` is unchanged across modes (execution mode is not benchmark semantics).
- **Pause/resume is supported during the real run**; completed jobs are durably persisted and
  never rerun.
- **Fast-battery results do not automatically trigger dataset changes**, and no item is burned
  merely by being measured — burning requires an item to directly inform a change.
- **Reviewer results precede model advancement**: a candidate advances only via the blind
  three-reviewer pass + Gary and the Dispatch-21 advancement rule, never on loss or parse
  rate. QAT-20 is excluded as a candidate (catastrophically degenerate); the first candidate
  is LoRA-20.

### Dispatch 25 branch decision (thresholds frozen first)

- Provisional research thresholds are **authored and committed before any interpretation**
  (agent-proposed under Gary's delegated authority, immutably locked; not a final ship gate).
  A decision is stamped with the locked threshold hashes and invalidated by any post-lock change.
- Applying the frozen threshold to the live run + an existing-checkpoint curve + a dataset audit,
  the branch is **`test_stronger_base`**: the untouched base fails the core-prose feasibility
  floor, no LoRA checkpoint improves over it (step-10 neutral, step-20 collapses), and a dataset
  cannot fix base capacity. **No training was started; Dataset A / A.2 unchanged; LoRA-20 not
  continued.** The next experiment (a stronger-base comparison, one controlled variable) is in
  `training/specs/next-linewright-experiment-v1.md` but not launched. Full-battery prose quality
  remains a blind-reviewer judgement that is still pending.

### Dispatch 26 stronger-base comparison (base = only changed variable)

- Ran the `test_stronger_base` branch as a controlled three-model comparison — **Qwen3-8B**
  (non-thinking) and **Ministral-3-8B-Instruct-2512** (FP8, text-only) vs the 4B control, 94 real
  GX10 jobs (0 integrity problems, mechanical replay identical). **No training, no dataset change,
  no threshold change.** Applying the frozen 0.50 core-prose floor unchanged: **Qwen3 0.857 and
  Ministral 0.714 both clear it; the 4B failed (0.286)** — confirming base capacity was the
  bottleneck. Qwen3 clears every frozen floor; Ministral fails module-coverage.
- Blind, calibrated reviewers marginally prefer Ministral's raw prose (3.07 vs Qwen 2.79) while
  Qwen leads instruction-compliance; Qwen has the mature 8GB GGUF path (Ministral's unverified).
  Branch: **`run_one_bounded_confirmation`, presumptive foundation Qwen3-8B** — a bounded
  human/quantized blind prose confirmation precedes any foundation commit. Voice-preservation is
  weak across ALL bases (~2.7–2.9/5) and becomes a fine-tune target once the base is fixed.
