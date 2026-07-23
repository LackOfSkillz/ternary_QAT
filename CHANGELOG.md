# Changelog

Notable changes to this LineWright research fork. Dates are absolute; the active branch is
`linewright-experiments`.

## [Unreleased]

### Dispatch 28A — Build + freeze the LineWright Prompt-Execution pilot instrument (2026-07-23)

Constructed and froze a new, audit-grade pilot instrument that tests whether a structured
LineWright contract makes a small model execute fiction-writing instructions more reliably than
strong natural-language prompting. **Construction + freeze ONLY** — no generation, no scoring, no
review, no decision, no training, no QAT, no Dataset A.3 expansion, `master` untouched. Built in its
own directory `benchmarks/linewright-prompt-execution-v1/`; the Dispatch-28
`linewright-prompt-effect-v1` pilot is preserved unchanged as provisional evidence-of-record.

- **Frozen-first sequence** (each committed before the next): author + validate + freeze the task
  layer (`98048fa`) → render + validate + freeze the prompt layer (`c7af6c3`).
- **30 FRESH tasks** (12 focused-revision / 5 protected-text / 4 no-change / 3 canon / 3 voice / 2
  scene / 1 structured), original to this instrument — validated to have **zero overlap** with
  Dataset A/A.2/A.3 **or** the Dispatch-28 benchmark (10-gram shingle scan). Focused-revision
  instruction positions **4 early / 4 middle / 4 late**, critical-instruction type rotated 4×3.
  Every required change / protected element / unaffected span keys on an **exact substring**; a
  deterministic typed check evaluator is the single source of truth (no LLM grader for primary
  correctness). 6 comprehension probes.
- **Leakage separation:** each task splits `compiler_inputs` (the only block a future application
  compiler may receive) from `evaluation_ground_truth` + `machine_checks`, asserted by the validator
  — so a later P3-Compiled arm cannot see the answers.
- **100 prompts:** P0-Realistic 30 (casual, with omission inventory), P0-Maximal 30 (exhaustive NL),
  P1-Contract 30 (canonical contract), P3-Ideal 10 (hand-built theoretical ceiling, labeled
  non-product). **P3-Compiled deferred** (the real compiler lives in the application project; no
  re-implementation or simulation permitted). **P0-Maximal ≡ P1-Contract information equivalence
  verified 30/30.** Every record `generation_authorized: false`.
- 17 Dispatch-28A tests (task layer, prompt layer, no-generation/no-outputs, repo invariants); full
  suite 393 passed / 1 skipped / 1 pre-existing peft-env failure; Gate 0 zero drift. Future
  generation (30×3 + 10 = 100 outputs) requires a new, separately-authorized dispatch.

### Dispatch 28 — LineWright Prompt Effect Pilot (2026-07-22)

Tested LineWright's product thesis directly: does compiling ordinary author intent into a
structured fiction-writing packet fix the multi-constraint focused-revision failure better than
the neutral Dispatch-27 LoRA? **No training, no QAT, no dataset change, no threshold change, no
weights published, `master` untouched.** Frozen-first: 30 benchmark-only tasks (deterministic
grounded machine checks) → freeze → 4 prompt arms → freeze (P0-Maximal ≡ P1-Contract
information-equivalence verified) → generation → mechanical scoring → blind soft review →
decision, each stage committed before the next.

- **Arms** (Qwen3-8B non-thinking, greedy, seed 20260722, 100 outputs, 0 reasoning leaks / 0 token
  caps): P0-Realistic (casual), P0-Maximal (every requirement, unstructured), P1-Contract (same
  info, structured), P3-Ideal (hand-built ceiling, 10 tasks). P3-Compiled dropped — no real
  compiler in this fork.
- **Mechanical (focused-revision, all-required-completed):** P0-Realistic **0.083** → P0-Maximal
  0.667 → P1-Contract 0.500 → P3-Ideal **0.750**. Headline: **P1−P0-Realistic +0.20** (whole
  product), **P1−P0-Maximal −0.067** (structure alone at equal info adds no *completion*),
  **P3-Ideal−P1 +0.30**. Returned-unchanged 0.167→0.0. **The Dispatch-27 LoRA gave 0.0 on this
  exact failure** — prompt architecture ≫ weight tuning here.
