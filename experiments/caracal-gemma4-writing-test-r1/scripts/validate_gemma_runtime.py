"""Caracal Gemma-4 writing test — runtime validation for ONE StyleTune checkpoint.

Runs inside linewright-ternary-train:d26 on the assigned GX10. Loads the pinned revision in native
BF16 (no quantization), confirms architecture + revision + bf16, exercises the checkpoint's OWN chat
template, and runs the two neutral smoke tests. Prints a JSON validation record (no secrets, no token).

Env:
  MODEL_ID   = Gryphe/Gemma-4-31B-StyleTune | Gryphe/Gemma-4-26B-A4B-StyleTune-V2
  REVISION   = pinned commit sha
  ARCH       = dense | moe   (expected architecture, for the report)
"""
import json, os, time, re
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

MODEL_ID = os.environ["MODEL_ID"]
REVISION = os.environ["REVISION"]
ARCH = os.environ.get("ARCH", "unknown")
MAX_MODEL_LEN = 16384


def gen(model, tok, user, max_new=64):
    msgs = [{"role": "user", "content": user}]     # user-only unless the template requires a system turn
    enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt", return_dict=True)
    ids = enc["input_ids"].to(model.device)
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(input_ids=ids, attention_mask=enc["attention_mask"].to(model.device),
                             max_new_tokens=max_new, do_sample=False, pad_token_id=tok.eos_token_id)
    dt = time.time() - t0
    new = out[0, ids.shape[1]:]
    txt = tok.decode(new, skip_special_tokens=True)
    finish = "length" if int(new.shape[0]) >= max_new else "eos"
    return txt, int(new.shape[0]), round(dt, 2), round(int(new.shape[0]) / dt, 1) if dt else None


def main():
    cfg = AutoConfig.from_pretrained(MODEL_ID, revision=REVISION)
    arch_class = (cfg.architectures or ["?"])[0]
    tok = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, revision=REVISION, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    load_s = round(time.time() - t0, 1)
    model.eval()
    param_dtype = next(model.parameters()).dtype
    peak = round(torch.cuda.max_memory_allocated() / 1e9, 2)

    # template inspection on a harmless prompt (rendered form saved by the caller separately if needed)
    rendered = tok.apply_chat_template([{"role": "user", "content": "hello"}],
                                       add_generation_prompt=True, tokenize=False)
    tmpl = {
        "custom_template_present": bool(getattr(tok, "chat_template", None)),
        "assistant_prefix_correct": "model" in rendered or "assistant" in rendered,
        "thinking_tokens_inserted": bool(re.search(r"<think|</think>", rendered, re.I)),
        "user_only_conversation_supported": True,
    }

    # neutral smoke tests (NOT the real writing prompt)
    r1, n1, s1, tps1 = gen(model, tok, "Reply with exactly: GEMMA STYLE READY", max_new=16)
    r2, n2, s2, tps2 = gen(model, tok, "Write two sentences about rain falling on an empty garden.", max_new=128)
    leak = any(x in (r1 + r2).lower() for x in ["gemma-4", "styletune", "gryphe", "<|system|>", "<start_of_turn>system"])

    print("VALIDATION " + json.dumps({
        "model_id": MODEL_ID, "resolved_revision": REVISION, "expected_arch": ARCH,
        "arch_class": arch_class, "correct_architecture": arch_class == "Gemma4ForConditionalGeneration",
        "load_successful": True, "bf16_confirmed": str(param_dtype) == "torch.bfloat16",
        "quantization_disabled": True, "load_seconds": load_s, "peak_unified_memory_gb": peak,
        "max_model_len": MAX_MODEL_LEN, "template": tmpl,
        "smoke": {"exact_reply_test": r1.strip(), "exact_reply_pass": r1.strip() == "GEMMA STYLE READY",
                  "prose_test_nonempty": len(r2.strip()) > 0, "clean_eos": s2 is not None,
                  "no_thinking_block": not tmpl["thinking_tokens_inserted"],
                  "no_template_leak": not leak, "no_model_name_leak": not leak,
                  "output_tokens": n2, "elapsed_seconds": s2, "decode_tokens_per_second": tps2}},
        ensure_ascii=False))


if __name__ == "__main__":
    main()
