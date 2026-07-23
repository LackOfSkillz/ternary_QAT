# Dispatch 27 Phase B — LoRA Training Integrity

**Integrity outcome: `valid`.** Machine-readable:
[`dispatch-27-lora-training-integrity.yaml`](dispatch-27-lora-training-integrity.yaml).

- **Base:** `Qwen/Qwen3-8B` @ `b968826d` (exact, correct), thinking disabled. LoRA rank 16 / α16 /
  dropout 0.05, targets `q/k/v/o+gate/up/down`, **43,646,976 trainable params**.
- **Dataset:** frozen Dataset A.3 pilot — the training `train_sha256` **matches** the committed
  freeze (`91e57242…`). 42 train / 6 validation (one held out per task family). Dataset A / A.2
  unchanged.
- **Run:** 21 optimizer steps / ~1 epoch, 23.9 s, peak 23.5 GB. **Validation loss decreases
  monotonically 4.4298 → 4.3783 (step 3→18)**, slight uptick at step 21 (val-loss optimum = step-18);
  train loss noisy (batch 2, 42 records). **Grad norms finite (2.7–4.8), no NaN/Inf.** No silent
  resume, no checkpoint substitution. 7 step checkpoints + final (== step-21), all adapter-hashed.
- **QAT: not launched.**