- **Structure's realized value = scope discipline:** P1-Contract is the only mechanically spotless
  arm (0 returned-unchanged / 0 unauthorized / 0 protected-corruption).
- **Blind soft review** (arm-hidden, two calibrated LM reviewers 3/3 & 3/3; human waived →
  model-review-only, NOT human-confirmed): P3-Ideal is the **best arm on every dimension** — prose
  3.89, voice 4.17, scope_control 4.22, over_editing 4.33 (most disciplined), rigidity 4.11 (most
  natural), usefulness 3.78. **The H7 anti-result (packet → rigidity/over-editing) does not hold**;
  P3-Ideal's mechanical protected/unaffected-span flags are brittle exact-match artifacts (benign
  rephrasing), not holistic over-editing. The one real fix is verbatim protected-span locking.
- **Decision: `prioritize_requirement_elicitation`** — the product value is eliciting/organizing the
  requirements authors don't state, not structure per se; structure adds scope discipline; the
  fuller packet improves both compliance and prose. **Product thesis SUPPORTED (provisional).**
  **Phase-2 100-task multimodel benchmark AUTHORIZED; Dataset A.3 expansion REMAINS PAUSED** (prompt
  engine is the near-term lever, not weight training). No commercial ship certification. 9 Dispatch-28
  tests; Gate 0 zero drift.

### Dispatch 27 Phase A — Qwen3-8B bounded prose + Q4 deployment confirmation (2026-07-22)

Executed the bounded Qwen confirmation before any LoRA work. **No training, no dataset change, no
threshold change, no weights published, `master` untouched.**

- **Frozen-before-scoring:** a 15-task confirmation set (reusing D26 frozen prompts) + an
  Aedan-authored Q4-preservation floor (`qwen-q4-confirmation-floor-v0`, delegated authority) +
  the `qwen-prose-confirmation-v1` manifest — committed before generation.
- **Official Q4_K_M** (`Qwen/Qwen3-8B-GGUF` rev `7c41481f`, sha `d98cdcbd…`, exact size, complete)
  generated via llama.cpp `llama-server --reasoning-budget 0` (**non-thinking verified, zero
  reasoning traces**). **Q4 preserves BF16**: mechanical identical (0.933 = 0.933), zero severe
  slop / token-cap / reasoning leak; two blind calibrated LM reviewers (supporting only) find BF16
  and Q4 **indistinguishable** (prose Δ −0.03, voice Δ −0.10, 0 new fatal — all within the 0.35
  floor). 0 identity leaks; scores locked before unblinding.
- **Branch = `confirm_Qwen3_8B_foundation`, PROVISIONAL** — the Q4 package is acceptable and the
  reference clears every frozen threshold with zero fatal prose failures, but the dispatch requires
  the final prose confirmation to include **Gary + an independent human** (not only LM graders).
  That human gate is open, so **Phase B (Dataset A.3 + LoRA) is BLOCKED** until it passes. 5 tests;
  Gate 0 zero drift.

### Dispatch 27 Phase B — Conservative Qwen3-8B LoRA feasibility pilot (2026-07-22)

Ran the confirmed foundation's first LineWright LoRA pilot end to end and made the advancement
decision. **No production claim, no weights published, `master` untouched. Dataset A/A.2/A.3, Fast
Battery v1, and frozen thresholds all unchanged; QAT NOT launched.**

- **Foundation confirmed by Gary** (after the two diverse blind reviews); the ~0.20 base
  focused-revision fatal rate became the pilot's testable target.
- **Training (integrity = valid):** Qwen3-8B @ `b968826d` (thinking disabled), LoRA rank16/α16 on
  the frozen Dataset A.3 (train hash matches), 42 train / 6 val, 21 steps / ~1 epoch, 43.6M trainable
  params. Val loss monotone-decreases (best step-18); grad norms finite; no NaN; no QAT.
