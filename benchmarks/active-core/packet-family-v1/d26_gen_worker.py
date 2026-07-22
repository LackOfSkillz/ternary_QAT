"""Dispatch-26 generation worker — three loader paths, one model role per process.

Runs ON a GX10 inside linewright-ternary-train:d26 (run001 + kernels==0.15.2). Reads the
frozen stronger-base plan and generates deterministically (greedy) for exactly the items whose
model_roles include this role. Loader dispatch:

  causal_lm          -> AutoModelForCausalLM (bf16). Qwen3 forces enable_thinking=False and the
                        output is scanned for a <think> reasoning trace (recorded, and stripped
                        so hidden reasoning is never counted as prose).
  mistral3_text_only -> AutoProcessor + AutoModelForImageTextToText (Ministral FP8, text-only;
                        vision omitted). finegrained-fp8 kernel via the `kernels` package.

One normalized-generation-result JSON per job. Model identity is recorded here and stripped
before reviewer packets. Self-contained (transformers/peft/torch/kernels in the image).
"""
import argparse
import hashlib
import json
import os
import re
import time

THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--role", required=True)
    ap.add_argument("--model-path", required=True)
    ap.add_argument("--loader", required=True, choices=["causal_lm", "mistral3_text_only"])
    ap.add_argument("--enable-thinking", default="none", choices=["none", "true", "false"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--worker-id", required=True)
    ap.add_argument("--host", required=True)
    ap.add_argument("--health-check", action="store_true")
    args = ap.parse_args()

    import torch
    plan = json.load(open(args.plan, encoding="utf-8"))
    desc = plan["model_descriptors"][args.role]
    seed = int(plan["seeds"][args.role])
    max_new = int(plan["max_new_tokens"])
    enable_thinking = {"none": None, "true": True, "false": False}[args.enable_thinking]

    if args.loader == "causal_lm":
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(args.model_path)
        if tok.pad_token_id is None:
            tok.pad_token = tok.eos_token
        model = AutoModelForCausalLM.from_pretrained(args.model_path, torch_dtype=torch.bfloat16,
                                                     device_map="cuda")
        model.eval()

        def build_ids(system, user):
            msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
            kw = {}
            if enable_thinking is not None:
                kw["enable_thinking"] = enable_thinking
            enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt",
                                          return_dict=True, **kw)
            return enc

        def decode(new_ids):
            return tok.decode(new_ids, skip_special_tokens=True)

        pad_id = tok.pad_token_id
    else:  # mistral3_text_only
        from transformers import AutoProcessor, AutoModelForImageTextToText
        try:  # Mistral tokenizer ships an incorrect regex; the flag fixes tokenization
            proc = AutoProcessor.from_pretrained(args.model_path, fix_mistral_regex=True)
        except TypeError:
            proc = AutoProcessor.from_pretrained(args.model_path)
        model = AutoModelForImageTextToText.from_pretrained(
            args.model_path, torch_dtype=torch.bfloat16, device_map="cuda")
        model.eval()
        tok = proc.tokenizer

        def build_ids(system, user):
            msgs = [{"role": "system", "content": [{"type": "text", "text": system}]},
                    {"role": "user", "content": [{"type": "text", "text": user}]}]
            return proc.apply_chat_template(msgs, add_generation_prompt=True, tokenize=True,
                                            return_dict=True, return_tensors="pt")

        def decode(new_ids):
            return proc.tokenizer.decode(new_ids, skip_special_tokens=True)

        pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    def generate(system, user):
        enc = build_ids(system, user)
        input_ids = enc["input_ids"].to(model.device)
        attn = enc.get("attention_mask")
        attn = attn.to(model.device) if attn is not None else None
        torch.manual_seed(seed)
        kwargs = dict(input_ids=input_ids, max_new_tokens=max_new, do_sample=False,
                      pad_token_id=pad_id)
        if attn is not None:
            kwargs["attention_mask"] = attn
        with torch.no_grad():
            out = model.generate(**kwargs)
        n_in = input_ids.shape[1]
        new = out[0][n_in:]
        raw = decode(new)
        had_think = bool(THINK_RE.search(raw)) or raw.strip().startswith("<think>")
        text = THINK_RE.sub("", raw).strip()
        hit_cap = int(new.shape[0]) >= max_new
        return text, raw, int(n_in), int(new.shape[0]), hit_cap, had_think

    if args.health_check:
        text, raw, *_rest, had_think = generate("You reply with exactly one word.",
                                                "Return exactly: READY")
        print(json.dumps({"role": args.role, "host": args.host, "loader": args.loader,
                          "revision": desc.get("revision"), "had_think": had_think,
                          "health_output": text.strip()[:64]}))
        return

    os.makedirs(args.out, exist_ok=True)
    run_id = plan["plan_id"]
    my_items = [i for i in plan["item_ids"]
                if args.role in plan["items"][i].get("model_roles", plan["model_roles"])]
    done = 0
    for item_id in my_items:
        job_id = f"{run_id}::{item_id}::{args.role}"
        outfile = os.path.join(args.out, job_id.replace(":", "_") + ".json")
        if os.path.exists(outfile):
            done += 1
            continue
        prompt = json.loads(plan["items"][item_id]["prompt"])
        started = time.time()
        text, raw, in_tok, out_tok, hit_cap, had_think = generate(prompt["system"], prompt["user"])
        completed = time.time()
        result = {
            "schema": "normalized-generation-result", "result_id": f"res::{job_id}",
            "run_id": run_id, "job_id": job_id, "plan_id": run_id,
            "benchmark_item_id": item_id, "model_role": args.role,
            "model_identity_ref": desc.get("identity"), "model_revision": desc.get("revision"),
            "tokenizer_revision": desc.get("tokenizer_revision"),
            "prompt_hash": plan["item_hashes"][item_id],
            "behavior_contract_hash": plan["behavior_contract_hashes"][item_id],
            "generation_settings_hash": plan["generation_settings_hash"],
            "execution_mode": plan["execution_mode"], "worker_id": args.worker_id,
            "host_id": args.host, "started_at": started, "completed_at": completed,
            "input_tokens": in_tok, "output_tokens": out_tok,
            "finish_reason": "length" if hit_cap else "stop", "hit_token_cap": hit_cap,
            "reasoning_mode": ("non_thinking" if enable_thinking is False else "default"),
            "reasoning_trace_detected": had_think,
            "output_text": text, "output_hash": _sha(text),
            "raw_output_hash": _sha(raw),
            "backend_metadata": {"loader": args.loader, "transformers_generate": True,
                                 "precision": desc.get("precision")},
            "status": "completed"}
        tmp = outfile + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False)
        os.replace(tmp, outfile)
        done += 1
        print(f"[{args.role}] {done}/{len(my_items)} {item_id} out_tok={out_tok} "
              f"cap={hit_cap} think={had_think}", flush=True)
    print(f"[{args.role}] DONE {done}/{len(my_items)}", flush=True)


if __name__ == "__main__":
    main()
