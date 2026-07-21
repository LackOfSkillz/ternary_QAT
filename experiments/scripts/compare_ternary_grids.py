#!/usr/bin/env python3
"""Directly compare the *math* of three ternary quantization grids, in pure
NumPy — no training, no compiled quantizer required.

Grids (see experiments/results/prism-format-characterization.md for source cites):

  ternary_QAT  : ternary/linear.py ternarize_weight
                 group=128, scale=amax (clamp 1e-8, kept fp32), round-half-EVEN
                 (torch.round), levels clamped to [-1,1].
  prism_q2_0   : PrismML-Eng/llama.cpp GGML_TYPE_Q2_0 (=42), ggml-quants.c
                 group=128, scale=amax stored fp16, round-half-AWAY (roundf),
                 code=clip(round(w/d),-1,2)+1, dequant=(code-1)*d_fp16.
  upstream_tq2_0: ggerganov/llama.cpp GGML_TYPE_TQ2_0, ggml-quants.c
                 group=256 (QK_K), scale=amax stored fp16, round-half-AWAY
                 (lroundf), levels {-1,0,1}, dequant=(q-1)*d_fp16.

Key expected results:
  * ternary_QAT(g128) ~= prism_q2_0(g128): SAME grid; differences only from
    (a) fp16 scale storage, (b) half-rounding at exact +/-0.5 boundaries.
  * ternary_QAT(g128) != upstream_tq2_0(g256): different group size.
"""
import argparse
import json

import numpy as np


# ---- rounding conventions ----
def round_half_even(x):      # torch.round / np.round (banker's)
    return np.round(x)


def round_half_away(x):      # C roundf / lroundf
    return np.sign(x) * np.floor(np.abs(x) + 0.5)


def _fp16(x):                # simulate fp16 storage round-trip
    return x.astype(np.float16).astype(np.float32)


# ---- reference implementations ----
def ternary_qat(w, group=128, eps=1e-8):
    shape = w.shape
    wg = w.reshape(-1, group).astype(np.float32)
    a = np.maximum(np.abs(wg).max(axis=1, keepdims=True), eps)
    levels = np.clip(round_half_even(wg / a), -1, 1)
    deq = (levels * a).reshape(shape)
    return {"levels": levels.astype(np.int8), "scale": a.reshape(-1),
            "deq": deq.astype(np.float32)}


def prism_q2_0(w, group=128):
    """Prism Q2_0 quantization MATH. The real Prism `GGML_TYPE_Q2_0` is fixed at
    group 128 (`QK2_0 = 128`); calling this with group != 128 is a purely
    HYPOTHETICAL mathematical parameterization for sensitivity analysis and is
    NOT evidence that the Prism fork supports any other group size."""
    shape = w.shape
    wg = w.reshape(-1, group).astype(np.float32)
    d = np.abs(wg).max(axis=1, keepdims=True)
    idv = np.where(d > 0, 1.0 / np.where(d > 0, d, 1.0), 0.0)
    code = np.clip(round_half_away(wg * idv) + 1, 0, 3)
    levels = code - 1                         # {-1,0,1,2}; in-range -> {-1,0,1}
    d16 = _fp16(d)
    deq = (levels * d16).reshape(shape)
    return {"levels": levels.astype(np.int8), "scale": d16.reshape(-1),
            "deq": deq.astype(np.float32)}


def upstream_tq2_0(w, group=256):
    shape = w.shape
    wg = w.reshape(-1, group).astype(np.float32)
    d = np.abs(wg).max(axis=1, keepdims=True)
    idv = np.where(d > 0, 1.0 / np.where(d > 0, d, 1.0), 0.0)
    levels = np.clip(round_half_away(wg * idv), -1, 2)
    d16 = _fp16(d)
    deq = (levels * d16).reshape(shape)
    return {"levels": levels.astype(np.int8), "scale": d16.reshape(-1),
            "deq": deq.astype(np.float32)}


IMPLS = {"ternary_qat": ternary_qat, "prism_q2_0": prism_q2_0,
         "upstream_tq2_0": upstream_tq2_0}


