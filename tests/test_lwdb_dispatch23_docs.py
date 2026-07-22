"""Dispatch 23 — documentation, schema, and existing-invariant checks.

Docs are updated and link-clean; new schemas parse; calibration items live under
benchmarks/ (never a training dir) and are benchmark_only; Dataset A + A.2 are unchanged; no
training run or ordinary benchmark run occurred; no empirical thresholds were invented.
"""
import glob
import hashlib
import json
import os
import re

import pytest

yaml = pytest.importorskip("yaml")

HERE = os.path.dirname(__file__)
REPO = os.path.abspath(os.path.join(HERE, ".."))
BENCH = os.path.join(REPO, "benchmarks")
MANIFEST = os.path.join(BENCH, "manifests", "diagnostic-battery-architecture-v1.yaml")
DOCS = os.path.join(REPO, "training", "docs")


def _read(p):
    return open(p, encoding="utf-8").read()


def _load(p):
    return yaml.safe_load(open(p, encoding="utf-8"))


# ---- documentation ----

def test_readme_references_module_j_and_pause_resume():
    t = _read(os.path.join(REPO, "README.md"))
    assert "Module J" in t and "pause/resume" in t.lower()


def test_roadmap_expands_23_without_renumbering_24_27():
    t = _read(os.path.join(REPO, "ROADMAP.md"))
    assert "durable pause/resume" in t.lower() or "pause/resume" in t.lower()
    # Dispatch 24 must remain "Fast Battery Construction and First Execution"
    assert re.search(r"24\D+[Ff]ast [Bb]attery [Cc]onstruction", t)
    for d in range(22, 28):
        assert re.search(rf"\b{d}\b", t)


def test_architecture_doc_has_execution_and_slop_sections():
    t = _read(os.path.join(DOCS, "linewright-diagnostic-battery-architecture-v1.md"))
    assert "Dispatch 23 addendum" in t
    assert "Module J" in t and "Durable run ledger" in t


def test_new_docs_exist():
    for name in ("slop-detection-research-review-v1.md", "lwdb-execution-and-resume-v1.md",
                 "lwdb-slop-report-v1.md"):
        assert os.path.exists(os.path.join(DOCS, name)), name


def test_changelog_records_dispatch_23():
    t = _read(os.path.join(REPO, "CHANGELOG.md"))
    assert "Dispatch 23" in t and "slop" in t.lower()


def test_doc_links_resolve():
    for md in ("linewright-diagnostic-battery-architecture-v1.md",
               "lwdb-execution-and-resume-v1.md", "lwdb-slop-report-v1.md"):
        p = os.path.join(DOCS, md)
        base = os.path.dirname(p)
        for link in re.findall(r"\]\(([^)]+)\)", _read(p)):
            if link.startswith("http") or link.startswith("#"):
                continue
            target = os.path.normpath(os.path.join(base, link.split("#", 1)[0]))
            assert os.path.exists(target), f"broken link {link} in {md}"


# ---- schemas / manifest ----

def test_all_dispatch23_schemas_parse_and_are_declared():
    m = _load(MANIFEST)
    for name in ("execution-plan-schema", "slop-report-schema", "normalized-generation-result-schema",
                 "instrument-replay-result-schema", "slop-corpus-summary-schema"):
        assert name in m["required_schemas"]
    for f in glob.glob(os.path.join(BENCH, "schemas", "*.yaml")):
        _load(f)  # parses


def test_manifest_declares_module_j_and_zero_outputs():
    m = _load(MANIFEST)
    assert "J" in m["modules"]
    out = m["dispatch_23"]["dispatch_23_outputs"]
    assert out["benchmark_items_created"] == 0
    assert out["training_runs"] == 0
    assert out["ordinary_fast_full_benchmark_run"] is False
    assert out["numeric_capability_floors_set"] is False
    assert out["numeric_slop_thresholds_set"] is False
    assert out["dataset_a_changed"] is False


def test_slop_report_schema_supports_inconclusive_and_families():
    s = _load(os.path.join(BENCH, "schemas", "slop-report-schema.yaml"))
    assert "inconclusive" in s["enums"]["severity"]
    for fam in ("deterministic", "semantic", "lexical_style", "reviewer", "corpus_level", "summary"):
        assert fam in s


def test_slop_detector_manifest_thresholds_unvalidated():
    s = _load(os.path.join(BENCH, "schemas", "slop-detector-manifest-schema.yaml"))
    assert "unvalidated" in s["fields"]["threshold_status"]["enum"]


# ---- calibration lives under benchmarks/, never training ----

def test_calibration_items_not_in_training_dirs():
    # no calibration/benchmark jsonl under datasets/ or training/runs
    for root in (os.path.join(REPO, "training", "runs"), os.path.join(REPO, "datasets")):
        for p in glob.glob(os.path.join(root, "**", "*calibration*.jsonl"), recursive=True):
            raise AssertionError(f"calibration item in a training/data dir: {p}")


def test_calibration_records_are_benchmark_only():
    for name in ("grader-calibration-set-v1.jsonl", "slop-calibration-set-v1.jsonl"):
        p = os.path.join(BENCH, "calibration", name)
        for line in open(p, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                assert r.get("benchmark_only") is True
                assert r.get("excluded_from_training") is True


# ---- no training run / no ordinary benchmark / no committed run artifacts ----

def test_no_sqlite_run_artifacts_committed():
    # ledger dbs are tmp-only; none should be tracked under the repo tree
    for pat in ("**/*.db", "**/*.sqlite"):
        for p in glob.glob(os.path.join(BENCH, pat), recursive=True):
            raise AssertionError(f"unexpected committed ledger db: {p}")


def test_benchmark_lifecycle_dirs_have_no_ordinary_items():
    for d in ("development", "active-core", "rotating", "reserve", "burned"):
        entries = [e for e in os.listdir(os.path.join(BENCH, d)) if e != ".gitkeep"]
        assert entries == [], f"unexpected items in benchmarks/{d}: {entries}"


# ---- Dataset A + A.2 unchanged ----

def test_frozen_dataset_a_hashes_unchanged():
    cfg = _load(os.path.join(REPO, "training", "configs",
                             "dataset-a-lora-full-comparison-v1.yaml"))["dataset"]
    base = os.path.join(REPO, "datasets", "dataset-a", "compiled", "experimental-v1")
    for fname, pinned in (("train.jsonl", cfg["train_checksum"]),
                          ("evaluation.jsonl", cfg["evaluation_checksum"])):
        actual = hashlib.sha256(open(os.path.join(base, fname), "rb").read()).hexdigest()
        assert actual == pinned, f"Dataset A {fname} changed!"


def test_dataset_a2_pilot_unchanged():
    man = json.load(open(os.path.join(REPO, "datasets", "dataset-a.2", "pilot", "manifest.json"),
                         encoding="utf-8"))
    pilot = os.path.join(REPO, "datasets", "dataset-a.2", "pilot")

    def digest(rows):
        return hashlib.sha256("".join(json.dumps(r, ensure_ascii=False) for r in rows)
                              .encode("utf-8")).hexdigest()
    for fname, key in (("train.jsonl", "train_sha256"), ("evaluation.jsonl", "evaluation_sha256")):
        rows = [json.loads(l) for l in open(os.path.join(pilot, fname), encoding="utf-8") if l.strip()]
        assert digest(rows) == man[key], f"Dataset A.2 {fname} changed!"
