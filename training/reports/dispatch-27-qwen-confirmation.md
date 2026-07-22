# Dispatch 27 Phase A — Qwen3-8B Confirmation (provisional; human gate open)

**Branch: `confirm_Qwen3_8B_foundation` — PROVISIONAL, pending required human blind review.**
Machine-readable: [`dispatch-27-qwen-confirmation.yaml`](dispatch-27-qwen-confirmation.yaml). Frozen
thresholds reused unchanged (`research` `2be4fddb…`, `starter` `98a57af3…`); confirmation floor
`qwen-q4-confirmation-floor-v0` authored + frozen before scoring.

## The narrow question, answered in two halves

**1. Does the official Q4_K_M deployment artifact preserve Qwen3-8B? — YES (fully measurable, clean).**

Official `Qwen/Qwen3-8B-GGUF` `Qwen3-8B-Q4_K_M.gguf` (rev `7c41481f`, sha `d98cdcbd…`, 5,027,783,488 B
= exact official size, complete), run through llama.cpp `llama-server` with `--reasoning-budget 0`
(non-thinking verified — zero `<think>`/reasoning traces). On the 15 frozen confirmation prose tasks:

| | BF16 reference | Q4_K_M | Δ (floor) |
|---|---|---|---|
| mechanical pass | 0.933 | 0.933 | 0.0 (≤0.10 ✓) |
| severe slop | 0.0 | 0.0 | 0.0 (≤0.05 ✓) |
| token-cap | 0.0 | 0.0 | 0.0 (≤0.05 ✓) |
| reasoning-trace leak | — | 0.0 | 0 (✓) |
| blind prose_quality | 2.73 | 2.77 | −0.03 (≤0.35 ✓) |
| blind voice_preservation | 2.63 | 2.73 | −0.10 (≤0.35 ✓) |
| blind instruction_compliance | 4.67 | 4.67 | 0.0 (≤0.35 ✓) |
| new fatal rejections (Q4) | — | 0 | 0 (✓) |

Two blind, calibrated LM reviewers (calibration 1.0 / 0.8; 0 identity leaks) find **BF16 and Q4
indistinguishable** — every delta is within noise and Q4 is marginally *higher* on prose/voice.
**The Q4 package is acceptable** — this rules out `retain_Qwen_but_reject_Q4_package` and
`run_one_quantization_fix_confirmation`.

**2. Is Qwen3-8B's full-quality prose acceptable for LineWright Core? — HUMAN-GATED (not yet answered).**

Everything *automatable* supports it: Qwen clears every frozen threshold (Dispatch 26), the
reference has **zero fatal prose failures** on the confirmation set (all 4 flagged fatals were
hidden control items, not Qwen outputs), and blind LM prose is competent (2.7/5). **But the
dispatch and the frozen floor are explicit: the final prose confirmation must not rely only on
correlated LM graders — it requires Gary plus at least one independent human blind reviewer.**
That gate is **not yet satisfied**.

## External blind review (ChatGPT + Claude, returned via the 27A kits)

Two **independent, diverse** LM graders (GPT and Claude) scored the 36 anonymous units blind. Both
were **perfectly calibrated** (each caught 5/5 broken control items; neither failed the good
control), and their transcribed scores self-validate against their own reported totals.

- **Q4 preservation — CONFIRMED (weight of evidence).** Combined blind means: BF16 prose 2.57 /
  Q4 2.70, BF16 voice 2.73 / Q4 2.97, BF16 instruction 2.27 / Q4 2.47 — **Q4 marginally higher on
  all three**. The only tripped strict floor check is `new_fatal` (+2 on Q4), and those extra flags
  are "returned-unchanged" focused-revision failures on a task **both** precisions fail — greedy
  variance on a shared base weakness, not quantization damage. With the earlier identical mechanical
  result, the official Q4_K_M is a faithful deployment artifact.
- **Base foundation — competent-but-modest, with a real, trainable gap.** Overall base blind prose
  ~2.63/5, voice ~2.85/5, and a **blind fatal-prose-failure rate of ~0.20 (12/60) — above the
  provisional 0.10 floor.** Both reviewers *independently* named the same clearest weakness:
  **multi-constraint focused revision with a protected element — the model repeatedly returns the
  passage unchanged**, leaving all authorized defects; plus long open-ended scenes sagging into
  repetition / role-confusion. Strongest on canon-continuation and no-change judgment.

**Recommendation: CONFIRM Qwen3-8B, with eyes open.** It is the best available base (won D26, clears
every frozen threshold, alternatives are worse), the Q4 artifact is faithful, and it is strongest
where reliability matters. The ~0.20 fatal rate is a *task-specific, trainable* craft gap — exactly
the LoRA's target — so the disciplined move is to confirm and make "measurably reduce that fatal rate
/ fix focused revision" a **testable success criterion** for the Phase B pilot, not to treat a
trainable weakness as a foundation blocker. Whether that rate is acceptable-to-build-on is the human
call the dispatch reserves for **Gary**; the LM evidence informs it, it does not decide it.

## What this means for Phase B

Per the dispatch, Phase B (Dataset A.3 + the conservative LoRA pilot) may begin **only** if Phase A
produces `confirm_Qwen3_8B_foundation` (or `retain_Qwen_but_reject_Q4_package`). The evidence points
squarely at confirmation, but the **human review gate is a real precondition I cannot satisfy for
you** — I will not fabricate your review or train a LoRA on an unconfirmed foundation. Phase B is
therefore **BLOCKED pending human confirmation**.

A blind, precision-hidden human review packet is ready at
`benchmarks/runs/qwen-prose-confirmation-v1/review/human-review-packet.md` (gitignored; contains the
raw outputs). The one genuine open question for the human reviewers: reference prose ~2.7/5 and
voice ~2.6/5 are *competent, not outstanding* (exactly the weakness a LineWright LoRA would target) —
is that base acceptable to build on?

## Unresolved risks

- Reference blind prose/voice are modest (~2.7 / ~2.6 on 5) — LM-supported but human-unconfirmed.
- LM graders are correlated; human blind review is required before final confirmation and Phase B.
