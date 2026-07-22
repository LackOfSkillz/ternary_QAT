# Fast Battery v1 — First Execution: Preliminary Report (Dispatch 24)

Status: **battery frozen + validated; pipeline proven; real dual-GX10 generation
execution-ready and pending.** No model-quality finding is made — by construction, no
trusted run has completed, so the verdict is `insufficient_evidence` and advancement is
deferred to Dispatch 25.

> Experimental only. Not production. Not a certification. Seven-record-style caveats apply:
> a first fast run does not establish a capability floor or a winner.

## What is frozen and validated

- **Fast battery v1**: 20 benchmark items + 4 hidden grader-calibration seeds (24 total),
  all `benchmark_only` + `excluded_from_training`, synthetic distributable fiction only.
- **Coverage**: modules A–I present, **J embedded** (slop analysis on every prose output);
  7 controlled pair families (surface, restraint, canon, voice, length, constraint, turn);
  difficulty 20% easy / 45% moderate / 30% hard / 5% adversarial.
- **Locked behavior contracts** and **provenance** for every item; pre-run validation
  passed (`pre-run-validation-report.json`), max source overlap with Dataset A/A.2 = 51
  chars (incidental).
- **Frozen hashed manifest** `benchmarks/manifests/fast-battery-v1.yaml`; frozen
  `generation-plan.json` (plan_hash `a726365a…`, 40 jobs = 20 items × 2 roles) that verifies.

## Models

| role | model | revision | endpoint | host |
|---|---|---|---|---|
| target_base | prism-ml/Ternary-Bonsai-4B-unpacked | 4485fae… | ep-base (local_huggingface) | gx10-9141 |
| new_candidate | Ternary-Bonsai-4B-unpacked + LoRA step-20 | lora-step-20 | ep-candidate (local_huggingface) | gx10-5611 |

**Candidate selection basis** (`run-manifest.json`): the Dispatch-24 rule selects the most
recent technically-valid, non-catastrophic checkpoint with complete provenance. **QAT-20 is
excluded** (Dispatch-20/23 evidence: catastrophically degenerate, 0/7 mechanical). LoRA-20 is
the best available non-excluded candidate (4/7 mechanical; partially degenerate but not
catastrophic) and runs the fast path (base + adapter, no fake-quant). It is an experimental
smoke checkpoint — its selection is not a quality claim.

## Execution readiness (real preflight, 2026-07-22)

`preflight.json`:

- **Both GX10s reachable** over Tailscale; both **NVIDIA GB10**; a fast inter-node link
  (192.168.10.0/24, MTU 9000).
- **gx10-9141 (base)**: base model 7.6G, LoRA-20 adapter, docker image — **fully
  provisioned** for `target_base`.
- **gx10-5611 (candidate)**: 121 GB RAM, **Python 3.12 + torch 2.11 already present**; needs
  provisioning for `new_candidate` — base model (transfer over the inter-node link), the
  LoRA-20 adapter, `transformers`+`peft`, and the linewright/ternary code.
- **No model-serving endpoints are running**; the planned endpoint type is
  `local_huggingface` (in-process HF generation per node), matching the Dispatch-20 eval path.

Intended topology (dispatch primary): `parallel_multi_host` — base on gx10-9141,
candidate on gx10-5611, simultaneously, against the same frozen plan. Sequential
single-host remains the sanctioned fallback if a node/endpoint is unavailable.

## Instrument

- Mechanical scoring is deterministic and replayable (Dispatch 23); a replay mismatch would
  invalidate the run.
- The grader-calibration set dogfoods the gates (Dispatch 23: 9 broken rejected, 3 good
  accepted); reviewer-reliability classification mechanism is ready (provisional cutoffs).
- Instrument-valid rule enforced: trusted findings require mechanical replay + valid
  calibration set + ≥1 calibrated reviewer, else `insufficient_evidence` / findings
  quarantined.

## Completion (this dispatch)

- **Real model jobs generated: 0.** The dual-GX10 generation is execution-ready but was not
  run in this dispatch (it requires provisioning gx10-5611 and a multi-step run; it is set up
  to run against the exact frozen `plan_hash`).
- **Pipeline proven end-to-end with deterministic stub workers**: 40 jobs routed by role
  (base→gx10-9141, candidate→gx10-5611), completed, durably persisted; scored with mechanical
  gates + Module-J slop; 44 blind absolute review units built (40 outputs + 4 calibration
  seeds) with **zero identity leaks** and calibration indistinguishable; 20 pairwise packets
  with content-shuffled candidate order; corpus summaries per role.

## Preliminary findings

**None asserted.** Per the dispatch, this dispatch must not declare a winner, a capability
floor, or release readiness. With no trusted real run completed, the overall verdict is
**`insufficient_evidence`**, and the base-vs-candidate advancement decision is **deferred to
Dispatch 25** (diagnostic-engine validation) after a real run and blind review.

## Next steps (operator / follow-up)

1. Provision gx10-5611 (base model + LoRA-20 adapter + `transformers`/`peft` + code over the
   inter-node link).
2. Health-check both `local_huggingface` endpoints (model identity + a `READY` probe, not a
   benchmark item).
3. Execute the frozen plan `lwdb-fast-v1-20260722` in `parallel_multi_host`; on node loss,
   pause and resume or fall back to `sequential_single_host` (plan_hash unchanged).
4. Score, build blind packets (seed the 4 calibration items), run the three-reviewer blind
   pass + Gary, then hand comparable evidence to Dispatch 25.