def compare(a, b):
    """Elementwise dequant comparison between two impl outputs on the same w."""
    da, db = a["deq"].ravel(), b["deq"].ravel()
    denom = np.maximum(np.abs(da), np.abs(db))
    denom = np.where(denom > 0, denom, 1.0)
    rel = np.abs(da - db) / denom
    # level agreement only meaningful when the grouping matches; compute anyway
    lev_match = None
    if a["levels"].size == b["levels"].size:
        lev_match = float((a["levels"].ravel() == b["levels"].ravel()).mean())
    return {
        "max_abs_err": float(np.max(np.abs(da - db))),
        "mean_abs_err": float(np.mean(np.abs(da - db))),
        "max_rel_err": float(np.max(rel)),
        "level_match_frac": lev_match,
        "deq_mismatch_frac": float((np.abs(da - db) > 1e-6).mean()),
    }


def make_tensors(seed):
    rng = np.random.default_rng(seed)
    tensors = {}
    # plain random, several shapes, cols divisible by lcm(64,128,256)=256
    tensors["rand_8x256"] = rng.standard_normal((8, 256)).astype(np.float32)
    tensors["rand_4x512"] = (rng.standard_normal((4, 512)) * 3).astype(np.float32)
    # ternary-valued base (like the unpacked model): {-1,0,1}*scale per g128
    base = rng.integers(-1, 2, size=(4, 256)).astype(np.float32)
    scale = rng.uniform(0.02, 0.2, size=(4, 256 // 128, 1))
    tensors["ternary_like_4x256"] = (base.reshape(4, 2, 128) * scale).reshape(4, 256).astype(np.float32)
    return tensors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260721)
    ap.add_argument("--output-json", default=None)
    ap.add_argument("--rel-tol", type=float, default=5e-3,
                    help="tolerance for pairs classified approximately-equivalent")
    args = ap.parse_args()

    tensors = make_tensors(args.seed)
    # (nameA, groupA, nameB, groupB, classification, enforce_tol_on_random)
    pairs = [
        ("ternary_qat", 128, "prism_q2_0", 128, "approximately_equivalent", True),
        ("prism_q2_0", 128, "upstream_tq2_0", 256, "not_equivalent", False),
        ("ternary_qat", 128, "upstream_tq2_0", 256, "not_equivalent", False),
        # HYPOTHETICAL g64: prism_reference_math_hypothetical_g64 — sensitivity
        # check only; the real Prism Q2_0 is g128 (QK2_0=128), not a g64 artifact.
        ("ternary_qat", 64, "prism_q2_0", 64, "approximately_equivalent_hypothetical_g64", True),
    ]

    results = []
    failures = []
    for na, ga, nb, gb, klass, enforce in pairs:
        per_tensor = {}
        worst_rel_random = 0.0
        for tname, w in tensors.items():
            if w.shape[1] % ga or w.shape[1] % gb:
                continue
            oa = IMPLS[na](w, group=ga)
            ob = IMPLS[nb](w, group=gb)
            m = compare(oa, ob)
            per_tensor[tname] = m
            if not tname.startswith("boundary"):
                worst_rel_random = max(worst_rel_random, m["max_rel_err"])
        entry = {"a": f"{na}(g{ga})", "b": f"{nb}(g{gb})",
                 "classification": klass, "per_tensor": per_tensor,
                 "worst_rel_err_random": worst_rel_random}
        results.append(entry)
        if enforce and worst_rel_random > args.rel_tol:
            failures.append(
                f"{na}(g{ga}) vs {nb}(g{gb}) classified {klass} but worst "
                f"rel err {worst_rel_random:.2e} > tol {args.rel_tol:.2e}")

    print("=== GRID MATH COMPARISON ===")
    for e in results:
        print(f"\n{e['a']}  vs  {e['b']}   [{e['classification']}]")
        for tname, m in e["per_tensor"].items():
            print(f"  {tname}: max_rel_err={m['max_rel_err']:.3e} "
                  f"level_match={m['level_match_frac']} "
                  f"deq_mismatch={m['deq_mismatch_frac']:.3f}")
        print(f"  worst_rel_err(random)={e['worst_rel_err_random']:.3e}")

    payload = {"seed": args.seed, "rel_tol": args.rel_tol, "pairs": results,
               "failures": failures}
    if args.output_json:
        with open(args.output_json, "w") as f:
            json.dump(payload, f, indent=2)

    if failures:
        print("\n=== FAILURES ===")
        for fmsg in failures:
            print("  !!", fmsg)
        raise SystemExit(1)
    print("\nGRID COMPARISON OK")


if __name__ == "__main__":
    main()
