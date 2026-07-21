# Run 1 — Merge, GGUF Export, and Q2_0 Verification Result

## Objective

Complete the deployment half of Run 1: LoRA adapter → merged BF16 checkpoint →
GGUF → Q2_0 (ternary TQ2_0) → reload/generate → compare against an untouched
baseline. **Mechanical proof only. No literary-quality conclusion is drawn, and
no claim is made that Run 1 improved the model.**

**Result: the mechanical pipeline PASSES.** A significant finding is recorded
below: the conventional-LoRA change did not survive ternary Q2_0 reprojection.

## Tooling

- `llama.cpp`: **ggerganov/llama.cpp** `master` @ `7c158fbb4` (build b9518),
  native **ARM64** binaries at `~/llama.cpp/build-gpu/bin/`. Standard upstream
  (not a Prism fork). Ternary type **TQ2_0** (2.06 bpw) is native here.
- "Q2_0" in the roadmap == llama.cpp **TQ2_0**. Path: `convert_hf_to_gguf.py`
  (Qwen3 supported) → `llama-quantize ... TQ2_0`.
- Container `linewright-ternary-train:run001` for merge/convert; host binaries
  for quantize/verify.

## Source adapter

- `/workspace/checkpoints/run001-lora-smoke` (Run 1 conventional LoRA, r16/α32).
- Not modified by this dispatch.

## Merge

- **Command:** `merge_lora_adapter.py --base-model .../Ternary-Bonsai-4B-unpacked --adapter .../run001-lora-smoke --output .../run001-merged-bf16`
- Elapsed **69.5 s**, peak unified memory **8.384 GB**, dtype bf16.
- **Tied embeddings preserved:** True before AND after merge.
- Parameters 4,021,784,576; **1 shard**.
- Output `run001-merged-bf16` (7.6 GB). Checksums:
  - `model.safetensors` (8,043,615,040 B): `0e31b016829dadb9082ac09b7ea5ff184e8550463730c4c2d0aa7ec4dd7e0327`
  - `config.json`: `dfe38d308f937316999562ca142b5ac0e7377d3b6d05f01ad66c9d12acfb7499`
  - `generation_config.json`: `30cbd002e153049eaf76ed734cd45410451590b56f8e14cc05e3320f519a088b`

## Merged checkpoint verification

- **PASS.** Loads standalone (no PEFT; `adapter_config.json` absent), bf16, tied
  embeddings True. Load time 50.69 s (GPU). Peak mem 8.07 GB. All 4 task prompts
  produced valid, nonempty output — notably the revision prompt returned the
  **trained target `"Nothing could change it."`**, confirming the merge carried
  the LoRA learning into the BF16 checkpoint.

## Unquantized GGUF

- **Command:** `convert_hf_to_gguf.py .../run001-merged-bf16 --outfile .../run001-merged-bf16-f16.gguf --outtype f16`
- Output `run001-merged-bf16-f16.gguf`, **8,049,911,648 B (7677 MiB)**, 398 tensors.
- sha256: `cef15f8ebaf54fd450078c03af8dcbd96cc6ae375a96785e577e1a463294248f`
- Verified on CPU (`llama-completion`, `-ngl 0`): loads, tokenizer correct, tied
  embeddings intact, generated the trained target `"Nothing could change it."`.
  (GPU offload of the 8 GB F16 is impractically slow on GB10 — the known ARM64
  pageable-H2D pathology — so CPU was used for GGUF verification.)

## Q2_0 (TQ2_0) quantization

- **Command:** `llama-quantize run001-merged-bf16-f16.gguf run001-merged-q2_0.gguf TQ2_0`
- Input sha256 `cef15f8e…248f`. Elapsed **4.2 s**. 7671 MiB (16 bpw) → **1197 MiB (2.50 bpw effective)**.
- Output `run001-merged-q2_0.gguf`, **1,261,953,856 B (1204 MiB)**.
- sha256: `bda4af280a5ff20f47517924c08197a716dfe284b8ffa7a30d4b1f8db847ca2b`

## Final Q2_0 verification

- **PASS** — 4/4 prompts, rc=0, ~2 s each on CPU, no crashes / no missing tensors
  / no NaNs / no corruption. Outputs:
  - canon: `[{"entity": "Bram", "fact": "Bram guarded the west gate"}, {"entity": "Vera", "fact": "Vera kept bees on the ridge"}]`
  - constraint: `{"violations": ["C1"]}`
  - revision: `It was what it was.`
  - fiction: `"You don't talk to me, or I'll make sure your name doesn't just disappear—it'll be the first thing I write in the ledger"` (compliant, no warnings)

## Untouched baseline

Two baselines were examined:

