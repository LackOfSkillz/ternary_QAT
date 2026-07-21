#!/usr/bin/env python3
"""Emit a JSON tensor-policy inventory of a GGUF file.

Reads with gguf-py's GGUFReader (supply the Prism fork's gguf-py on PYTHONPATH
so GGML_TYPE_Q2_0=42 resolves by name; unknown types still report by number).
No model load, no runtime. Read-only.
"""
import argparse
import json
from collections import Counter

from gguf import GGUFReader

# GGML block sizes (elements per block) and bytes per block for a byte estimate.
# Only the types we expect here need be exact; others fall back to None.
_BLK = {  # type_num: (block_elems, block_bytes)
    0: (1, 4),     # F32
    1: (1, 2),     # F16
    35: (256, 66), # TQ2_0 (2 + 256/4)
    42: (128, 34), # Q2_0 Prism (2 + 128/4)
    14: (256, 210),# Q6_K (approx: 210 bytes/256)
    12: (256, 144),# Q4_K (approx: 144 bytes/256)
}


def classify(name):
    if name == "token_embd.weight" or name.endswith("token_embd.weight"):
        return "token_embedding"
    if name == "output.weight":
        return "lm_head_or_output"
    if name.endswith("attn_q.weight"):
        return "attention_q"
    if name.endswith("attn_k.weight"):
        return "attention_k"
    if name.endswith("attn_v.weight"):
        return "attention_v"
    if name.endswith("attn_output.weight"):
        return "attention_o"
    if name.endswith("ffn_gate.weight"):
        return "mlp_gate"
    if name.endswith("ffn_up.weight"):
        return "mlp_up"
    if name.endswith("ffn_down.weight"):
        return "mlp_down"
    if "norm" in name:
        return "normalization"
    return "other"


def byte_estimate(type_num, n_elements):
    if type_num not in _BLK:
        return None
    be, bb = _BLK[type_num]
    if n_elements % be:
        return None
    return (n_elements // be) * bb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gguf", required=True)
    ap.add_argument("--output-json", required=True)
    args = ap.parse_args()

    r = GGUFReader(args.gguf)
    tensors = []
    type_counts = Counter()
    class_counts = Counter()
    for t in r.tensors:
        tt = t.tensor_type
        tnum = int(tt)
        tname = getattr(tt, "name", str(tnum))
        n_elem = int(t.n_elements)
        cls = classify(t.name)
        type_counts[f"{tname}({tnum})"] += 1
        class_counts[cls] += 1
        tensors.append({
            "name": t.name,
            "shape": [int(x) for x in t.shape],
            "n_elements": n_elem,
            "ggml_type": tname,
            "ggml_type_num": tnum,
            "stored_bytes_estimate": byte_estimate(tnum, n_elem),
            "tensor_class": cls,
        })

    names = {t["name"] for t in tensors}
    has_output = "output.weight" in names
    embd = next((t for t in tensors if t["tensor_class"] == "token_embedding"), None)
    embd_type = embd["ggml_type"] if embd else None
    norms = [t for t in tensors if t["tensor_class"] == "normalization"]
    norms_all_f32 = all(t["ggml_type"] == "F32" for t in norms) if norms else None
    q2_0_names = {"Q2_0"}
    embd_is_q2_0 = embd is not None and embd["ggml_type"] in q2_0_names

    out = {
        "path": args.gguf,
        "total_tensors": len(tensors),
        "type_counts": dict(type_counts),
        "class_counts": dict(class_counts),
        "has_separate_output_weight": has_output,
        "token_embedding_type": embd_type,
        "embeddings_are_q2_0": embd_is_q2_0,
        "norms_all_f32": norms_all_f32,
        "inferred_tied_output": (not has_output),
        "tensors": tensors,
    }
    with open(args.output_json, "w") as f:
        json.dump(out, f, indent=2)
    print(f"total={len(tensors)} types={dict(type_counts)}")
    print(f"token_embd={embd_type} embeddings_q2_0={embd_is_q2_0} "
          f"separate_output={has_output} norms_all_f32={norms_all_f32} "
          f"tied={not has_output}")


if __name__ == "__main__":
    main()
