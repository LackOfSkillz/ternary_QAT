# Environment Validation — caracal-gemma4-writing-test-r1

**Phase:** environment preparation. Metadata only. Master untouched.

> **Verification correction:** "Gemma 4" postdates the assistant's Jan-2026 training cutoff. Rather than
> assume it doesn't exist, the model existence, revisions, architecture, sizes, and gated status were
> confirmed **live via the Hugging Face API** (a genuinely-fake repo returns HTTP 401; these return real
> `model_info` JSON with `sha` + `siblings`). The dispatch's models are real and public.

## Models (verified)
| | dense | MoE |
|---|---|---|
| model | `Gryphe/Gemma-4-31B-StyleTune` | `Gryphe/Gemma-4-26B-A4B-StyleTune-V2` |
| revision | `5a46842fc6c9…` | `f34ba405740e…` |
| arch class | Gemma4ForConditionalGeneration | Gemma4ForConditionalGeneration |
| architecture | dense | mixture_of_experts |
| base model | google/gemma-4-31B-it | google/gemma-4-26B-A4B-it |
| gated | False | False |
| repo GB / shards | 65.4 / 2 | 53.1 / 2 |
| chat_template.jinja | True | True |
| assigned box | gx10-9141 | gx10-5611 |
| download | in_progress | blocked_box_address_unknown |

## Runtime
- Container `linewright-ternary-train:d26`: transformers **5.14.1** (natively supports `model_type: gemma4`), torch 2.10.0a0+nv25.11.
- Precision: BF16 weights + BF16 KV cache, **no quantization**; max_model_len 16384.
- Engine preference: ['vLLM', 'transformers', 'minimal_shared_transformers_service'].
- gx10-9141 disk free: 2.0 TB. HF token required: False (models ungated).

## Blockers
- **gx10-5611 (second GX10) Tailscale address is unknown to Aedan — required to download/load/serve the MoE model on its assigned box. gxssh currently reaches only gx10-9141 (100.92.130.112).**

## Frozen / prepared
- Caracal prompt frozen verbatim (441 bytes, sha `9964e2161cef…`), private.
- LineWright packet: **awaiting Gary approval** (generation not allowed).
- 4-cell matrix + decoding/evaluation/blind-review/recovery plans represented in `freeze/`.
- No real generations; no Candidate A–D; no shares/archive/populated pages.