- **Checkpoint curve (base + 8 checkpoints × 14 frozen items = 126 gens):** the LoRA is
  **mechanically NEUTRAL** — identical to base on every metric (mechanical 0.786, core-prose 0.857,
  structured 1.0, canon 1.0) with **zero critical regressions, zero severe slop, zero token-cap,
  zero reasoning leak.**
- **Focused-revision audit (primary target, 3-fix probe):** base unchanged-return **0.667**; every
  checkpoint identical at 0.667 — the LoRA does not touch the target; protected line preserved (1.0).
- **Blind base-vs-`step-18` review** (2 calibrated blind LM reviewers; human review waived →
  model-review-only, NOT human-confirmed): base prose **3.455 == LoRA 3.455**, **prose_gain 0.0**,
  0 new fatal — the frozen effect floor (≥0.25) is not cleared.
- **Decision: `revise_Dataset_A3`** — the pilot is non-destructive but neutral (42 records too small
  to move the target); scale + curate A.3 (higher focused-revision density, teacher diversification,
  Gate-3 review) under the same recipe. **QAT denied** (checkpoint not selected). 10 tests; Gate 0
  zero drift.

### Dispatch 27A — Blind prose review kits for external reviewers (2026-07-22)

Packaged the frozen Phase A blind materials into two self-contained reviewer ZIP kits so the human
gate can be completed. **No new outputs; no unblinding; no training.**

- `benchmarks/runs/qwen-prose-confirmation-v1/reviewer-kits/` → `prose-review-chatgpt-v1.zip`,
  `prose-review-claude-v1.zip` (+ private manifest + validation report). Each kit: README, scoring
  instructions, 1–5 rubric (10 dimensions + fatal-failure rules), 36 anonymous review units,
  YAML+JSON score templates (no prefilled scores), submission checklist.
- **Fully blind:** reviewer-salted randomized order (different per kit), no identity key / private
  paths / prior scores / deployment or model manifests, all scores null, output text preserved
  verbatim (hash-checked). **Forbidden-term scan = 0** — kit dir/zip/`review_id` were **neutralized**
  (`prose-review-*`, `prose-confirmation-v1`) rather than the dispatch's illustrative `qwen-*` names,
  which would have announced the model to the blind reviewer (blindness overrides the sample name;
  the private manifest keeps the true run id). 8 tests enforce the invariants.

### Dispatch 27 Phase B prep — Dataset A.3 + frozen LoRA config (training HELD) (2026-07-22)

Per Gary's choice at the gate ("prep A.3, hold training"), prepared Phase B **without training**.
**No LoRA/QAT launched; Dataset A and A.2 unchanged; Fast Battery v1 + thresholds unchanged.**

- **Dataset A.3 design contract** (task mix, token balance, provenance discipline, holdout pools,
  overlap checks, teacher-concentration limits) + a **48-record pilot corpus** — genuinely diverse
  original fiction across all 8 task families in the target mix, single-teacher (documented,
  `review_status: draft`, Gate-3 pending). Audit: mix on target, **changed_true 17 / changed_false 4**
  (fixes the prior audit gap), **benchmark overlap CLEAN (0.0)**, **template Jaccard 0.0** (no
  templating), frozen `train_sha256 91e57242…`. 48 < the 300–500 production target is the
  **documented justified exception** (the remainder needs human curation + teacher diversification).
- **Frozen conservative LoRA config** (`qwen3-8b-lora-pilot-v1`): Qwen3-8B @ `b968826d` non-thinking,
  rank 16 / α16 / dropout 0.05, LR 1e-5, targets q/k/v/o+gate/up/down, ~1 epoch, early stopping,
  frequent checkpoints — deliberately inverting the 4B over-exposure that collapsed by step 20.
  **Frozen checkpoint-eval subset** (14 items) committed before training. 7 more tests.
- **Training is HELD** pending Gary's human foundation confirmation (Phase A gate).

### Dispatch 26 — Controlled stronger-base comparison for LineWright Core (2026-07-22)

Executed the Dispatch-25 `test_stronger_base` branch as a controlled three-model comparison —
base model the ONLY changed variable. **No training, no dataset change, no threshold change, no
weights published, no ship certification, `master` untouched.**

