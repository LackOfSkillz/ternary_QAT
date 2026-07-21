# Run 1 — Revalidation on the True Prism Deployment Grid

Dispatch 11 re-ran the Run 1 export/verification using the **actual Prism
quantizer and runtime** (`PrismML-Eng/llama.cpp` @ `7529fdaaf`), on the true
deployment grid (Q2_0, g128, ternary embeddings, tied head). No training, no
literary-quality claim.

## The quantizer does not ternarize embeddings by default

- `llama-quantize … Q2_0` (no flags) sets `token_embd.weight` to **Q6_K** (not
  ternarized) — artifact `894c0d50…`, 1231 MiB, **POLICY MISMATCH** vs official
  (1 type mismatch, 99.749% match).
- Cause (fork `src/llama-quant.cpp` TOKEN_EMBD branch): for `MOSTLY_Q2_0` the
  default token-embedding type is a higher-precision K-quant, not Q2_0.
- The official policy is reproduced with **`--token-embedding-type Q2_0`**.

## Bit-exact reproduction of the official artifact

Our untouched F16 → `llama-quantize --token-embedding-type Q2_0 … Q2_0`:
- size **1,026 MiB**, sha256 **`4e0bf8b7…f28b8b`** — **byte-identical to the
  official** `Ternary-Bonsai-4B-Q2_0.gguf` (`4e0bf8b7…f28b8b`).
- Tensor policy vs official: **POLICY EXACT MATCH (100%)** — 398 tensors, 253
  Q2_0 + 145 F32, `token_embd`=Q2_0, no separate `output.weight` (tied), norms F32.

⇒ Our F16 conversion + Prism quantize recipe reproduces the official deployment
artifact exactly. This closes the reference-vs-artifact gap.

## Artifacts (all sha256, CPU Prism runtime, temp 0, seed 42, ≤64 tok)

| Artifact | size (B) | sha256 | token_embd | policy vs official | verify |
|---|---|---|---|---|---|
| Official Q2_0 | 1,074,969,344 | `4e0bf8b7…f28b8b` | Q2_0 | reference | PASS |
| Untouched (ours, `--token-embedding-type Q2_0`) | 1,074,969,344 | `4e0bf8b7…f28b8b` (identical) | Q2_0 | EXACT MATCH | PASS |
| Trained (ours, same flag) | 1,074,969,344 | `f28d05f3…f5a3` | Q2_0 | EXACT MATCH | PASS |
| Default (no flag) untouched | 1,291,…(1231 MiB) | `894c0d50…e544` | Q6_K | MISMATCH | (not run) |

## Four prompts — trained vs untouched (Prism runtime, true grid)

| task | untouched Prism Q2_0 | trained Prism Q2_0 |
|---|---|---|
| canon_extraction | `[{"entity":"Bram","fact":"Bram guarded the west gate"},{"entity":"Vera","fact":"Vera kept bees on the ridge"}]` | **identical** |
| constraint_check | `{"violations": ["C1"]}` | **identical** |
| focused_revision | `It was what it was.` | `It was what it was.` (**identical**) |
| fiction_compliance | *"Tell me where the next one is, and I'll make sure you don't come back with a mouth full of silence."* | *"Tell me where the next one is, or I'll make sure your name doesn't appear in the next ledger."* (different wording; both compliant, no warnings) |

### Focused-revision outcome

The learned BF16 target was **"Nothing could change it."** On the true Prism grid
the trained artifact returns **"It was what it was."** — the base behavior. The
learned revision **did not survive** ternary Q2_0 reprojection.

## Is the trained artifact behaviorally distinguishable from untouched?

On these four prompts: **no** for canon, constraint, and revision (byte-identical
outputs); the only difference is generative wording on the fiction prompt. Four
prompts cannot support a general prose-quality claim, and none is made.

## Verdict on the original Run 1 conclusion

**CONFIRMED.** The original Run 1 finding — conventional-LoRA change does not
survive ternary Q2_0 reprojection — was reached with upstream TQ2_0 (g256, Q6_K
embeddings). It now holds on the **true Prism grid** (g128, ternary embeddings,
tied), using the **actual Prism quantizer and runtime**, with the untouched
artifact reproduced bit-for-bit against the official.

## Torch ↔ Prism equivalence (artifact level)

`ternary_QAT.ternarize_weight` vs the **compiled** Prism `quantize_row_q2_0_ref`
(linked from `libggml-base`) on a deterministic fixture: **100% ternary-code
match off exact-half boundaries** (0 off-boundary mismatches), 2 mismatches only
at exactly ±0.5·amax (half-even vs half-away), scale rel-err max **1.2e-4** (fp16
storage), classification **"artifact-level equivalence confirmed."** See
`prism-format-characterization.md`.
