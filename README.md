# ternary_QAT

Lightweight ternary QAT for [Ternary-Bonsai](https://huggingface.co/models?search=unpacked%20ternary) unpacked text models.

This is designed from the start to be Unsloth compatible.

## LineWright research fork

This repository is an **experimental research branch** forked from
[ElectroGlyph's `ternary_QAT`](https://github.com/electroglyph/ternary_QAT). The
upstream project remains the source of the ternary-QAT work; this fork does not
replace it, and ElectroGlyph has not endorsed the LineWright project. Generally
useful changes may be proposed upstream.

- Active research branch: **`linewright-experiments`**.
- **Goal:** evaluate a zero-configuration local *starter model* for LineWright
  users — no API key, no model-server knowledge, running on broadly available
  consumer hardware.
- **Ternary-Bonsai 4B is only an initial candidate**, subject to feasibility
  gates. The initial official base candidate is
  `prism-ml/Ternary-Bonsai-4B-unpacked`, and its official Q2_0 GGUF
  (`prism-ml/Ternary-Bonsai-4B-gguf`) is the untouched deployment baseline. 1.7B
  (Lite fallback), 8B (optional higher tier),
  and conventional GGUF models remain valid comparison candidates.
- **Required initial capabilities:** canon extraction, hard-constraint checking,
  focused anti-slop revision, and fiction-permissive compliance. (Optional
  capabilities are enumerated in the roadmap and ship only if they pass their own
  gates.)
- **Author content is never used as gradient input** — see the policy below.
- The project is **benchmark-gated**: nothing is treated as proven until it
  passes precommitted quality and runtime gates.
- **Conventional LoRA and ternary QAT will be compared** on the same base, data,
  splits, and benchmark; QAT is retained only for a meaningful, repeatable gain.
- The **final packed artifact** (the deployed GGUF) must be evaluated — not
  merely training loss.

Full details, phase order, and decision rules are in [`ROADMAP.md`](ROADMAP.md).

### Author-content policy

Author manuscripts, project content, voice samples, and private writing may be
used **only as temporary inference-time context**, carrying provenance tags that
mechanically exclude them from training datasets. Selection history and voice
measurements may inform context compilation, but nothing derived from author
content may become gradient input. Any benchmark distributed publicly or shipped
with LineWright must use synthetic, licensed, public-domain, or otherwise
distributable material.

### Fiction-permission policy

> The starter model must not falsely refuse lawful fictional writing merely
> because it includes violence, sexuality, crime, trauma, horror, abuse,
> addiction, controversial beliefs, or morally compromised characters. The
> project may evaluate naturally permissive models, compatible
> community-abliterated models, local abliteration, or fiction-compliance
> fine-tuning. Every intervention must be tested for writing-quality,
> instruction-following, structured-output, and post-quantization regressions.

- **No abliteration method has yet been selected.**
- Fiction permissiveness is evaluated on the **final packed artifact**, not just
  the base model.
- The target is fiction-safe behavior, **not** a universal unrestricted
  assistant. Real-world operational requests are outside the starter model's
  writing scope. An existing abliterated or permissive model may serve as a
  behavioral comparison but is not automatically the training base, since
  modifications may not survive reprojection to the ternary Q2_0 grid.

### Export path (training vs. deployment)

`swap_linear()` inserts **fake quantization during training** — it does not
itself produce the packed deployment model. The packed artifact is produced by a
separate export path:

```text
Unpacked checkpoint
    ↓
Fake-quantized training
    ↓
Merged or full fine-tuned checkpoint
    ↓
GGUF conversion
    ↓
Compatible Prism-ML llama-quantize
    ↓
Final Q2_0 GGUF
```

LineWright training work has completed a **Run 1 pipeline smoke test** (train →
merge → GGUF → Prism Q2_0 → evaluate) and deployment-grid characterization; it has
**not** begun bulk dataset generation or a production training run.

### Dataset work: research instrument vs. production corpus

LineWright is a **fiction-first private writing studio for novelists**. Dataset
work in this repository is split so a new contributor can tell the difference:

- **Dataset A — a research instrument, not a shipping dataset.** A narrow,
  fiction-only, heavily-reviewed set (~300–400 approved records) built solely to
  drive the matched conventional-LoRA vs ternary-QAT comparison and to test
  whether a small model can follow fiction-craft instructions **without collapsing
  every passage into one house style**. See [`datasets/dataset-a/`](datasets/dataset-a/).
- **Dataset B — the production fiction corpus (later).** Trains the bundled
  fiction model; not created here.
- **Future Writing Engines** (non-fiction specialists) are a **commercial vision,
  not a committed release**, and a larger future fiction model would be a
  transparent hardware tier — never withheld quality.

Dataset A is authored as human-readable **Markdown** (one file per record), moves
through **draft → mechanically validated → substantive review → Gary review →
approved → frozen → compiled**, and is deterministically compiled to JSONL **only
after approval and freeze**. Every record carries provenance and licensing fields;
**no generated record automatically enters training**.

Governing principle:

> Teach a specific fiction-writing operation, preserve everything the author did
> not authorize the model to change, and produce an output that can be evaluated.

Anti-style-collapse principle:

> Anti-slop training must remove genericness, redundancy, unearned explanation,
> and unauthorized rewriting without imposing a universal house style.

Weights are ternarized to `{-1, 0, 1}` per group of (128/64/user-defined) consecutive weights along the last dim, matching the Bonsai on-disk format (verified bit-exact). Embeddings + all `nn.Linear` modules (attn, MLP, lm_head) are ternarized; norms stay FP.

Based on Prism-ML's whitepaper: https://github.com/PrismML-Eng/Bonsai-demo/blob/main/ternary-bonsai-8b-whitepaper.pdf

## LineWright Diagnostic Battery (LWDB)

The **LineWright Model Capability, Reliability, and Tuning Diagnostic Battery** is the
permanent evaluation instrument run after every meaningful model-tuning experiment. It is a
**diagnostic instrument, not a ranking test**: it reports which capability changed, in which
direction, with what effect size, on what evidence, and with what confidence — and names a
likely bottleneck (dataset, training, quantization, context compilation, decoding, or
base-model capacity) only when a controlled comparison supports it.

- **Fast battery** (~24–30 items) runs after meaningful checkpoints to catch catastrophic
  regressions, spot early overfitting, and gate the full battery. **Full battery** (~60–80)
  runs for dataset-version, base-model, quantization, and release decisions. Both share one
  architecture (same schemas, taxonomy, scoring, confidence, and provenance).
- **Mechanical evidence** (schema, no-change preservation, repetition, memorization,
  truncation, negative-space damage) and **reviewer evidence** (prose quality, voice,
  coherence, usefulness) stay separate. A strong subjective score never cancels a mechanical
  fatal flaw.
- **Benchmark items are excluded from training by construction** and never enter gradients;
  items that inform a change become *burned* and stop counting as independent evidence for it.
- Builds on the Dispatch-21 hardened evaluation gates in
  [`linewright/evaluation/`](linewright/evaluation/).

Full specification:
[`training/docs/linewright-diagnostic-battery-architecture-v1.md`](training/docs/linewright-diagnostic-battery-architecture-v1.md).
Machine-readable manifest and schemas live in [`benchmarks/`](benchmarks/).

**Dispatch 23** added the instrument's foundations (still no benchmark prompts, model runs,
or thresholds):

- **Hardware-agnostic execution** — parallel (dual-GX10) and sequential (single-machine)
  runs are semantically equivalent, consuming one frozen, hashed generation plan.
- **Durable pause/resume** — a SQLite run ledger survives graceful/immediate pause,
  controller restart, network changes, and worker loss, resuming without rerunning
  completed jobs (mid-generation recovery is item-level, not token-level).
- **Instrument calibration** — hidden known-good/known-broken grader records that dogfood
  the gates, mechanical replay, and reviewer-reliability classification; a failed
  calibration quarantines findings (`insufficient_evidence`).
- **Module J — slop detection** (not an AI-authorship detector): a hybrid of deterministic
  measures, interface-only semantic detectors, and a reviewer checklist, producing a valid
  slop report with separate evidence families and **unvalidated** thresholds.

See [`lwdb-execution-and-resume-v1.md`](training/docs/lwdb-execution-and-resume-v1.md),
[`lwdb-slop-report-v1.md`](training/docs/lwdb-slop-report-v1.md), and
[`slop-detection-research-review-v1.md`](training/docs/slop-detection-research-review-v1.md).

**Dispatch 24** built and froze the first **fast battery v1** (20 items across modules A–J
with 7 controlled pairs, locked contracts, provenance, hashed manifest) and the full run
pipeline (generation-plan freeze, dual-GX10 worker routing, mechanical + Module-J slop
scoring, blind reviewer packets with calibration seeding and zero identity leaks). The first
execution **ran as a live dual-GX10 parallel run** — untouched base on `gx10-9141`, tuned
LoRA-20 candidate on `gx10-5611`, both against one frozen plan (`plan_hash a726365a`):
**40 / 40 jobs completed, 0 integrity problems, mechanical replay identical → instrument-valid.**
Preliminary, instrument-valid signal (not a verdict): the LoRA-20 candidate **degenerates
markedly more** than the base (severe slop on 9/20 outputs vs 1; token-cap hits 9 vs 3; it
fails both surface-pair arms, so the fault is model/training, not the context compiler), while
both share a structured-protocol weakness. **No winner, capability floor, or release claim is
made** — advancement is **deferred to Dispatch 25**; blind human/independent review is future
work (44 identity-free units + 4 hidden calibration seeds prepared). See
`benchmarks/runs/lwdb-fast-v1-20260722/completed-run-report.md`.

**Dispatch 25** converted that run into a disciplined branch decision. Provisional research
thresholds were **authored and frozen/committed before any interpretation** (agent-proposed
under Gary's delegated authority; not a final ship gate), and a lock makes them immutable — any
post-lock change invalidates the decision. Applying the frozen threshold to the evidence (the
live run, an existing-checkpoint curve, a dataset audit, and a real packet token profile), with
observation/cause/intervention confidence kept separate, the branch is **`test_stronger_base`**:
the untouched base fails the core-prose feasibility floor (0.286 < 0.50), no LoRA checkpoint
improves over it (step-10 neutral, step-20 collapses), and a dataset cannot fix base capacity.
**No training, no dataset change, no winner, no ship claim.** See
`training/reports/dispatch-25-decision-v1.md`.

**Dispatch 26** executed that branch as a controlled three-model comparison (base = only changed
variable): Qwen3-8B (non-thinking) and Ministral-3-8B-Instruct-2512 (FP8, text-only) vs the 4B
control, 94 real GX10 jobs (0 integrity problems, replay identical). Applying the **frozen**
core-prose floor unchanged: **Qwen3 0.857 and Ministral 0.714 both clear 0.50 — the 4B failed at
0.286**, confirming base capacity was the bottleneck. **Qwen3 clears every frozen floor**;
Ministral fails module-coverage. Blind, calibrated reviewers marginally prefer Ministral's raw
prose while Qwen leads instruction-compliance; Qwen has the mature 8GB GGUF path. Branch:
**`run_one_bounded_confirmation`**, presumptive foundation **Qwen3-8B** (confirm prose before
committing). See `training/reports/dispatch-26-foundation-decision.md`.

**Status:** fast battery v1 frozen; live dual-GX10 run + stronger-base comparison completed
(instrument-valid); Dispatch-26 branch = **run one bounded confirmation, presumptive foundation
Qwen3-8B** (threshold-bound, provisional). No training, no dataset change, no empirical ship
thresholds, no published weights.

## Install

Have your preferred torch version installed first so that this doesn't install the CPU version (which you probably don't want)

```bash
pip install ternary_QAT                 # core (torch only)
pip install "ternary_QAT[peft,transformers]"  # + LoRA / model loading

if you use uv:
uv pip install ternary_QAT --torch-backend=auto
```

## Use

### Full-finetune

```python
from transformers import AutoModelForCausalLM
from ternary import swap_linear, TernaryConfig

model = AutoModelForCausalLM.from_pretrained("prism-ml/Ternary-Bonsai-1.7B-unpacked")
swap_linear(model, TernaryConfig(group_size=128))
# ... train normally; ternarize fires in every Linear.forward
```

### LoRA (ternary frozen base + FP adapters)

```python
from peft import LoraConfig, get_peft_model
from ternary import swap_linear, TernaryConfig, ternarize_lora_params, reternarize_merged_linears

model = ...  # load model
swap_linear(model, TernaryConfig(group_size=128))
model = get_peft_model(model, LoraConfig(r=128, lora_alpha=128, ...))

# ... train ...

# at save: ternarize adapter, merge, re-ternarize merged linears
ternarize_lora_params(model)
model = model.merge_and_unload()
reternarize_merged_linears(model)
model.save_pretrained("./out")
```

See [`examples/`](examples/) for LoRA, FFT, and Unsloth examples.

## Learning rate

Ternary QAT needs **10-50x higher LR** than standard fine tuning.

The lowest usable LR I've found so far is around 7e-4, so experiment in that range up to the e-3s, depending on rank and dataset size.