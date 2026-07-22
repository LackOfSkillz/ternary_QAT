"""Real HF generation worker for the fast battery (Dispatch 24 continuation).

Runs ON a GX10 (inside the linewright docker image) for ONE model role. Reads the frozen
generation plan, loads the assigned model (base, or base + LoRA adapter for the candidate),
generates each item's output deterministically, and writes one normalized-generation-result
JSON per job. Self-contained: transformers + peft + torch only (all in the image); no
dependency on the wider repo. Model identity fields are recorded here (stripped before
reviewer packets).

Usage (inside container):
  python hf_gen_worker.py --plan generation-plan.json --role target_base \
     --base-model /workspace/hf-cache/prism-ml/Ternary-Bonsai-4B-unpacked \
     --out /workspace/out --worker-id w-base --host gx10-9141
  # candidate adds: --adapter /workspace/lora-step-20
"""
import argparse
import hashlib
import json
import os
import time


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--role", required=True, choices=["target_base", "new_candidate"])
    ap.add_argument("--base-model", required=True)
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--worker-id", required=True)
    ap.add_argument("--host", required=True)
    ap.add_argument("--health-check", action="store_true",
                    help="load model, emit a READY probe, and exit (no benchmark content)")
    args = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    plan = json.load(open(args.plan, encoding="utf-8"))
    desc = plan["model_descriptors"][args.role]
    gen = plan["generation_settings"]
    seed = int(plan["seeds"][args.role])
    max_new = int(plan["max_new_tokens"])

    tok = AutoTokenizer.from_pretrained(args.base_model)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.base_model, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.adapter)
    model.eval()

    def generate(system, user):
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt",
                                      return_dict=True)
        if hasattr(enc, "input_ids") or isinstance(enc, dict):
            input_ids = enc["input_ids"].to(model.device)
            attn = enc["attention_mask"].to(model.device) if enc.get("attention_mask") is not None else None
        else:  # some versions return a bare tensor
            input_ids = enc.to(model.device)
            attn = None
        torch.manual_seed(seed)
        kwargs = dict(input_ids=input_ids, max_new_tokens=max_new, do_sample=False,
                      pad_token_id=tok.pad_token_id)
        if attn is not None:
            kwargs["attention_mask"] = attn
        with torch.no_grad():
            out = model.generate(**kwargs)
        n_in = input_ids.shape[1]
        new = out[0][n_in:]
        text = tok.decode(new, skip_special_tokens=True)
        hit_cap = int(new.shape[0]) >= max_new
        return text, int(n_in), int(new.shape[0]), hit_cap

    if args.health_check:
        text, *_ = generate("You reply with exactly one word.", "Return exactly: READY")
        print(json.dumps({"role": args.role, "host": args.host,
                          "model_revision": desc.get("revision"),
                          "adapter": bool(args.adapter), "health_output": text.strip()[:64]}))
        return

    os.makedirs(args.out, exist_ok=True)
    run_id = plan["plan_id"]
    done = 0
    for item_id in plan["item_ids"]:
        job_id = f"{run_id}::{item_id}::{args.role}"
        outfile = os.path.join(args.out, job_id.replace(":", "_") + ".json")
        if os.path.exists(outfile):          # resumable: skip completed jobs
            done += 1
            continue
        prompt = json.loads(plan["items"][item_id]["prompt"])
        started = time.time()
        text, in_tok, out_tok, hit_cap = generate(prompt["system"], prompt["user"])
        completed = time.time()
        result = {
            "schema": "normalized-generation-result", "result_id": f"res::{job_id}",
            "run_id": run_id, "job_id": job_id, "plan_id": run_id,
            "benchmark_item_id": item_id, "model_role": args.role,
            "model_identity_ref": desc.get("identity"), "model_revision": desc.get("revision"),
            "checkpoint_ref": desc.get("checkpoint"),
            "prompt_hash": plan["item_hashes"][item_id],
            "behavior_contract_hash": plan["behavior_contract_hashes"][item_id],
            "generation_settings_hash": plan["generation_settings_hash"],
            "execution_mode": plan["execution_mode"], "worker_id": args.worker_id,
            "host_id": args.host, "started_at": started, "completed_at": completed,
            "input_tokens": in_tok, "output_tokens": out_tok,
            "finish_reason": "length" if hit_cap else "stop", "hit_token_cap": hit_cap,
            "output_text": text, "output_hash": _sha(text),
            "backend_metadata": {"endpoint_type": "local_huggingface",
                                 "transformers_generate": True},
            "status": "completed"}
        tmp = outfile + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False)
        os.replace(tmp, outfile)             # atomic persist
        done += 1
        print(f"[{args.role}] {done}/{len(plan['item_ids'])} {item_id} "
              f"out_tok={out_tok} cap={hit_cap}", flush=True)
    print(f"[{args.role}] DONE {done}/{len(plan['item_ids'])}", flush=True)


if __name__ == "__main__":
    main()
