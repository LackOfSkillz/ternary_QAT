# Prism Ternary Deployment-Grid Characterization

Purpose: determine the exact quantization grid Run 2/Run 3 must train against and
evaluate on, before any QAT config is written. All claims below cite source code
or direct tensor evidence.

## Official sources and commits

| Thing | Source | Commit / rev |
|---|---|---|
| Runtime + quantizer (fork) | `github.com/PrismML-Eng/llama.cpp` (`prism` branch) | `7529fdaaf99ffdc5ca71ace9c7409a56b27ad92f` |
| Model (unpacked FP16) | `hf.co/prism-ml/Ternary-Bonsai-4B-unpacked` | `4485fae7a00129467b9329b738110d88b2942a1a` |
| GGUF artifacts | `hf.co/prism-ml/Ternary-Bonsai-4B-gguf` | `a3eb42bafe873f9686bc97486c43b72ef7d75ec8` |
| Fake-quant lib (this repo) | fork of `electroglyph/ternary_QAT` | HEAD of this branch |
| Docs | `docs.prismml.com/download/formats` | — |
| Whitepaper / demo | `github.com/PrismML-Eng/Bonsai-demo` | — |

## GGML type 42

- Symbolic name: **`GGML_TYPE_Q2_0 = 42`** (fork `ggml/include/ggml.h`; `Q1_0 = 41`
  is the 1-bit type already merged upstream, `NVFP4 = 40`, `COUNT = 43`).
- **Not** in upstream llama.cpp — the `prism` fork adds Q2_0 (CPU NEON/generic +
  Metal). Stock llama.cpp (b9518) rejects it: *"token_embd.weight has invalid
  ggml type 42. should be in [0, 42)"*.
- Block (`ggml/src/ggml-common.h`): `QK2_0 = 128`; `block_q2_0 = { ggml_half d;
  uint8_t qs[128/4]; }` → **34 bytes / 128 weights = 2.125 bpw**.
- Quant math (`ggml/src/ggml-quants.c quantize_row_q2_0_ref`):
  `d = amax(block)` (fp16); `code = clamp(round(w/d), -1, 2) + 1` (C `roundf`,
  half-away-from-zero); dequant `w = (code-1) * d`. In-range data (|w| ≤ amax)
  gives ternary `{-1,0,+1}`; the 4th code (+2) is unused for real data.

## Official artifact load (the gate)

- **PASS.** `Ternary-Bonsai-4B-Q2_0.gguf` loads and generates on the Prism
  runtime, CPU (`-ngl 0`), ctx 2048, temp 0, seed 42, ≤64 tokens.
- Binaries built (native ARM64, CPU): `~/llama.cpp-prism/build-cpu/bin/{llama-completion, llama-cli, llama-quantize}`.
- 4/4 task prompts produced valid nonempty output (canon JSON, `{"violations":["C1"]}`, revision, compliant noir threat).
- Stock `~/llama.cpp` (b9518) **cannot** load it (type 42). This confirms the
  Dispatch-6/9 caution: ordinary upstream llama.cpp is not sufficient.

## Tensor-policy inventory — official Q2_0

From `gguf` reader (`official-q2_0-tensors.json`): 398 tensors —
**253 × Q2_0(42)** + **145 × F32(0)**.

| Class | Type | Count |
|---|---|---|
| `token_embd.weight` | **Q2_0 (ternarized, g128)** | 1 |
| attn q/k/v/output | Q2_0 | 144 |
| mlp gate/up/down | Q2_0 | 108 |
| all norms (attn/ffn/q/k/output) | F32 | 145 |

Answers:
- **Embeddings ternarized?** **Yes** — `token_embd.weight` is Q2_0.
- **lm_head?** **Tied** — there is no separate `output.weight` tensor
  (253 = 7×36 + token_embd; an untied head would be 254). The runtime reuses
  `token_embd.weight` for the output projection.
- **Norms:** F32 (not quantized). No separate scale tensors (fp16 scale is inline
  in each Q2_0 block).

## Why the official Q2_0 (1,074,969,344 B) is smaller than my upstream TQ2_0 (1,261,953,856 B)

