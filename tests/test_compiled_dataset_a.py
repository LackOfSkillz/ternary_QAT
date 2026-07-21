"""Tests for the deterministic Dataset A compiler and frozen splits.

Operates on the committed experimental-v1 artifacts and recompiles into a throwaway
subdir to prove byte-for-byte determinism.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

_HERE = os.path.dirname(__file__)
_DA = os.path.abspath(os.path.join(_HERE, "..", "datasets", "dataset-a"))
_COMPILED = os.path.join(_DA, "compiled", "experimental-v1")
_SCRIPTS = os.path.join(_DA, "scripts")
_SYS_PROMPT = os.path.join(_DA, "prompts", "linewright-training-system-v1.txt")

yaml = pytest.importorskip("yaml")


def _load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")]


def _train():
    return _load(os.path.join(_COMPILED, "train.jsonl"))


def _eval():
    return _load(os.path.join(_COMPILED, "evaluation.jsonl"))


def test_counts_and_no_leakage():
    tr, ev = _train(), _eval()
    assert len(tr) == 28 and len(ev) == 7
    tr_ids = {r["id"] for r in tr}
    ev_ids = {r["id"] for r in ev}
    assert tr_ids.isdisjoint(ev_ids)
    assert len(tr_ids | ev_ids) == 35            # all frozen records accounted for


def test_unique_ids_and_parse():
    tr, ev = _train(), _eval()
    ids = [r["id"] for r in tr + ev]
    assert len(ids) == len(set(ids))
    for r in tr + ev:
        assert r["messages"][0]["role"] == "system"
        assert r["messages"][2]["role"] == "assistant"
        assert r["messages"][2]["content"].strip()


def test_no_rejected_or_notes_leak_in_targets():
    for r in _train() + _eval():
        c = r["messages"][2]["content"]
        for leak in ("Rejection Reasons", "Reviewer Notes", "Protected Elements"):
            assert leak not in c


def test_structured_no_change_targets_are_valid_json():
    # dsa-revision-019 (train) and dsa-revision-002 (eval) are structured no-change
    seen = 0
    for r in _train() + _eval():
        if r["id"] in ("dsa-revision-019", "dsa-revision-002"):
            obj = json.loads(r["messages"][2]["content"])
            assert obj["changed"] is False
            seen += 1
    assert seen == 2


def test_all_train_rows_have_source_hash():
    for r in _train() + _eval():
        assert len(r["metadata"]["source_hash"]) == 64


def test_manifest_hashes_match_files():
    man = json.load(open(os.path.join(_COMPILED, "manifest.json"), encoding="utf-8"))
    import hashlib
    for _key, meta in man["files"].items():
        p = os.path.join(_COMPILED, meta["path"])
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        assert h == meta["sha256"]


def test_deterministic_recompile(tmp_path):
    # recompile into a throwaway subdir twice; bytes must match each other AND the
    # committed train.jsonl
    sub = "_pytest_determinism"
    outdir = os.path.join(_DA, "compiled", sub)
    try:
        def run():
            subprocess.run([sys.executable, os.path.join(_SCRIPTS, "compile_dataset_a.py"),
                            "--root", _DA, "--out-subdir", sub,
                            "--freeze-id", "dataset-a-experimental-v1",
                            "--system-prompt", _SYS_PROMPT],
                           check=True, capture_output=True)
            return open(os.path.join(outdir, "train.jsonl"), "rb").read()
        a = run()
        b = run()
        committed = open(os.path.join(_COMPILED, "train.jsonl"), "rb").read()
        assert a == b
        assert a == committed
    finally:
        shutil.rmtree(outdir, ignore_errors=True)


def test_compiled_validator_passes():
    r = subprocess.run([sys.executable, os.path.join(_SCRIPTS, "validate_compiled.py"),
                        "--root", _DA, "--out-subdir", "experimental-v1"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ALL COMPILED ARTIFACTS VALID" in r.stdout
