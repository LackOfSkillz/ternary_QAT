"""Caracal Gemma-4 writing test — run the 4-cell writing matrix (DEFERRED).

Do NOT run until Gary approves the LineWright packet AND the final identical decoding config.
For each of the 4 cells (dense_caracal, dense_linewright, moe_caracal, moe_linewright):
  - render the prompt with the checkpoint's OWN chat template (user-only unless template requires system)
  - generate ONCE with the single frozen decoding config (identical across all cells)
  - write a full raw generation record (see freeze/evaluation-plan.yaml) to private-data/generations/
Never clean/correct prose. Never regenerate selectively. Targets/prose stay private/git-ignored.
"""
raise SystemExit("DEFERRED: awaiting LineWright packet + final decoding approval (see freeze/evaluation-plan.yaml)")