Direct tensor evidence (`upstream-tq2_0-tensors.json`): my `llama-quantize TQ2_0`
artifact keeps **`token_embd.weight` at Q6_K (~6.5 bpw)** — upstream default does
**not** ternarize embeddings — while the rest are TQ2_0(35) at **group 256**. The
official Prism Q2_0 ternarizes `token_embd` (Q2_0, ~2.1 bpw). token_embd ≈ 388 M
params → Q6_K ~315 MB vs Q2_0 ~103 MB ≈ **~185 MB**, matching the file-size gap.
So the size difference is a **policy + group-size** difference, not a bug.

## Q2_0 vs PQ2_0 vs Q2_0_g64 (from repo listing + docs)

| File | size (B) | group | runtime | status |
|---|---|---|---|---|
| `Ternary-Bonsai-4B-Q2_0.gguf` | 1,074,969,344 | 128 | Prism fork (type 42) | current deployment |
| `Ternary-Bonsai-4B-PQ2_0.gguf` | 1,074,969,344 | — | Prism fork | **planned/future format** (not yet characterized at tensor level here) |
| `Ternary-Bonsai-4B-Q2_0_g64.gguf` | 1,137,806,656 | 64 | "official mainline llama.cpp format" (per docs) | larger (more per-group scales) |

`Q2_0_g64` is documented as the mainline-loadable variant (g64); `PQ2_0` is a
planned future fork format. **Unresolved (see below):** the exact tensor-level
layout of PQ2_0 and whether `Q2_0_g64` loads in stock llama.cpp were not
verified in this dispatch (only Q2_0 was downloaded and loaded).

## Quantization-math comparison

Sources: `ternary/linear.py::ternarize_weight`; fork `ggml-quants.c
quantize_row_q2_0_ref`; upstream `ggml-quants.c quantize_row_tq2_0_ref`.

| Property | ternary_QAT | Prism Q2_0 | upstream TQ2_0 |
|---|---|---|---|
| group size | **128** | **128** | **256** (QK_K) |
| scale statistic | amax | amax | amax |
| scale precision | fp32 (fake-quant) | **fp16** (stored) | fp16 (stored) |
| scale zero policy | clamp min 1e-8 | id=0 if d==0 | id=0 if d==0 |
| rounding | round-half-**even** (torch.round) | round-half-**away** (roundf) | round-half-away (lroundf) |
| level range | [-1, 1] | [-1, 2] (code 0..3) | [-1, 1] |
| dequant | level·scale | (code-1)·scale | (q-1)·scale |
| embeddings | ternarized (`TernaryEmbedding`) | **ternarized** | Q6_K (not ternarized) |
| lm_head (tied) | re-shared Parameter | tied (omitted) | tied (Q6_K via embed) |
| runtime | training only | Prism fork | stock llama.cpp |

### Equivalence classification (each cites the row above + probe results)

- **ternary_QAT (g128) vs Prism Q2_0 (g128): ARTIFACT-LEVEL EQUIVALENCE CONFIRMED**
  (Dispatch 11). Same grid (g128, amax scale), same embedding-ternarization and
  tied policy. Differences: (a) Prism stores the scale in fp16 (ternary_QAT keeps
  fp32), (b) rounding differs only at exactly ±0.5·amax (half-even vs half-away).
  - Reference-level probe (`compare_ternary_grids.py`, pure NumPy): ternary levels
    match 100% on random off-boundary data; max dequant rel-err ~4e-4.
  - **Artifact-level probe (Dispatch 11):** the real
    `ternary.linear.ternarize_weight` vs the **compiled** fork function
    `quantize_row_q2_0_ref` — linked from `libggml-base.so`
    (`~/llama.cpp-prism/build-cpu/bin`, commit `7529fdaaf`, quantizer binary
    sha256 `712e3b5e…50bad`) via `experiments/native/prism_q2_0_probe.c` on a
    deterministic fixture (random / zeros / exact-±0.5 / near-boundary / outlier /
    embedding-like, g128). Result: **code match 100% off exact-half boundaries**
    (0 off-boundary mismatches), 2 mismatches only at exactly ±0.5 (rounding mode),
    **scale rel-err max 1.2e-4** (fp16 storage), dequant abs-err 1.0 confined to the
    two boundary elements. Scripts: `export_actual_torch_ternary_fixture.py`,
    `compare_actual_torch_vs_prism.py`.
  - **Bit-exact whole-artifact check:** our untouched base quantized with the Prism
    quantizer (`--token-embedding-type Q2_0`) is **byte-identical** to the official
    `Ternary-Bonsai-4B-Q2_0.gguf` (sha256 `4e0bf8b7…f28b8b`). See
    `run001-prism-grid-revalidation.md`.
  ⇒ ternary_QAT is the correct fake-quant to emulate the Prism deployment grid;
  the only differences are the documented fp16-scale storage and ±0.5 half-rounding.
