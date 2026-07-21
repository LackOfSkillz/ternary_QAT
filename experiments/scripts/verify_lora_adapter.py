#!/usr/bin/env python3
"""Verify a trained Run 1 LoRA adapter: load base + adapter, inspect config,
run one short generation. Does NOT merge the adapter."""
import argparse
import json
import os

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model", required=True)
    ap.add_argument("--adapter", required=True)
    args = ap.parse_args()

    print("=== LOAD BASE ===")
    tok = AutoTokenizer.from_pretrained(args.base_model)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        args.base_model, dtype=torch.bfloat16, attn_implementation="sdpa",
        low_cpu_mem_usage=True, device_map={"": 0})

    print("=== LOAD ADAPTER (not merged) ===")
    model = PeftModel.from_pretrained(base, args.adapter)
    model.eval()

    # adapter metadata
    cfg_path = os.path.join(args.adapter, "adapter_config.json")
    if os.path.exists(cfg_path):
        with open(cfg_path, encoding="utf-8") as f:
            acfg = json.load(f)
        print("adapter r:", acfg.get("r"), "| alpha:", acfg.get("lora_alpha"),
              "| dropout:", acfg.get("lora_dropout"))
        print("adapter target_modules:", acfg.get("target_modules"))
        print("adapter task_type:", acfg.get("task_type"))
    has_weights = (os.path.exists(os.path.join(args.adapter, "adapter_model.safetensors"))
                   or os.path.exists(os.path.join(args.adapter, "adapter_model.bin")))
    print("adapter weights present:", has_weights)

    print("=== GENERATION (<=64 new tokens) ===")
    msgs = [
        {"role": "system", "content": "You perform focused anti-slop revision "
         "without changing plot or voice."},
        {"role": "user", "content": "Revise the sentence to remove filler and "
         "cliche while preserving meaning and tone.\n\nSentence: At the end of "
         "the day, it was what it was."},
    ]
    enc = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                  return_tensors="pt", return_dict=True).to("cuda")
    in_len = enc["input_ids"].shape[1]
    with torch.no_grad():
        gen = model.generate(**enc, max_new_tokens=64, do_sample=False)
    text = tok.decode(gen[0][in_len:], skip_special_tokens=True)
    ok = bool(text.strip())
    print("generated:", repr(text))
    print("output nonempty:", ok)
    print("peak mem (GB):", round(torch.cuda.max_memory_allocated()/1e9, 3))
    print("ADAPTER VERIFICATION: PASS" if ok else "ADAPTER VERIFICATION: FAIL")


if __name__ == "__main__":
    main()
