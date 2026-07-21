#!/usr/bin/env python3
"""Merge a Run 1 LoRA adapter into the BF16 base and save a standalone
Transformers checkpoint. Standard Transformers + PEFT only (no Unsloth,
bitsandbytes, FlashAttention, or ternary swap_linear). Does not modify the
source base or adapter."""
import argparse
import os
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def tied_state(model):
    """Return (tied_bool, embed_ptr, head_ptr) for a CausalLM with tied lm_head."""
    inner = getattr(model, "model", model)
    embed = getattr(inner, "embed_tokens", None)
    head = getattr(model, "lm_head", None)
    if embed is None or head is None:
        return None, None, None
    ep, hp = embed.weight.data_ptr(), head.weight.data_ptr()
    return ep == hp, ep, hp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--validate-only", action="store_true",
                    help="load base+adapter, confirm merge possible, write nothing")
    args = ap.parse_args()

    if os.path.isdir(args.output) and os.listdir(args.output) and not args.force \
            and not args.validate_only:
        raise SystemExit(f"refusing to overwrite nonempty output {args.output} "
                         f"(pass --force)")

    print("source base:", args.base_model)
    print("adapter:", args.adapter)
    print("output:", args.output)

    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(args.base_model)
    base = AutoModelForCausalLM.from_pretrained(
        args.base_model, dtype=torch.bfloat16, attn_implementation="sdpa",
        low_cpu_mem_usage=True, device_map={"": 0})
    tied_before, _, _ = tied_state(base)

    model = PeftModel.from_pretrained(base, args.adapter)
    print("dtype:", next(model.parameters()).dtype)

    if args.validate_only:
        print("validate-only: base+adapter loaded; merge is possible. Writing nothing.")
        print(f"tied before merge: {tied_before}")
        print("VALIDATE OK")
        return

    merged = model.merge_and_unload()
    tied_after, _, _ = tied_state(merged)
    n_params = sum(p.numel() for p in merged.parameters())

    os.makedirs(args.output, exist_ok=True)
    merged.save_pretrained(args.output, safe_serialization=True)
    tok.save_pretrained(args.output)
    try:
        merged.generation_config.save_pretrained(args.output)
    except Exception as e:
        print("note: generation_config save skipped:", e)

    shards = [f for f in os.listdir(args.output) if f.endswith(".safetensors")]
    elapsed = time.time() - t0
    peak = round(torch.cuda.max_memory_allocated() / 1e9, 3) if torch.cuda.is_available() else None

    print("dtype (merged):", next(merged.parameters()).dtype)
    print("tied before merge:", tied_before)
    print("tied after merge:", tied_after)
    print("parameter count:", n_params)
    print("shard count:", len(shards))
    print("elapsed (s):", round(elapsed, 1))
    print("peak unified mem (GB):", peak)
    print("MERGE COMPLETE ->", args.output)


if __name__ == "__main__":
    main()
