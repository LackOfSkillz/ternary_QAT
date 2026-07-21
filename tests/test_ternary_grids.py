"""Fixture tests for ternary-grid math equivalence and differences.

These are the repository's first formal tests. They compare the pure-Python
reference implementations of ternary_QAT fake-quant, Prism Q2_0 (g128), and
upstream TQ2_0 (g256). See experiments/scripts/compare_ternary_grids.py.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "experiments", "scripts"))
import compare_ternary_grids as g  # noqa: E402


def test_exact_zeros_all_impls():
    w = np.zeros((2, 128), dtype=np.float32)
    for impl, grp in [(g.ternary_qat, 128), (g.prism_q2_0, 128),
                      (g.upstream_tq2_0, 128)]:
        out = impl(w, group=grp)
        assert np.all(out["levels"] == 0)
        assert np.allclose(out["deq"], 0.0)


def test_qat_prism_agree_off_boundary():
    # random values scaled so almost none sit exactly on a +/-0.5 boundary
    rng = np.random.default_rng(1)
    w = rng.standard_normal((8, 128)).astype(np.float32)
    a = g.ternary_qat(w, 128)
    p = g.prism_q2_0(w, 128)
    # same grid: levels identical off-boundary
    assert np.array_equal(a["levels"], p["levels"])
    # dequant differs only by fp16 scale storage -> small relative error
    denom = np.maximum(np.abs(a["deq"]), 1e-6)
    assert np.max(np.abs(a["deq"] - p["deq"]) / denom) < 5e-3


def test_half_boundary_rounding_differs():
    # value exactly 0.5*amax: half-even (qat) -> 0 ; half-away (prism) -> 1
    w = np.array([[1.0, 0.5, 0.0] + [0.0] * 125], dtype=np.float32)  # amax=1.0
    a = g.ternary_qat(w, 128)
    p = g.prism_q2_0(w, 128)
    assert a["levels"][0, 1] == 0      # torch.round(0.5) == 0
    assert p["levels"][0, 1] == 1      # roundf(0.5) == 1
    # negative boundary too
    w2 = np.array([[1.0, -0.5, 0.0] + [0.0] * 125], dtype=np.float32)
    assert g.ternary_qat(w2, 128)["levels"][0, 1] == 0
    assert g.prism_q2_0(w2, 128)["levels"][0, 1] == -1


def test_just_below_and_above_boundary_agree():
    # 0.49 -> 0 ; 0.51 -> 1 in BOTH rounding conventions
    w = np.array([[1.0, 0.49, 0.51] + [0.0] * 125], dtype=np.float32)
    a = g.ternary_qat(w, 128)
    p = g.prism_q2_0(w, 128)
    assert a["levels"][0, 1] == 0 and p["levels"][0, 1] == 0
    assert a["levels"][0, 2] == 1 and p["levels"][0, 2] == 1


def test_positive_negative_extremes():
    w = np.array([[1.0, -1.0] + [0.0] * 126], dtype=np.float32)
    for impl in (g.ternary_qat, g.prism_q2_0):
        out = impl(w, 128)
        assert out["levels"][0, 0] == 1
        assert out["levels"][0, 1] == -1


def test_all_zero_group_no_nan():
    w = np.zeros((1, 128), dtype=np.float32)
    for impl in (g.ternary_qat, g.prism_q2_0, g.upstream_tq2_0):
        out = impl(w, 128)
        assert np.all(np.isfinite(out["deq"]))
        assert np.allclose(out["deq"], 0.0)


def test_single_outlier_dominates_scale():
    # one large value sets amax; the rest normalize to ~0
    w = np.zeros((1, 128), dtype=np.float32)
    w[0, 0] = 10.0
    w[0, 1] = 0.1  # 0.1/10 = 0.01 -> rounds to 0
    p = g.prism_q2_0(w, 128)
    assert p["levels"][0, 0] == 1
    assert p["levels"][0, 1] == 0


def test_group_size_changes_grid():
    # same tensor, g64 vs g128 -> different scales -> can change levels
    rng = np.random.default_rng(7)
    w = rng.standard_normal((2, 128)).astype(np.float32)
    # compare dequantized values (original tensor shape) — the grids differ
    d64 = g.ternary_qat(w, 64)["deq"]
    d128 = g.ternary_qat(w, 128)["deq"]
    assert d64.shape == d128.shape == w.shape
    assert not np.allclose(d64, d128)


def test_prism_differs_from_upstream_group_size():
    # prism g128 vs upstream g256 on same data -> generally different dequant
    rng = np.random.default_rng(3)
    w = (rng.standard_normal((4, 256)) * 2).astype(np.float32)
    p = g.prism_q2_0(w, 128)["deq"]
    u = g.upstream_tq2_0(w, 256)["deq"]
    assert not np.allclose(p, u)


@pytest.mark.parametrize("group", [64, 128])
def test_embedding_shaped_tensor_runs(group):
    # tied-embedding-shaped: (vocab, hidden) with hidden % group == 0
    vocab, hidden = 200, 256
    rng = np.random.default_rng(11)
    w = (rng.standard_normal((vocab, hidden)) * 0.05).astype(np.float32)
    for impl in (g.ternary_qat, g.prism_q2_0):
        out = impl(w, group)
        assert out["deq"].shape == (vocab, hidden)
        assert np.all(np.isfinite(out["deq"]))
