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
