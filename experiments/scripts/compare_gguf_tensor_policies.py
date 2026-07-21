#!/usr/bin/env python3
"""Compare two GGUF tensor-policy inventories (from inventory_gguf_tensors.py)."""
import argparse
import json


def load(path):
    with open(path) as f:
        return json.load(f)


def diff_policies(ref, cand):
    """Compare two inventory dicts (from inventory_gguf_tensors) -> result dict."""
    rt = {t["name"]: t for t in ref["tensors"]}
    ct = {t["name"]: t for t in cand["tensors"]}
    ref_names, cand_names = set(rt), set(ct)

    missing = sorted(ref_names - cand_names)     # in ref, not in candidate
    extra = sorted(cand_names - ref_names)       # in candidate, not in ref
    common = ref_names & cand_names

    type_mismatch = []
    shape_mismatch = []
    for n in sorted(common):
        if rt[n]["ggml_type"] != ct[n]["ggml_type"]:
            type_mismatch.append({"name": n, "reference": rt[n]["ggml_type"],
                                  "candidate": ct[n]["ggml_type"]})
        if rt[n]["shape"] != ct[n]["shape"]:
            shape_mismatch.append({"name": n, "reference": rt[n]["shape"],
                                   "candidate": ct[n]["shape"]})

    # class count deltas
    rc, cc = ref.get("class_counts", {}), cand.get("class_counts", {})
    class_delta = {}
    for k in set(rc) | set(cc):
        if rc.get(k, 0) != cc.get(k, 0):
            class_delta[k] = {"reference": rc.get(k, 0), "candidate": cc.get(k, 0)}

    exact_match = (not missing and not extra and not type_mismatch
                   and not shape_mismatch)
    match_pct = (100.0 * sum(1 for n in common
                             if rt[n]["ggml_type"] == ct[n]["ggml_type"]
                             and rt[n]["shape"] == ct[n]["shape"])
                 / max(len(ref_names | cand_names), 1))

    result = {
        "total_tensor_count_ref": ref["total_tensors"],
        "total_tensor_count_cand": cand["total_tensors"],
        "total_count_diff": cand["total_tensors"] - ref["total_tensors"],
        "missing_in_candidate": missing,
        "extra_in_candidate": extra,
        "type_mismatches": type_mismatch,
        "shape_mismatches": shape_mismatch,
        "class_count_deltas": class_delta,
        "embedding_type_ref": ref.get("token_embedding_type"),
        "embedding_type_cand": cand.get("token_embedding_type"),
        "embedding_type_match": ref.get("token_embedding_type") == cand.get("token_embedding_type"),
        "separate_output_ref": ref.get("has_separate_output_weight"),
        "separate_output_cand": cand.get("has_separate_output_weight"),
        "separate_output_match": ref.get("has_separate_output_weight") == cand.get("has_separate_output_weight"),
        "norms_all_f32_ref": ref.get("norms_all_f32"),
        "norms_all_f32_cand": cand.get("norms_all_f32"),
        "exact_match_percent": round(match_pct, 3),
        "policy_exact_match": exact_match,
    }
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--output-json", required=True)
    args = ap.parse_args()

    result = diff_policies(load(args.reference), load(args.candidate))
    missing = result["missing_in_candidate"]
    extra = result["extra_in_candidate"]
    type_mismatch = result["type_mismatches"]
    shape_mismatch = result["shape_mismatches"]
    exact_match = result["policy_exact_match"]
    with open(args.output_json, "w") as f:
        json.dump(result, f, indent=2)

    print("=== POLICY COMPARISON ===")
    print(f"tensors ref={result['total_tensor_count_ref']} "
          f"cand={result['total_tensor_count_cand']} diff={result['total_count_diff']}")
    print(f"missing={len(missing)} extra={len(extra)} "
          f"type_mismatch={len(type_mismatch)} shape_mismatch={len(shape_mismatch)}")
    print(f"embedding: ref={result['embedding_type_ref']} "
          f"cand={result['embedding_type_cand']} match={result['embedding_type_match']}")
    print(f"separate_output match={result['separate_output_match']} "
          f"(ref={result['separate_output_ref']} cand={result['separate_output_cand']})")
    print(f"exact_match_percent={result['exact_match_percent']}")
    print("POLICY EXACT MATCH" if exact_match else "POLICY MISMATCH")
    if type_mismatch[:10]:
        print("first type mismatches:")
        for m in type_mismatch[:10]:
            print(f"  {m['name']}: {m['reference']} -> {m['candidate']}")


if __name__ == "__main__":
    main()
