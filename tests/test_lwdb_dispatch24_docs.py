"""Dispatch 24 — documentation + existing-invariant checks."""
import hashlib
import json
import os
import re

import pytest

yaml = pytest.importorskip("yaml")

HERE = os.path.dirname(__file__)
REPO = os.path.abspath(os.path.join(HERE, ".."))
RUN = os.path.join(REPO, "benchmarks", "runs", "lwdb-fast-v1-20260722")


def _read(p):
    return open(p, encoding="utf-8").read()


def test_readme_and_roadmap_mark_dispatch_24():
    r = _read(os.path.join(REPO, "README.md"))
    assert "fast battery" in r.lower() and "dual-GX10" in r
    rd = _read(os.path.join(REPO, "ROADMAP.md"))
    assert re.search(r"\*\*24\*\*.*current", rd) or re.search(r"24.*current", rd)
    for d in (25, 26, 27):
        assert re.search(rf"\b{d}\b", rd)


def test_training_pilot_documents_first_execution():
    t = _read(os.path.join(REPO, "TRAINING_PILOT.md"))
    assert "dual-GX10" in t and "frozen generation plan" in t
    assert "sequential" in t.lower() and "resume" in t.lower()


def test_changelog_records_dispatch_24():
    t = _read(os.path.join(REPO, "CHANGELOG.md"))
    assert "Dispatch 24" in t and "fast battery" in t.lower()


def test_run_artifacts_present_and_plan_verifies():
    for name in ("generation-plan.json", "endpoint-manifest.json", "run-manifest.json",
                 "preflight.json", "preliminary-report.md"):
        assert os.path.exists(os.path.join(RUN, name)), name
    from linewright.evaluation.execution.plan import verify_plan_hash
    plan = json.load(open(os.path.join(RUN, "generation-plan.json"), encoding="utf-8"))
    assert verify_plan_hash(plan)
    # no secrets serialized
    assert "api_key" not in json.dumps(plan).lower()


def test_run_manifest_excludes_qat20_and_names_candidate_exactly():
    m = json.load(open(os.path.join(RUN, "run-manifest.json"), encoding="utf-8"))
    assert m["candidate"]["checkpoint_path"].endswith("lora/checkpoints/step-20")
    assert "QAT-20 excluded" in m["candidate"]["selection_basis"]
    assert m["candidate"]["training_method"].startswith("LoRA")


def test_preliminary_report_makes_no_winner_claim():
    t = _read(os.path.join(RUN, "preliminary-report.md"))
    assert "insufficient_evidence" in t
    assert "deferred to Dispatch 25" in t.lower() or "deferred to dispatch 25" in t.lower()


def test_manifest_hashed_and_experimental():
    m = yaml.safe_load(open(os.path.join(REPO, "benchmarks", "manifests", "fast-battery-v1.yaml"),
                            encoding="utf-8"))
    assert m["battery_hash"] and m["status"] == "frozen"
    assert m["production_approved"] is False and m["experimental_use_only"] is True


def test_frozen_dataset_a_unchanged():
    cfg = yaml.safe_load(open(os.path.join(REPO, "training", "configs",
                        "dataset-a-lora-full-comparison-v1.yaml"), encoding="utf-8"))["dataset"]
    base = os.path.join(REPO, "datasets", "dataset-a", "compiled", "experimental-v1")
    for fname, pinned in (("train.jsonl", cfg["train_checksum"]),
                          ("evaluation.jsonl", cfg["evaluation_checksum"])):
        actual = hashlib.sha256(open(os.path.join(base, fname), "rb").read()).hexdigest()
        assert actual == pinned


def test_dataset_a2_pilot_unchanged():
    man = json.load(open(os.path.join(REPO, "datasets", "dataset-a.2", "pilot", "manifest.json"),
                         encoding="utf-8"))
    pilot = os.path.join(REPO, "datasets", "dataset-a.2", "pilot")

    def digest(rows):
        return hashlib.sha256("".join(json.dumps(r, ensure_ascii=False) for r in rows)
                              .encode("utf-8")).hexdigest()
    for fname, key in (("train.jsonl", "train_sha256"), ("evaluation.jsonl", "evaluation_sha256")):
        rows = [json.loads(l) for l in open(os.path.join(pilot, fname), encoding="utf-8") if l.strip()]
        assert digest(rows) == man[key]


def test_no_committed_ledger_or_output_dirs():
    import glob
    for pat in ("**/*.sqlite",):
        assert not glob.glob(os.path.join(RUN, pat), recursive=True)
