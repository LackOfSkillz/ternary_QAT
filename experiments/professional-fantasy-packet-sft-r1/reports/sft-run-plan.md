# SFT Run Plan (Dispatch 30G)

- Base: Qwen/Qwen3-8B @ b968826d9c46..., max_seq 8192, thinking disabled.
- Arms: frozen_base (eval only), atomic_packet_sft, compositional_packet_sft.
- Recipe (identical across arms): LoRA r16/a16 dropout0.05, targets q/k/v/o/gate/up/down; 1 epoch, batch2/ga1, lr1e-5 cosine, warmup0.03, wd0, clip1.0, bf16, seed20260722, gradient checkpointing, completion-only loss.
- Basis: repo-validated qwen3-8b-lora-pilot-v1 (Dispatch 27B); deviation: MAXLEN->8192 (targets need it) + grad checkpointing.
- Controls: same targets, record order, seed, optimizer, scheduler, batch geometry, steps, checkpoint policy.
- Checkpoint selection: final checkpoint after equal training exposure, fixed before any held-out inference.
