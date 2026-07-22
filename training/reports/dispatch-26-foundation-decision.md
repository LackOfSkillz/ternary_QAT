# Dispatch 26 — LineWright Core Foundation Decision (provisional)

**Branch: `run_one_bounded_confirmation`.** Presumptive foundation: **Qwen3-8B (non-thinking)**.
Provisional; **no final commercial ship certification; no weights published; `master` untouched.**
Machine-readable: [`dispatch-26-foundation-decision.yaml`](dispatch-26-foundation-decision.yaml).
Threshold lock verified (`research` `2be4fddb…`, `starter` `98a57af3…`); the frozen floors were
**reused, not re-authored**.

## What the controlled comparison found

Three models, one changed variable (the base), 94 real jobs on the GX10 (0 integrity problems,
mechanical replay identical):

- **Frozen threshold (decisive, hierarchy level 2):** **Qwen3-8B clears every frozen floor**
  (core-prose 0.857, mechanical 0.75, 7/9 modules, zero severe slop, zero token-cap, **zero
  reasoning-trace leakage**). **Ministral clears core-prose (0.714) but FAILS module-coverage
  (5/9 < 7)** — its failures concentrate in structured-protocol tasks. The **4B remains
  infeasible** (core-prose 0.286).
- **Blind prose (2 genuinely-blind sub-agent reviewers, perfectly calibrated 1.0/1.0, tight
  agreement 0.25):** raw prose quality slightly favours **Ministral (3.07) > 4B (3.0) > Qwen
  (2.79)**, while **instruction-compliance favours Qwen (4.36)**. Zero fatal rejections for any
  candidate. External human reviewers (**Gary, ChatGPT**) are **pending**.
- **Packet family (6 arms × 3 tasks):** all three models produce mechanically-valid prose on
  compiled LineWright packets up to ~5K tokens (no collapse, no runaway); the 8–12K long-context
  stress was **not** reached without prohibited padding (recorded limitation), so salience-repair
  benefit is not yet observable mechanically.
- **Deployment (hierarchy level 8):** Qwen3 has a **mature official GGUF** (`Qwen3-8B-GGUF`
  Q4_K_M, single ~4.7 GB file) that **fits 8 GB**. Ministral has an official GGUF too, but its
  mistral3-multimodal/FP8 path + 8 GB behaviour are **unverified** (transformers FP8 resident
  10.4 GB, generation spikes ~27 GB). Physical 8 GB-GPU testing unavailable on the GB10 (121 GB
  unified) — 8 GB fit is reasoned from artifact size + measured resident memory.

## Why `run_one_bounded_confirmation`, not `select_Qwen3_8B`

Qwen3 is the **only** model clearing the frozen threshold **and** the only one with a viable 8 GB
deployment path — Ministral is ruled out at the threshold level (module-coverage), and its
marginal prose edge **cannot** override a threshold failure (explicit rule + decision hierarchy).
So the foundation is effectively Qwen3. **But** the one genuinely unresolved signal is Qwen3's
*prose quality*: two blind, calibrated reviewers placed it marginally **below both** Ministral and
the 4B, and human blind reviewers have not yet scored. Ambiguity is not a win. The disciplined
move is **one bounded confirmation targeting exactly that distinction** — an expanded/human blind
prose pass on Qwen3's core-prose outputs (plus a check on the GGUF-quantized artifact's prose) —
before committing the foundation. Not a broad new benchmark; one focused confirmation.

## Rejected branches

- **`select_Qwen3_8B`** — premature: Qwen's blind prose is marginally the lowest of the three and
  human review is pending; committing now would ignore a real (if small) prose signal.
- **`select_Ministral_3_8B`** — Ministral fails the frozen module-coverage floor; prose preference
  cannot override a threshold failure, and its 8 GB local path is unverified.
- **`retain_current_4B`** — the 4B fails the core-prose floor (0.286); both 8B bases roughly triple
  its core-prose reliability. Retaining it is not supportable.
- **`test_another_base`** — unnecessary: a feasible, well-supported stronger base (Qwen3) was found.
- **`insufficient_evidence`** — the mechanical/threshold evidence is clean and decisive; only the
  prose-quality tie-break is open, which a bounded confirmation resolves.

## The bounded confirmation (next step, not run here)

Hold base = Qwen3-8B, method fixed; obtain **human/expanded blind prose scores** on the frozen
core-prose outputs (Gary + at least one independent reviewer), and a blind pass on the **Q4_K_M
GGUF** outputs, to confirm Qwen3's prose is not materially worse than Ministral/4B at deployment
precision. One controlled question, no dataset change, no training.

## Unresolved risks

- Qwen3 blind prose marginally below peers (2 sub-agent reviewers; humans pending).
- Voice-preservation is weak across ALL models (~2.7–2.9/5) — a fine-tune target, not a base
  disqualifier.
- Long-context (8–12K) packet stress not exercised (authored project caps at ~5K without filler).
- Quantized (GGUF) prose quality vs full precision not yet blind-reviewed.
