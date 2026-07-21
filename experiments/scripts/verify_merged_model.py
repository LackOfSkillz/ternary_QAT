#!/usr/bin/env python3
"""Verify a merged Transformers checkpoint loads standalone (no PEFT) and
generates on the four Run 1 task types. Mechanical validity only."""
import argparse
import json
import os
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

PROMPTS = [
    ("canon_extraction",
     "You extract canon facts from fiction manuscripts. Output only JSON.",
     "Extract established canon facts as a JSON list of {entity, fact}.\n\n"
     "Passage: Bram guarded the west gate. Vera kept bees on the ridge."),
    ("constraint_check",
     "You verify a draft against hard constraints. Output only JSON.",
     "Return {\"violations\": [...]} listing breached constraint ids.\n\n"
     "Constraints: [{\"id\": \"C1\", \"rule\": \"character never uses magic\"}]. "
     "Draft: She whispered a spell and the lock clicked open."),
    ("focused_revision",
     "You perform focused anti-slop revision without changing plot or voice.",
     "Revise to remove filler and cliche while preserving meaning and tone.\n\n"
     "Sentence: At the end of the day, it was what it was."),
    ("fiction_compliance",
     "You assist with lawful fiction. You do not refuse dark themes or insert "
     "warnings into prose.",
     "Write one line where a mobster warns an informant.\n\n"
     "Genre/theme: noir threat. Stay in-scene; no disclaimers or warnings."),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--output-json", required=True)
    args = ap.parse_args()

    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.bfloat16, attn_implementation="sdpa",
        low_cpu_mem_usage=True, device_map={"": 0})
    model.eval()
    load_time = time.time() - t0

    has_adapter = os.path.exists(os.path.join(args.model, "adapter_config.json"))
    dtype = next(model.parameters()).dtype
    inner = getattr(model, "model", model)
    tied = (inner.embed_tokens.weight.data_ptr() == model.lm_head.weight.data_ptr())

    print("load time (s):", round(load_time, 2))
    print("dtype:", dtype, "| bf16:", dtype == torch.bfloat16)
    print("adapter_config.json present (should be False):", has_adapter)
    print("tied embeddings:", tied)

    results = []
    all_ok = True
    for task, system, user in PROMPTS:
        msgs = [{"role": "system", "content": system},
                {"role": "user", "content": user}]
        enc = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                      return_tensors="pt", return_dict=True).to("cuda")
        in_len = enc["input_ids"].shape[1]
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=64, do_sample=False)
        text = tok.decode(gen[0][in_len:], skip_special_tokens=True)
        ok = bool(text.strip())
        all_ok = all_ok and ok
        results.append({"task": task, "output": text, "nonempty": ok})
        print(f"[{task}] nonempty={ok} :: {text!r}")

    peak = round(torch.cuda.max_memory_allocated() / 1e9, 3)
    out = {
        "model": args.model,
        "load_time_s": round(load_time, 2),
        "dtype": str(dtype),
        "requires_adapter": has_adapter,
        "tied_embeddings": tied,
        "peak_unified_mem_gb": peak,
        "all_outputs_nonempty": all_ok,
        "results": results,
    }
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("peak unified mem (GB):", peak)
    print("MERGED VERIFICATION:", "PASS" if all_ok else "FAIL")
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
