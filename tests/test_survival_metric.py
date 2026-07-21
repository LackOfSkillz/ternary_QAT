"""Deterministic tests for the quantization-survival metric scaffold."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "experiments", "scripts"))
import measure_quant_survival as m  # noqa: E402


def _probs(rows):
    a = np.asarray(rows, dtype=np.float64)
    return a / a.sum(axis=-1, keepdims=True)


P = _probs([[0.7, 0.2, 0.1], [0.2, 0.5, 0.3]])       # base-ish
Q = _probs([[0.1, 0.2, 0.7], [0.3, 0.5, 0.2]])       # trained-ish (differs)


def test_zero_difference_both_representations():
    r = m.survival(P, P, P, P)
    assert r["global"]["D_bf16_mean"] == pytest.approx(0.0, abs=1e-9)
    assert r["global"]["D_pack_mean"] == pytest.approx(0.0, abs=1e-9)
    # every denominator is near zero -> ratio undefined for all
    assert r["global"]["denominator_near_zero_count"] == P.shape[0]


def test_nonzero_bf16_zero_packed_gives_zero_survival():
    # base->trained moves at bf16, but packed base==packed trained (movement lost)
    r = m.survival(P, Q, P, P)
    assert r["global"]["D_bf16_mean"] > 0
    assert r["global"]["D_pack_mean"] == pytest.approx(0.0, abs=1e-9)
    assert r["global"]["survival_ratio_of_means"] == pytest.approx(0.0, abs=1e-9)


def test_equal_bf16_and_packed_difference_gives_unit_survival():
    # identical movement at both representations -> survival ~1
    r = m.survival(P, Q, P, Q)
    assert r["global"]["survival_ratio_of_means"] == pytest.approx(1.0, rel=1e-9)


def test_amplified_packed_difference_gives_high_survival():
    # packed movement larger than bf16 movement -> ratio > 1
    small = _probs([[0.5, 0.3, 0.2]])
    near = _probs([[0.49, 0.31, 0.20]])   # tiny bf16 move
    far = _probs([[0.05, 0.15, 0.80]])    # big packed move
    r = m.survival(small, near, small, far)
    assert r["global"]["survival_ratio_of_means"] > 1.0


def test_near_zero_denominator_counted():
    near = _probs([[0.5, 0.3, 0.2], [0.5, 0.3, 0.2]])
    same = near.copy()
    moved = _probs([[0.1, 0.2, 0.7], [0.2, 0.3, 0.5]])
    r = m.survival(near, same, near, moved, near_zero=1e-3)
    assert r["global"]["denominator_near_zero_count"] == 2
    # per-example ratios undefined -> mean is None
    assert r["global"]["survival_ratio_per_example_mean"] is None


def test_nonfinite_input_rejected_from_stats():
    bad_T = P.copy()
    bad_T[0, 0] = np.nan
    r = m.survival(P, bad_T, P, Q)
    assert r["global"]["invalid_nonfinite_count"] >= 1


def test_per_task_aggregation():
    tasks = np.array(["canon", "fiction"])
    r = m.survival(P, Q, P, Q, tasks=tasks)
    assert set(r["per_task"].keys()) == {"canon", "fiction"}
    for t in ("canon", "fiction"):
        assert r["per_task"][t]["survival_ratio_of_means"] == pytest.approx(1.0, rel=1e-9)


def test_seed_aggregation_ci():
    agg = m.aggregate_seeds([0.9, 1.0, 1.1, 1.0])
    assert agg["n"] == 4
    assert agg["mean"] == pytest.approx(1.0, rel=1e-9)
    assert agg["ci_low"] < agg["mean"] < agg["ci_high"]
    empty = m.aggregate_seeds([np.nan, np.inf])
    assert empty["n"] == 0 and empty["mean"] is None


def test_jsd_bounds():
    # JSD in [0, ln2]; identical -> 0, disjoint -> ln2
    p = _probs([[1.0, 0.0]])
    q = _probs([[0.0, 1.0]])
    assert m.jsd(p, p)[0] == pytest.approx(0.0, abs=1e-9)
    assert m.jsd(p, q)[0] == pytest.approx(np.log(2.0), rel=1e-6)
