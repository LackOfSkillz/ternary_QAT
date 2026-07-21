#!/usr/bin/env python3
"""Compare the REAL torch fake-quant fixture against the COMPILED Prism Q2_0
probe output. Both operated on the identical fp32 fixture (row-major, g128).

Inputs:
  --torch-npz    : from export_actual_torch_ternary_fixture.py (.npz)
  --prism-codes  : <prefix>.codes.i8 (int8 levels from prism_q2_0_probe)
  --prism-deq    : <prefix>.deq.f32  (fp32 dequant from prism_q2_0_probe)
"""
import argparse
import json

import numpy as np

GROUP = 128


def classify(off_boundary_mismatch_count, scale_rel_err_max, fp16_tol=2e-3):
    """Classify torch-vs-Prism artifact equivalence. Only UNEXPLAINED
    off-boundary code mismatches reject; known ±0.5 rounding and fp16-scale
    differences do not."""
    off_ok = off_boundary_mismatch_count == 0
    fp16_ok = scale_rel_err_max < fp16_tol
    if off_ok and fp16_ok:
        return "artifact-level equivalence confirmed"
    if off_ok:
        return "artifact-level equivalence partially confirmed"
    return "artifact-level equivalence rejected"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--torch-npz", required=True)
    ap.add_argument("--prism-codes", required=True)
    ap.add_argument("--prism-deq", required=True)
    ap.add_argument("--output-json", required=True)
    args = ap.parse_args()

    z = np.load(args.torch_npz, allow_pickle=True)
    orig = z["original"].astype(np.float32).ravel()
    t_lev = z["torch_levels"].astype(np.int8).ravel()
    t_deq = z["torch_deq"].astype(np.float32).ravel()
    labels = list(z["labels"]) if "labels" in z else []

    p_lev = np.fromfile(args.prism_codes, dtype=np.int8)
    p_deq = np.fromfile(args.prism_deq, dtype=np.float32)
    assert p_lev.size == t_lev.size == orig.size, (p_lev.size, t_lev.size, orig.size)

    # per-group scale recovered from each dequant (level*scale) == amax(input)
    def scales(deq):
        dg = deq.reshape(-1, GROUP)
        return np.max(np.abs(dg), axis=1)
    t_scale, p_scale = scales(t_deq), scales(p_deq)

    # exact-half-boundary mask: |w/amax| == 0.5 (where torch half-even and prism
    # half-away legitimately differ)
    ig = np.abs(orig).reshape(-1, GROUP)
    amax = np.max(ig, axis=1, keepdims=True)
    amax = np.where(amax > 0, amax, 1.0)
    frac = (orig.reshape(-1, GROUP) / amax).ravel()
    on_boundary = np.isclose(np.abs(frac), 0.5, atol=1e-6)

    code_match = (t_lev == p_lev)
    off_mismatch = np.where(~code_match & ~on_boundary)[0]
    boundary_mismatch = np.where(~code_match & on_boundary)[0]

    denom = np.maximum(np.abs(t_scale), 1e-12)
    scale_rel = np.abs(t_scale - p_scale) / denom
    deq_denom = np.maximum(np.abs(t_deq), 1e-12)
    deq_rel = np.abs(t_deq - p_deq) / deq_denom

    result = {
        "n_elements": int(orig.size),
        "group": GROUP,
        "labels": [str(x) for x in labels],
        "code_match_percent": round(100.0 * code_match.mean(), 4),
        "code_mismatch_total": int((~code_match).sum()),
        "off_boundary_mismatch_count": int(off_mismatch.size),
        "off_boundary_mismatch_rate": round(float((~code_match & ~on_boundary).mean()), 6),
        "exact_half_boundary_mismatch_count": int(boundary_mismatch.size),
        "exact_half_boundary_positions": off_mismatch[:0].tolist() or boundary_mismatch[:20].tolist(),
        "off_boundary_mismatch_positions": off_mismatch[:20].tolist(),
        "scale_abs_err_max": float(np.max(np.abs(t_scale - p_scale))),
        "scale_rel_err_max": float(np.max(scale_rel)),
        "dequant_abs_err_max": float(np.max(np.abs(t_deq - p_deq))),
        "dequant_abs_err_mean": float(np.mean(np.abs(t_deq - p_deq))),
        "dequant_rel_err_max": float(np.max(deq_rel)),
    }

    # Gate/classification
    off_boundary_ok = result["off_boundary_mismatch_count"] == 0
    klass = classify(result["off_boundary_mismatch_count"], result["scale_rel_err_max"])
    result["classification"] = klass

    with open(args.output_json, "w") as f:
        json.dump(result, f, indent=2)

    print("=== TORCH vs COMPILED-PRISM (artifact level) ===")
    print(f"code_match={result['code_match_percent']}%  "
          f"off_boundary_mismatch={result['off_boundary_mismatch_count']}  "
          f"exact_half_boundary_mismatch={result['exact_half_boundary_mismatch_count']}")
    print(f"scale_rel_err_max={result['scale_rel_err_max']:.3e}  "
          f"dequant_abs_err_max={result['dequant_abs_err_max']:.3e}")
    print("classification:", klass)
    # This tool does not fail on the known boundary/fp16 differences; it only
    # rejects UNEXPLAINED off-boundary code mismatches.
    if not off_boundary_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
