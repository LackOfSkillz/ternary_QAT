# Conservative Qwen3-8B LoRA Pilot — config (v1)

**Frozen config. Training HELD** pending Gary's human foundation confirmation (Dispatch 27 Phase A
gate). Committed before any training. Machine-readable:
[`qwen3-8b-lora-pilot-v1.yaml`](qwen3-8b-lora-pilot-v1.yaml). Frozen thresholds reused unchanged.

## Question

Can a *modest* LineWright LoRA improve Qwen3-8B's prose, voice, restraint, and author-usefulness
**without** damaging instruction-compliance, structured protocol, canon fidelity, stability, or
packet handling? A feasibility experiment — not a production run.

## Recipe (one conservative choice; no sweep)

- **Base:** `Qwen/Qwen3-8B` @ `b968826d` (Instruct, non-thinking). Not Qwen3 Base.
- **LoRA:** rank 16, alpha 16 (~1×), dropout 0.05, targets `q/k/v/o_proj` + `gate/up/down_proj`.
- **Optim:** LR **1e-5** (conservative end of 5e-6–2e-5; nothing like the ternary-QAT 7e-4 regime),
  cosine, 3% warmup, weight_decay 0, grad-clip 1.0, adamw, bf16.
- **Run:** ~1 epoch, shuffled, **early stopping** on val loss, dev pool held out, seq len **2048**
  (from A.3 stats, not the 131K advertised context), packing off.
- **Checkpoints:** every 3 steps (≥4 trained checkpoints before final), recording step / examples /
  tokens / passes / train+val loss / LR / grad-norm / adapter hash.

## Why this shape (vs the failed 4B run)

The 4B LoRA-20 overexposed 28 records across ~5 passes and collapsed by step 20 (severe slop 9/20,
token-cap 9/20). This pilot deliberately inverts that: **more records (48 > 28), fewer passes
(~1 vs ~5), lower LR, frequent early checkpoints, early stopping** — to catch the peak *before*
degeneration rather than train through it. Stop conditions: severe slop, token-cap runaway, a
frozen critical-module regression, worsening val loss, diversity collapse, reasoning traces, or a
clear peak-then-decline.

## Advancement (precommit, applied unchanged after review)

A checkpoint advances only if base thresholds preserved, **zero** critical / severe-slop / token-cap
/ reasoning-leak regressions, structured-output and realistic-packet not materially worse, core-prose
not worse, **and** blind prose *meaningfully* better (≥0.25 on 5) with voice-preservation up (≥0.25)
and instruction-compliance drop ≤0.15, zero new fatal. Non-wins: prose up but protocol down; voice up
but canon down; one reviewer only; a later checkpoint when an earlier was better; more verbose ≠ more
useful; imitating a single training voice.
