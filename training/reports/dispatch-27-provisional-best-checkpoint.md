# Dispatch 27 Phase B — Provisional Best Checkpoint (pre-blind)

**Selected: `lora_step-18` (optimizer step 18), BEFORE any blind-review
identity mapping.** Machine-readable:
[`dispatch-27-provisional-best-checkpoint.yaml`](dispatch-27-provisional-best-checkpoint.yaml).

All 8 checkpoints are mechanically eligible (zero reasoning leak, no new severe-slop/token-cap,
zero critical regressions, canon/no-change/structured/realistic-packet not worse than base). They
**tie on every quality metric** — the LoRA is neutral, and the focused-revision audit shows no
checkpoint reduces the unchanged-return rate (gain = 0.0). With all higher-priority ranking keys
tied, the **validation-loss tiebreaker (criterion 6)** selects **step-18** (val loss
4.3783, the curve minimum). The final/step-21 checkpoint is deliberately NOT
privileged.

- focused-revision unchanged-return reduction: 0.0
- critical regressions: 0
- eligible alternatives: 8 (all checkpoints)
- rejected: 0

Selecting a checkpoint here does NOT imply advancement — advancement requires the blind prose gain
to clear the frozen effect floor, which is decided next.
