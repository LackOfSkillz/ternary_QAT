#!/usr/bin/env python3
"""Export a deterministic fixture through the REAL torch fake-quant
(`ternary.linear.ternarize_weight`) for artifact-level comparison against the
compiled Prism quantizer. Does NOT reimplement ternarize_weight.

Writes:
  <out>.npz : original fp32, torch dequant, derived torch levels + group scales
  <out>.bin : the original fp32 tensor, row-major (input for the C probe)
Group size is fixed to 128 (the Prism Q2_0 / ternary_QAT grid) and every row
length is a multiple of 128 so flat 128-blocks match torch's last-dim grouping.
"""
import argparse

import numpy as np
import torch

from ternary.linear import ternarize_weight  # the REAL function


def build_rows():
    """Return a single (R,128) fp32 matrix; each row is a labeled fixture case."""
    rows = []
    labels = []
    rng = np.random.default_rng(20260721)
    # random
    rows.append(rng.standard_normal(128).astype(np.float32)); labels.append("random_normal")
    rows.append((rng.standard_normal(128) * 4).astype(np.float32)); labels.append("random_wide")
    # exact zeros
    rows.append(np.zeros(128, np.float32)); labels.append("all_zeros")
    # boundary: amax=1, some values exactly +/-0.5
    b = np.zeros(128, np.float32); b[0] = 1.0; b[1] = 0.5; b[2] = -0.5; b[3] = -1.0
    rows.append(b); labels.append("exact_half_boundary")
    # just below / above boundary
    c = np.zeros(128, np.float32); c[0] = 1.0; c[1] = 0.49; c[2] = 0.51; c[3] = -0.51
    rows.append(c); labels.append("near_boundary")
    # single outlier dominates the scale
    d = np.zeros(128, np.float32); d[0] = 10.0; d[1] = 0.1; d[2] = -0.1
    rows.append(d); labels.append("single_outlier")
    # embedding-like small magnitudes
    rows.append((rng.standard_normal(128) * 0.03).astype(np.float32)); labels.append("embedding_like")
    return np.stack(rows), labels


def derive_levels_scales(deq, group=128):
    """Recover ternary levels and per-group scale from the REAL dequant output
    (deq = level*scale, level in {-1,0,1}); scale = max|deq| per group."""
    dg = deq.reshape(-1, group)
    scale = np.max(np.abs(dg), axis=1)                      # == fp32 amax when any level != 0
    safe = np.where(scale > 0, scale, 1.0)[:, None]
    levels = np.rint(dg / safe).astype(np.int8)
    return levels, scale.astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="output path prefix (no ext)")
    args = ap.parse_args()

    mat, labels = build_rows()                             # (R,128) fp32
    w = torch.from_numpy(mat)
    deq = ternarize_weight(w, 128).detach().cpu().numpy().astype(np.float32)
    levels, scales = derive_levels_scales(deq, 128)

    np.savez(args.out + ".npz", original=mat, torch_deq=deq,
             torch_levels=levels, torch_scales=scales,
             labels=np.array(labels))
    # raw fp32, row-major, for the C probe
    mat.astype("<f4").tofile(args.out + ".bin")
    print(f"rows={mat.shape[0]} group=128 elements={mat.size}")
    print("wrote", args.out + ".npz", "and", args.out + ".bin")


if __name__ == "__main__":
    main()