- **Candidates (real, verified on the GX10):** Qwen3-8B (`b968826d`, Apache-2.0, non-thinking
  enforced) and Ministral-3-8B-Instruct-2512 (`5b26027e`, Apache-2.0, **FP8 multimodal**, run
  text-only via `kernels==0.15.2`), vs the Ternary-Bonsai 4B control. Frozen-before-generation:
  candidate/licensing record, a realistic **6-arm × 3-task packet family** (authored project
  world; noisy/repaired identical-content; long arm honestly capped at ~5K tokens since padding
  is prohibited), extension manifest (references Fast Battery v1 unchanged by hash), and a frozen
  94-job plan (`plan_hash d45a04a9`).
- **Phase A run:** 94/94 real jobs, **0 integrity problems, mechanical replay identical**; Qwen
  produced **zero `<think>` traces**. **Core-prose (frozen 0.50 floor): Qwen3 0.857, Ministral
  0.714 — both clear the floor the 4B failed (0.286)**, confirming the bottleneck was base
  capacity. **Qwen3 clears every frozen floor; Ministral fails module-coverage (5/9).**
- **Blind prose** (2 genuinely-blind, perfectly-calibrated sub-agent reviewers; humans Gary/ChatGPT
  pending): Ministral 3.07 > 4B 3.0 > Qwen 2.79 raw prose, but Qwen leads instruction-compliance
  (4.36); zero fatal rejections. **Deployment:** measured resident memory; official GGUFs exist for
  both; Qwen Q4_K_M (~4.7GB) fits 8GB (mature), Ministral's 8GB path unverified.
- **Foundation decision: `run_one_bounded_confirmation`**, presumptive foundation **Qwen3-8B** —
  the only model clearing the frozen threshold with a viable 8GB path, but marginally lowest blind
  prose is a genuine unresolved distinction to confirm (human/quantized blind pass) before
  committing. 16 new tests; Gate 0 zero drift.

### Dispatch 25 — Provisional threshold lock, diagnostic validation, branch decision (2026-07-22)

Converted the Dispatch-24 live run into a threshold-bound branch decision. **No training, no
dataset change, no broad sweep, no winner or ship claim; LoRA-20 not continued.**

- **Threshold-first, enforced:** authored two provisional threshold files
  (`benchmarks/thresholds/research-continuation-v0.yaml`, `starter-model-acceptance-v0.yaml` —
  agent-proposed under delegated authority, NOT final ship gates), **committed them before any
  analysis**, then wrote `threshold-lock-v0.json`. `linewright/evaluation/thresholds/` refuses
  analysis unless the lock verifies; any post-lock threshold change invalidates the decision.
- **Diagnostic-finding-v1 schema** separates observation / causal hypothesis / intervention,
  each with independent confidence (mechanical certainty never propagates). Analyzed all 7
  Dispatch-24 controlled pairs (`diagnostic-findings.json`) — incl. the surface pair ruling out
  the context compiler for the candidate (both arms fail on a **compact** packet; a full
  packet-length family is still required).
- **Real packet token profile** (real tokenizer, no whitespace): bare 167 / compiled 225
  (ratio 1.35), classified **partial/compact**.
- **Blind access separation** (`battery/blind.py`): anonymous `review/` vs `private-unblinding/`;
  scoring cannot open the identity key; unblinding refuses before score-locks.
- **Existing-checkpoint curve** (real run, base + LoRA-10 + LoRA-20 on a frozen 9-item subset):
  mechanical pass 5/5/2, severe slop 0/0/6 — **step-10 neutral, step-20 collapses**, monotone
  worsening, best = base.
- **Dataset A + A.2 audit** (unchanged): example-balance ≠ token-balance (canon dominates
  tokens); no-change protocol half-taught in Dataset A (2 `changed:false`, 0 `changed:true`);
  zero template concentration; single-teacher (opus) provenance.
- **Decision** (`dispatch-25-decision-v1.md`): applying the frozen threshold → **`test_stronger_base`**
  (base fails the 0.50 core-prose floor at 0.286). Next-experiment spec authored (stronger-base
  comparison, one controlled variable; not started). VOICE-P0A verified: a scheduling gate, not a
  blocker. 12 new tests.

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
