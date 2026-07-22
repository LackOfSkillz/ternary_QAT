"""Dispatch 22 — validate the LineWright Diagnostic Battery ARCHITECTURE.

These tests assert the architecture is well-formed and self-consistent. They do NOT run
models, generate prompts, or set thresholds (none of which this dispatch produces).
"""
import glob
import hashlib
import os
import re

import pytest

yaml = pytest.importorskip("yaml")

HERE = os.path.dirname(__file__)
REPO = os.path.abspath(os.path.join(HERE, ".."))
BENCH = os.path.join(REPO, "benchmarks")
MANIFEST = os.path.join(BENCH, "manifests", "diagnostic-battery-architecture-v1.yaml")
SPEC = os.path.join(REPO, "training", "docs", "linewright-diagnostic-battery-architecture-v1.md")
SCHEMA_DIR = os.path.join(BENCH, "schemas")


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def manifest():
    return _load(MANIFEST)


# ---------------- manifest structure ----------------

def test_manifest_parses(manifest):
    assert manifest["name"].startswith("LineWright Model Capability")
    assert manifest["status"] == "architecture_only"
    assert manifest["dispatch"] == 22


def test_all_capability_modules_exist(manifest):
    assert set(manifest["modules"]) == set("ABCDEFGHI")


def test_all_six_layers_exist(manifest):
    layers = manifest["layers"]
    for n in range(1, 7):
        assert any(k.startswith(f"layer_{n}_") for k in layers), f"missing layer {n}"


def test_fast_and_full_profiles_exist(manifest):
    prof = manifest["battery_profiles"]
    assert "fast" in prof and "full" in prof
    assert prof["shared"]["differ_only_in"]  # fast/full share one architecture


def test_confidence_levels_exist(manifest):
    assert manifest["confidence_levels"] == ["high", "moderate", "low", "inconclusive"]


def test_evidence_types_exist(manifest):
    for e in ("mechanical", "matched_pair_mechanical", "reviewer_consensus",
              "reviewer_split", "single_reviewer", "mixed_mechanical_and_reviewer"):
        assert e in manifest["evidence_types"]


def test_lifecycle_states_and_burned_exist(manifest):
    states = manifest["lifecycle_states"]
    for s in ("development", "candidate", "active", "used_for_measurement",
              "used_for_diagnosis", "burned", "retired"):
        assert s in states
    assert "burned" in states


def test_bottleneck_cause_space_complete(manifest):
    for c in ("dataset_coverage", "dataset_balance", "training_duration", "learning_rate",
              "training_method", "quantization", "context_compilation", "decoding",
              "base_model_capacity"):
        assert c in manifest["bottleneck_cause_space"]


# ---------------- schemas ----------------

def test_all_required_schemas_exist(manifest):
    for name in manifest["required_schemas"]:
        p = os.path.join(SCHEMA_DIR, f"{name}.yaml")
        assert os.path.exists(p), f"missing schema {name}"
        # filename/manifest use the '-schema' suffix; the internal `schema:` key omits it
        assert _load(p)["schema"] + "-schema" == name


def test_benchmark_only_exclusion_is_required():
    item = _load(os.path.join(SCHEMA_DIR, "benchmark-item-schema.yaml"))
    bo = item["fields"]["benchmark_only"]
    assert bo["required"] is True and bo["type"] == "const" and bo["const"] is True
    prov = _load(os.path.join(SCHEMA_DIR, "benchmark-provenance-schema.yaml"))
    assert prov["fields"]["benchmark_only"]["const"] is True


def test_controlled_pair_fields_in_schema():
    item = _load(os.path.join(SCHEMA_DIR, "benchmark-item-schema.yaml"))["fields"]
    for f in ("pair_id", "family_id", "controlled_variable", "invariant_features",
              "expected_diagnostic_if_split", "paired_item_ids"):
        assert f in item
    fam = _load(os.path.join(SCHEMA_DIR, "pair-family-schema.yaml"))
    for f in ("controlled_variable", "invariant_features", "expected_diagnostic_if_split"):
        assert f in fam["fields"]


def test_model_role_manifest_supports_required_roles():
    roles = _load(os.path.join(SCHEMA_DIR, "model-role-manifest-schema.yaml"))["roles"]
    for r in ("target_base", "previous_best", "new_candidate",
              "strong_reference", "weak_reference"):
        assert r in roles