- **ternary_QAT (g128) ≠ upstream TQ2_0 (g256): NOT EQUIVALENT.** Different group
  size and different embedding policy (Q6_K vs ternary).
- **Prism Q2_0 (g128) vs upstream TQ2_0 (g256): NOT EQUIVALENT** (group size +
  embedding policy) despite identical core round/scale math.

## Tied-weight treatment

- Official Q2_0: `lm_head` tied — no `output.weight` tensor; runtime aliases
  `token_embd.weight`.
- `ternary_QAT.swap_linear()` detects the tied pair and re-shares the `lm_head`
  Parameter onto the embedding after swap (the upstream `44a1c84` fix), so the
  tied invariant is preserved through fake-quant training and re-verified in Run 1
  (tied True before and after merge). **Consistent** with Prism's packed policy.

## Grid-comparison probe result

`experiments/scripts/compare_ternary_grids.py` (pure NumPy, no compiled quant):
`GRID COMPARISON OK`; ternary_QAT(g128) vs Prism Q2_0(g128) level-match 1.0,
worst random rel-err 4.8e-4 (< 5e-3 tol); prism(g128) vs upstream(g256) not
close. Fixture tests in `tests/test_ternary_grids.py` (20 pass) pin the
half-boundary rounding difference, all-zero groups, single-outlier scaling,
group-size sensitivity, and embedding-shaped tensors.

## Which grid must Run 2/3 train and evaluate against?

**The Prism Q2_0 grid: group 128, per-group amax fp16 scale, ternary {-1,0,+1},
embeddings ternarized, lm_head tied — loaded/evaluated with the PrismML-Eng
`prism` fork (`7529fdaaf`), NOT stock llama.cpp and NOT upstream TQ2_0.**
`ternary_QAT` fake-quant (g128, `TernaryEmbedding` + tied re-share) matches this
grid up to fp16-scale storage and ±0.5 half-rounding, so it is the right training
emulator. Run 1's earlier "matched-tooling" baseline used upstream TQ2_0 (g256,
Q6_K embeddings) and is therefore **not** a faithful Prism proxy — Run 2/3 must
quantize with the Prism quantizer and evaluate on the Prism runtime.

## Hardware scope

The Prism runtime and performance figures in this report are ARM64/GX10-specific
validation results. They are not evidence for consumer laptop performance or
minimum hardware requirements. Runtime qualification for any minimum-spec claim
must be done on the designated 8 GB Windows laptop (see ROADMAP), not on the GX10.

## Unresolved questions

1. **PQ2_0 tensor layout** and how it differs from Q2_0 (planned/future format) —
   not characterized (artifact not downloaded).
2. Whether **`Q2_0_g64`** actually loads in stock mainline llama.cpp and whether
   its ternary math equals upstream TQ2_0 at g64 — not tested.
3. Exact **fp16-scale + half-rounding** worst-case behavioral impact of the small
   ternary_QAT↔Prism mismatch — bounded tiny here, but should be measured on a
   real model in the survival harness.
4. Whether the Prism quantizer exposes a **fake-quant/round-trip mode** to snap a
   BF16 checkpoint to the exact Prism grid without going through GGUF (would let
   the survival harness compute `*_pack` states directly).

None of these block writing the Run 3 QAT config's *grid* choice (g128 + ternary
embeddings + tied, Prism runtime for eval), but #1–#2 should be closed before a
release-qualification comparison.
