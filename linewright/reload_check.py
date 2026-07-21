"""Fresh-process checkpoint reload check (invoked by runtime.verify_checkpoint_reload).

Supports three checkpoint types, distinguished by an on-disk marker:
  - stub  : adapter.json           (Dispatch 18A CPU stub)
  - lora  : lw-checkpoint.json type=lora        (real PEFT adapter)
  - ternary-qat : lw-checkpoint.json type=ternary-qat (real swapped state dict)

It loads in a FRESH process (never reusing a live training object), generates one
short response, and prints a single JSON result line.
"""
import argparse
import json
import os
import time


def detect_type(ckpt):
    """Return the checkpoint type from on-disk markers: lora | ternary-qat | stub."""
    marker_path = os.path.join(ckpt, "lw-checkpoint.json")
    if os.path.isfile(marker_path):
        return json.load(open(marker_path, encoding="utf-8"))["checkpoint_type"]
    if os.path.isfile(os.path.join(ckpt, "adapter.json")):
        return "stub"
    return "unknown"


def _reload_stub(ckpt):
    from linewright.backends import StubBackend
    model = StubBackend.load_checkpoint(ckpt)
    out = model.generate([{"role": "user", "content": "Reload check."}],
                         {"temperature": 0, "max_new_tokens": 16})
    return {"checkpoint_type": "stub", "model_init": True, "tokenizer_init": True,
            "output": out, "output_nonempty": bool(out and out.strip()), "ok": True}


def _generate_once(model, tokenizer, device):
    import torch
    from linewright import collate
    msgs = [{"role": "user", "content": "Reload check: produce one short line."}]
    ids = collate.build_generation_ids(tokenizer, msgs)
    input_ids = torch.tensor([ids]).to(device)
    with torch.no_grad():
        out = model.generate(input_ids, max_new_tokens=16,
                             pad_token_id=tokenizer.pad_token_id, do_sample=False,
                             temperature=None, top_p=None)
    return tokenizer.decode(out[0][len(ids):], skip_special_tokens=True)


def _reload_hf(ckpt, marker):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    base = marker.get("base_model_path")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(base, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base, torch_dtype=torch.bfloat16, attn_implementation="sdpa",
        local_files_only=True)
    missing, unexpected = [], []
    ctype = marker["checkpoint_type"]
    if ctype == "lora":
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, ckpt)
    elif ctype == "ternary-qat":
        from ternary.swap import swap_linear

        class _C:
            group_size = marker.get("group_size", 128)
        swap_linear(model, _C())
        state = torch.load(os.path.join(ckpt, "qat_state.pt"), map_location="cpu")
        res = model.load_state_dict(state, strict=False)
        missing, unexpected = list(res.missing_keys), list(res.unexpected_keys)
    model.to(device).eval()
    load_secs = round(time.time() - t0, 2)
    out = _generate_once(model, tokenizer, device)
    return {"checkpoint_type": ctype, "model_init": True, "tokenizer_init": True,
            "model_class": type(model).__name__,
            "tokenizer_class": type(tokenizer).__name__,
            "load_seconds": load_secs, "missing_keys": len(missing),
            "unexpected_keys": len(unexpected), "output": out,
            "output_nonempty": bool(out and out.strip()),
            "cuda_peak_mb": (round(torch.cuda.max_memory_allocated() / 2**20, 1)
                             if device == "cuda" else None),
            "ok": bool(out and out.strip())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--backend", default="stub")
    args = ap.parse_args()
    ckpt = args.checkpoint
    result = {"ok": False, "checkpoint": ckpt, "backend": args.backend}
    try:
        marker_path = os.path.join(ckpt, "lw-checkpoint.json")
        if os.path.isfile(marker_path):
            marker = json.load(open(marker_path, encoding="utf-8"))
            result.update(_reload_hf(ckpt, marker))
        else:
            result.update(_reload_stub(ckpt))
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
