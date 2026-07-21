#!/usr/bin/env python3
"""Quantization-survival metric — SCAFFOLD (format-independent logic only).

Implements the difference-of-differences survival metric defined in
docs/quantization-survival-metric.md. This dispatch implements ONLY the math
over pre-collected distributions; it does NOT load any model or runtime. A
later dispatch adds collection once the deployment grid is confirmed.

Four model states, each providing a next-token distribution per (example,
position):
  B_bf16 = untouched BF16 base
  T_bf16 = trained BF16 model
  B_pack = untouched packed model
  T_pack = trained packed model

  D_bf16 = JSD(B_bf16, T_bf16)        # behavioral movement before packing
  D_pack = JSD(B_pack, T_pack)        # behavioral movement after packing
  survival_ratio = D_pack / D_bf16    # with an explicit near-zero policy

Input (`--input`): an .npz (or .np[yz]) whose arrays are probabilities or logits
of shape (N, V) or (N, T, V) for the four states, plus a 'tasks' string array of
length N. Keys: probs_B_bf16/probs_T_bf16/probs_B_pack/probs_T_pack (or
logits_*). Optional 'seeds' (N,) integer array for CI-across-seeds.
"""
import argparse
import json

import numpy as np

EPS = 1e-8
LN2 = float(np.log(2.0))


def _softmax(x):
    x = x - np.max(x, axis=-1, keepdims=True)
    e = np.exp(x)
    return e / np.clip(np.sum(e, axis=-1, keepdims=True), EPS, None)


def _kl(p, q):
    p = np.clip(p, EPS, 1.0)
    q = np.clip(q, EPS, 1.0)
    return np.sum(p * (np.log(p) - np.log(q)), axis=-1)


def jsd(p, q):
    """Jensen-Shannon divergence (natural log), per row over the last axis."""
    m = 0.5 * (p + q)
    return 0.5 * _kl(p, m) + 0.5 * _kl(q, m)


def _to_probs(arr, is_logits):
    arr = np.asarray(arr, dtype=np.float64)
    if is_logits:
        arr = _softmax(arr)
    # collapse (N, T, V) -> treat each position as a sample by flattening N,T
    if arr.ndim == 3:
        arr = arr.reshape(-1, arr.shape[-1])
    return arr


def survival(B_bf16, T_bf16, B_pack, T_pack, tasks=None, near_zero=1e-4):
    d_bf16 = jsd(B_bf16, T_bf16)           # (M,)
    d_pack = jsd(B_pack, T_pack)           # (M,)
    finite = np.isfinite(d_bf16) & np.isfinite(d_pack)
    invalid = int((~finite).sum())
    d_bf16, d_pack = d_bf16[finite], d_pack[finite]
    if tasks is not None:
        tasks = np.asarray(tasks)
        # broadcast per-example tasks to per-position if flattened
        if tasks.shape[0] != d_bf16.shape[0] and d_bf16.shape[0] % tasks.shape[0] == 0:
            reps = d_bf16.shape[0] // tasks.shape[0]
            tasks = np.repeat(tasks, reps)
        tasks = tasks[finite] if tasks.shape[0] == finite.shape[0] else tasks

    denom_small = d_bf16 < near_zero
    denom_small_count = int(denom_small.sum())
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(denom_small, np.nan, d_pack / np.maximum(d_bf16, EPS))

    def agg(name, arr):
        valid = arr[np.isfinite(arr)]
        return {
            f"{name}_mean": float(np.mean(valid)) if valid.size else None,
            f"{name}_median": float(np.median(valid)) if valid.size else None,
            f"{name}_std": float(np.std(valid)) if valid.size else None,
            f"{name}_n": int(valid.size),
        }

    out = {
        "global": {
            "D_bf16_mean": float(np.mean(d_bf16)) if d_bf16.size else None,
            "D_pack_mean": float(np.mean(d_pack)) if d_pack.size else None,
            # global survival ratio = ratio of mean movements (robust to small denom)
            "survival_ratio_of_means": (float(np.mean(d_pack) / np.maximum(np.mean(d_bf16), EPS))
                                        if d_bf16.size else None),
            **agg("survival_ratio_per_example", ratio),
            "denominator_near_zero_count": denom_small_count,
            "invalid_nonfinite_count": invalid,
            "n_samples": int(d_bf16.size),
            "near_zero_threshold": near_zero,
        },
        "per_task": {},
    }
    if tasks is not None and tasks.shape[0] == d_bf16.shape[0]:
        for t in sorted(set(tasks.tolist())):
            mask = tasks == t
            db, dp, rr = d_bf16[mask], d_pack[mask], ratio[mask]
            out["per_task"][str(t)] = {
                "D_bf16_mean": float(np.mean(db)) if db.size else None,
                "D_pack_mean": float(np.mean(dp)) if dp.size else None,
                "survival_ratio_of_means": (float(np.mean(dp) / np.maximum(np.mean(db), EPS))
                                            if db.size else None),
                **agg("survival_ratio_per_example", rr),
            }
    return out


def aggregate_seeds(ratios, z=1.96):
    """Aggregate one survival-ratio value per seed into mean + normal CI.

    `ratios`: list/array of per-seed survival ratios (non-finite entries
    dropped). Returns mean, std, n, and a z*sem confidence interval.
    """
    arr = np.asarray(ratios, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    n = int(arr.size)
    if n == 0:
        return {"mean": None, "std": None, "n": 0, "ci_low": None, "ci_high": None}
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    sem = std / np.sqrt(n) if n > 1 else 0.0
    return {"mean": mean, "std": std, "n": n,
            "ci_low": mean - z * sem, "ci_high": mean + z * sem}


def _load(path, is_logits):
    data = np.load(path, allow_pickle=True)
    pre = "logits_" if is_logits else "probs_"
    states = {}
    for s in ["B_bf16", "T_bf16", "B_pack", "T_pack"]:
        key = pre + s
        if key not in data:
            raise SystemExit(f"missing array '{key}' in {path}")
        states[s] = _to_probs(data[key], is_logits)
    tasks = data["tasks"] if "tasks" in data else None
    return states, tasks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help=".npz with the four states")
    ap.add_argument("--logits", action="store_true",
                    help="arrays are logits (softmax applied); default probs")
    ap.add_argument("--near-zero", type=float, default=1e-4)
    ap.add_argument("--output-json", required=True)
    args = ap.parse_args()

    states, tasks = _load(args.input, args.logits)
    result = survival(states["B_bf16"], states["T_bf16"],
                      states["B_pack"], states["T_pack"],
                      tasks=tasks, near_zero=args.near_zero)
    with open(args.output_json, "w") as f:
        json.dump(result, f, indent=2)
    gl = result["global"]
    print("=== SURVIVAL SUMMARY ===")
    print(f"D_bf16_mean = {gl['D_bf16_mean']}")
    print(f"D_pack_mean = {gl['D_pack_mean']}")
    print(f"survival_ratio_of_means = {gl['survival_ratio_of_means']}")
    print(f"per-example survival mean = {gl['survival_ratio_per_example_mean']}")
    print(f"near-zero denom = {gl['denominator_near_zero_count']} | "
          f"invalid = {gl['invalid_nonfinite_count']} | n = {gl['n_samples']}")


if __name__ == "__main__":
    main()
