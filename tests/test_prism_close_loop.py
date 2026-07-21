"""Tests for the Prism close-the-loop tooling: tensor-policy comparison,
torch-vs-Prism classification, and the torch fixture's scale/level derivation."""
import os
import sys

import numpy as np
import pytest

_SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "experiments", "scripts")
_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _SCRIPTS)
sys.path.insert(0, _ROOT)

import compare_gguf_tensor_policies as pol  # noqa: E402
import compare_actual_torch_vs_prism as cmp  # noqa: E402


def _inv(tensors, **kw):
    from collections import Counter
    tc = Counter(f'{t["ggml_type"]}' for t in tensors)
    d = {
        "total_tensors": len(tensors),
        "tensors": tensors,
        "class_counts": dict(Counter(t.get("tensor_class", "other") for t in tensors)),
        "token_embedding_type": next((t["ggml_type"] for t in tensors
                                      if t.get("tensor_class") == "token_embedding"), None),
        "has_separate_output_weight": any(t["name"] == "output.weight" for t in tensors),
        "norms_all_f32": True,
    }
    d.update(kw)
    return d


def _t(name, typ, shape, cls):
    return {"name": name, "ggml_type": typ, "shape": shape, "tensor_class": cls}


# ---- tensor-policy comparison ----
def test_policy_exact_match():
    tensors = [_t("token_embd.weight", "Q2_0", [2560, 100], "token_embedding"),
               _t("blk.0.attn_q.weight", "Q2_0", [2560, 2560], "attention_q")]
    r = pol.diff_policies(_inv(tensors), _inv([dict(x) for x in tensors]))
    assert r["policy_exact_match"] is True
    assert r["exact_match_percent"] == 100.0
    assert r["embedding_type_match"] is True


def test_policy_embedding_type_mismatch():
    ref = [_t("token_embd.weight", "Q2_0", [2560, 100], "token_embedding")]
    cand = [_t("token_embd.weight", "Q6_K", [2560, 100], "token_embedding")]
    r = pol.diff_policies(_inv(ref), _inv(cand))
    assert r["policy_exact_match"] is False
    assert r["embedding_type_match"] is False
    assert len(r["type_mismatches"]) == 1


def test_policy_missing_and_extra():
    ref = [_t("a.weight", "Q2_0", [4, 4], "other"),
           _t("b.weight", "Q2_0", [4, 4], "other")]
    cand = [_t("a.weight", "Q2_0", [4, 4], "other"),
            _t("c.weight", "Q2_0", [4, 4], "other")]
    r = pol.diff_policies(_inv(ref), _inv(cand))
    assert r["missing_in_candidate"] == ["b.weight"]
    assert r["extra_in_candidate"] == ["c.weight"]


def test_policy_shape_mismatch():
    ref = [_t("a.weight", "Q2_0", [4, 128], "other")]
    cand = [_t("a.weight", "Q2_0", [4, 256], "other")]
    r = pol.diff_policies(_inv(ref), _inv(cand))
    assert len(r["shape_mismatches"]) == 1
    assert r["policy_exact_match"] is False


# ---- torch-vs-Prism classification ----
def test_classify_confirmed():
    assert cmp.classify(0, 1.2e-4) == "artifact-level equivalence confirmed"


def test_classify_partial_on_large_scale_err():
    # off-boundary clean but scale error beyond fp16 tolerance
    assert cmp.classify(0, 1e-2) == "artifact-level equivalence partially confirmed"


def test_classify_rejected_on_off_boundary_mismatch():
    assert cmp.classify(3, 1e-5) == "artifact-level equivalence rejected"


# ---- torch fixture scale/level derivation (numpy only, no torch needed) ----
def test_derive_levels_scales_from_dequant():
    exp = pytest.importorskip("numpy")  # always present; keeps torch optional
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "expfix", os.path.join(_SCRIPTS, "export_actual_torch_ternary_fixture.py"))
    # import only the pure-numpy helper without executing torch import at module top
    # (module imports torch at top; skip cleanly if torch/ternary unavailable)
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception:
        pytest.skip("torch/ternary not importable in this env")
    deq = np.array([[0.5, 0.0, -0.5] + [0.0] * 125], dtype=np.float32)  # scale 0.5
    levels, scales = mod.derive_levels_scales(deq, 128)
    assert scales[0] == pytest.approx(0.5)
    assert levels[0, 0] == 1 and levels[0, 1] == 0 and levels[0, 2] == -1