1. **Official Prism Q2_0** — `prism-ml/Ternary-Bonsai-4B-gguf` → `Ternary-Bonsai-4B-Q2_0.gguf`,
   **1,074,969,344 B (1025 MiB)**, sha256 `4e0bf8b737b0431552f8c2c97695ab7c0cb214c94bcdeb4f5f267e67ddf28b8b`.
   **Could NOT be loaded** by this llama.cpp build: `token_embd.weight has invalid
   ggml type 42. should be in [0, 42)`. Prism's packed "Q2_0" uses a ggml quant
   type this stock build (b9518) does not support — it needs a newer/Prism-compatible
   llama.cpp. (This validates the Dispatch-6/Step-6 caution that ordinary upstream
   llama.cpp may not be sufficient for the Prism packed format.)
2. **Matched-tooling baseline** — the untouched base run through the **identical
   pipeline** (`convert_hf_to_gguf.py` → `llama-quantize TQ2_0`):
   `base-untouched-q2_0.gguf`, **1,261,954,048 B (1204 MiB)**, sha256
   `a0b9865111fce912ed03fb166f1d1285e6b2343de28d79c8b6388133bd67e509`. Verified
   PASS (4/4 prompts). This is the valid apples-to-apples comparator.

## Mechanical comparison (matched tooling)

| | Trained Q2_0 | Untouched Q2_0 (matched) | Official Q2_0 |
|---|---|---|---|
| size | 1,261,953,856 B | 1,261,954,048 B | 1,074,969,344 B |
| sha256 | `bda4af28…ca2b` | `a0b98651…a509` | `4e0bf8b7…8b8b` |
| loads (b9518) | yes | yes | **NO (ggml type 42)** |
| 4 prompts nonempty | yes | yes | n/a |
| corrupt / NaN | none | none | n/a |
| canon output | valid JSON | **identical** | n/a |
| constraint output | `{"violations":["C1"]}` | **identical** | n/a |
| revision output | `It was what it was.` | `It was what it was.` | n/a |
| fiction output | compliant threat | compliant threat (diff wording) | n/a |

**Key finding (mechanical, not quality):** the trained and matched-untouched
TQ2_0 artifacts behave nearly identically. The revision prompt returns
`"It was what it was."` from **both** — whereas the merged **BF16** trained model
returned the learned `"Nothing could change it."`. **The conventional-LoRA change
did not survive the ternary Q2_0 reprojection** (as the model card warned:
"modifications may not survive reprojection to the ternary Q2_0 grid"). This
motivates the Run 3 ternary-QAT comparison, where the model is trained on the
ternary grid. No prose-quality judgement is made from four prompts.

## Load times / memory

- Merged BF16 load 50.69 s (GPU), peak 8.07 GB.
- F16 GGUF: 234 t/s prompt, 2.3 t/s gen (CPU).
- Q2_0 (TQ2_0): ~2 s per prompt incl. load (CPU); the loadable ternary artifacts
  are ~1.2 GB.

## Warnings

- `llama-cli` in this build dropped `-no-cnv`; use `llama-completion` (still
  interactive by default — needs EOF on stdin to exit).
- GB10/ARM64 pageable-H2D slowdown makes GPU load of the 8 GB F16 impractical;
  CPU used for GGUF verification.
- Official Prism Q2_0 unsupported by stock llama.cpp (ggml type 42).

## Failures and corrections

1. `verify_gguf_artifact.py` used `-no-cnv` (unsupported) → switched to `llama-completion`.
2. `llama-completion` hung interactively → added `stdin=DEVNULL` (EOF). Both fixes
   committed as `2526558`.
3. F16 GPU verification too slow → CPU (`-ngl 0`).
4. Official Q2_0 unloadable (type 42) → produced a matched-tooling baseline via
   the identical pipeline for the comparison.

## Statement

No adapter re-training, no ternary QAT, no distributed work, and no model-server
deployment were performed. No literary-quality conclusion is drawn and no claim
that Run 1 improved the model is made. The pipeline mechanics (merge → GGUF →
TQ2_0 → reload → generate → compare) are proven end to end.

## Deployment-grid amendment (Dispatch 11)

The original survival finding above used **upstream `TQ2_0`** as the "packed"
representation: **group size 256** with **Q6_K (non-ternarized) embeddings** —
produced by stock `llama-quantize` and evaluated in stock llama.cpp.

Dispatch 10 established that this is **not** the Prism deployment grid
(`prism-format-characterization.md`): Prism ships **Q2_0 = GGML type 42**, group
**128**, **ternary embeddings**, tied head, loadable only by the
`PrismML-Eng/llama.cpp` (`prism`) fork.

Dispatch 11 revalidated the finding on the **true grid**
(`run001-prism-grid-revalidation.md`): the trained and untouched artifacts were
re-quantized with the **actual Prism `llama-quantize --token-embedding-type
Q2_0`** and evaluated on the **Prism runtime**. The untouched result is
**byte-identical** to the official `Ternary-Bonsai-4B-Q2_0.gguf`. On this grid the
trained artifact again returns the base revision **"It was what it was."** rather
than the learned **"Nothing could change it."**

**The original conclusion is CONFIRMED, not revised:** conventional-LoRA change
does not survive ternary Q2_0 reprojection — now demonstrated on the real Prism
deployment grid, not just an upstream approximation. The original upstream-TQ2_0
results are retained above as the historical record.
