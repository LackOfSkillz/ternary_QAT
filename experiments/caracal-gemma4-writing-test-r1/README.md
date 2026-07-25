# Caracal / LineWright — Gemma 4 StyleTune Writing Test (r1)

A controlled, blinded four-way writing comparison between two Gemma 4 StyleTune checkpoints under two
prompt conditions (Caracal's original prompt vs a LineWright scene packet expressing the same premise).

## Models (verified against the Hugging Face API, not memory)
- **Dense** — `Gryphe/Gemma-4-31B-StyleTune` (`Gemma4ForConditionalGeneration`, dense, 65.4 GB, rev `5a46842f…`) → box **gx10-9141**.
- **MoE** — `Gryphe/Gemma-4-26B-A4B-StyleTune-V2` (`Gemma4ForConditionalGeneration`, MoE ~4B active, 53.1 GB, rev `f34ba405…`) → box **gx10-5611**.

Both are public/ungated. Primary experiment runs **native BF16, no quantization**, one model per GX10.

> Note: "Gemma 4" postdates the assistant's Jan-2026 training cutoff; existence, revisions, architecture,
> sizes, and gated status were all confirmed live via the HF API before any download.

## Layout
- `freeze/` — frozen plans (committed): `model-plan.yaml`, `decoding-plan.yaml`, `evaluation-plan.yaml`, `blind-review-plan.yaml`.
- `scripts/` — generic tooling (committed): runtime validation, writing matrix, blind-review builder, reveal archive builder, share combiner.
- `reports/` — metadata-only reports (committed).
- `private-data/` — **git-ignored**: prompts, generations, review packages, blind keys/shares, recovery secrets, manifests. Never committed.

## Status (this phase = environment preparation only)
Per the dispatch stop condition, this phase stops after: checkpoints downloaded + revisions pinned;
both models load in BF16; native chat templates verified; neutral smoke tests pass; stable endpoints;
Caracal's prompt frozen; the 4-cell matrix and all plans represented in safe config. **No real writing
generations, no LineWright packet, no Candidate A–D assignment, no shares/archive/populated pages yet.**
Those begin only after Gary approves the LineWright packet and final decoding settings.