def test_mechanical_result_has_negative_space_dimension():
    mr = _load(os.path.join(SCHEMA_DIR, "mechanical-result-schema.yaml"))
    assert "negative_space_valid" in mr["gate_dimensions"]


# ---------------- no fabricated thresholds ----------------

def test_no_numeric_capability_floor_hardcoded(manifest):
    pol = manifest["capability_floor_policy"]
    assert pol["numeric_values"] == "unset"
    assert pol["fabricated_thresholds_present"] is False
    # no schema or the manifest may carry a percent sign or a numeric score/pass threshold
    bad = re.compile(r"(capability_floor|score_threshold|min_score|pass_threshold|pass_rate)\s*:\s*[0-9]")
    for p in [MANIFEST] + glob.glob(os.path.join(SCHEMA_DIR, "*.yaml")):
        text = open(p, encoding="utf-8").read()
        assert "%" not in text, f"unexpected percent threshold in {os.path.basename(p)}"
        assert not bad.search(text), f"hard-coded threshold in {os.path.basename(p)}"


# ---------------- documentation ----------------

def _relative_links(md_path):
    text = open(md_path, encoding="utf-8").read()
    links = re.findall(r"\]\(([^)]+)\)", text)
    out = []
    for l in links:
        if l.startswith("http") or l.startswith("#"):
            continue
        out.append(l.split("#", 1)[0])
    return out


def test_documentation_links_resolve():
    for md in (SPEC, os.path.join(REPO, "README.md"), os.path.join(BENCH, "README.md"),
               os.path.join(REPO, "docs", "linewright-diagnostic-battery.md")):
        base = os.path.dirname(md)
        for link in _relative_links(md):
            target = os.path.normpath(os.path.join(base, link))
            assert os.path.exists(target), f"broken link {link} in {os.path.relpath(md, REPO)}"


def test_spec_has_all_nineteen_sections():
    text = open(SPEC, encoding="utf-8").read()
    nums = set(re.findall(r"^## (\d+)\.", text, re.M))
    assert {str(i) for i in range(1, 20)}.issubset(nums)


def test_roadmap_contains_dispatches_22_to_27():
    text = open(os.path.join(REPO, "ROADMAP.md"), encoding="utf-8").read()
    for d in range(22, 28):
        assert re.search(rf"\b{d}\b", text), f"roadmap missing dispatch {d}"
    assert "current" in text.lower()


def test_readme_references_battery():
    text = open(os.path.join(REPO, "README.md"), encoding="utf-8").read()
    assert "Diagnostic Battery" in text
    assert "linewright-diagnostic-battery-architecture-v1.md" in text


def test_changelog_records_architecture_dispatch():
    text = open(os.path.join(REPO, "CHANGELOG.md"), encoding="utf-8").read()
    assert "Dispatch 22" in text and "Diagnostic Battery" in text


# ---------------- no training / no prompts created ----------------

def test_no_benchmark_prompts_or_run_artifacts_created(manifest):
    # lifecycle item dirs are skeletons: only .gitkeep, no items/prompts/outputs
    for d in ("development", "active-core", "rotating", "reserve", "calibration", "burned"):
        entries = [e for e in os.listdir(os.path.join(BENCH, d)) if e != ".gitkeep"]
        assert entries == [], f"unexpected files in benchmarks/{d}: {entries}"
    out = manifest["dispatch_22_outputs"]
    assert out["benchmark_items_created"] == 0
    assert out["model_generations"] == 0
    assert out["training_runs"] == 0
    assert out["dataset_a_changed"] is False


# ---------------- frozen Dataset A unchanged ----------------

def test_frozen_dataset_a_hashes_unchanged():
    cfg = _load(os.path.join(REPO, "training", "configs",
                             "dataset-a-lora-full-comparison-v1.yaml"))["dataset"]
    base = os.path.join(REPO, "datasets", "dataset-a", "compiled", "experimental-v1")
    for fname, pinned in (("train.jsonl", cfg["train_checksum"]),
                          ("evaluation.jsonl", cfg["evaluation_checksum"])):
        actual = hashlib.sha256(open(os.path.join(base, fname), "rb").read()).hexdigest()
        assert actual == pinned, f"Dataset A {fname} changed!"
