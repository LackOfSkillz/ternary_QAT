"""Prove the Dataset A validator accepts a well-formed record and rejects
malformed ones. Builds a throwaway dataset root using the REAL schema/enums."""
import importlib.util
import os
import shutil

import pytest

_HERE = os.path.dirname(__file__)
_DA = os.path.join(_HERE, "..", "datasets", "dataset-a")
_VALIDATOR = os.path.join(_DA, "scripts", "validate_dataset_a.py")

yaml = pytest.importorskip("yaml")

_spec = importlib.util.spec_from_file_location("validate_dataset_a", _VALIDATOR)
val = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(val)


GOOD = """---
id: dsa-canon-999
dataset: dataset-a
split: unassigned
review_status: draft
task_type: canon_extraction
operating_mode: source_bound
difficulty: easy
template_family: canon-fixture
semantic_cluster: fixture-cluster
provenance: model-authored fixture by claude-opus-4-8
origin: model_authored
source_type: synthetic_internal
license_status: unverified
teacher_model: claude-opus-4-8
teacher_terms_status: pending_review
excluded_from_training: true
expected_properties:
  - valid JSON
---

## Instruction
Extract canon facts as JSON.

## Context
A short synthetic passage that is unique to this fixture record.

## Gold Response
[{"entity": "X", "fact": "unique fixture fact"}]

## Evaluation
Output parses as JSON.

## Reviewer Notes
Fixture.
"""


def _build_root(tmp_path, record_text):
    root = tmp_path / "dataset-a"
    (root / "schema").mkdir(parents=True)
    (root / "drafts" / "canon").mkdir(parents=True)
    for fn in ("record-schema.yaml", "enums.yaml"):
        shutil.copy(os.path.join(_DA, "schema", fn), root / "schema" / fn)
    (root / "drafts" / "canon" / "rec.md").write_text(record_text, encoding="utf-8")
    return str(root)


def test_good_record_passes(tmp_path):
    problems, stats = val.validate(_build_root(tmp_path, GOOD))
    assert problems == [], problems
    assert stats["records"] == 1


def test_missing_required_field_rejected(tmp_path):
    bad = GOOD.replace("license_status: unverified\n", "")
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("license_status" in p for p in problems)


def test_bad_enum_value_rejected(tmp_path):
    bad = GOOD.replace("review_status: draft", "review_status: totally_made_up")
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("review_status" in p and "enum" in p for p in problems)


def test_missing_required_section_rejected(tmp_path):
    bad = GOOD.replace("## Gold Response\n[{\"entity\": \"X\", \"fact\": \"unique fixture fact\"}]\n", "")
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("Gold Response" in p for p in problems)


def test_missing_front_matter_rejected(tmp_path):
    problems, _ = val.validate(_build_root(tmp_path, "no front matter here\n"))
    assert any("front matter" in p for p in problems)


def test_approved_status_in_drafts_rejected(tmp_path):
    bad = GOOD.replace("review_status: draft", "review_status: frozen")
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("drafts/" in p for p in problems)


def test_unknown_field_rejected(tmp_path):
    bad = GOOD.replace("origin: model_authored\n",
                       "origin: model_authored\nmystery_field: nope\n")
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("unknown front-matter field 'mystery_field'" in p for p in problems)


def test_misspelled_known_field_rejected(tmp_path):
    # a typo'd key is an unknown key AND drops the required real field
    bad = GOOD.replace("difficulty: easy", "dificulty: easy")
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("dificulty" in p for p in problems)          # unknown key
    assert any("missing required field 'difficulty'" in p for p in problems)


def test_missing_teacher_model_rejected(tmp_path):
    bad = GOOD.replace("teacher_model: claude-opus-4-8\n", "")
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("teacher_model" in p for p in problems)


def test_bad_origin_enum_rejected(tmp_path):
    bad = GOOD.replace("origin: model_authored", "origin: ghostwritten")
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("origin" in p and "enum" in p for p in problems)


def _pair_record(rid, partner, cluster):
    return (GOOD.replace("id: dsa-canon-999", f"id: {rid}")
                .replace("task_type: canon_extraction", "task_type: focused_revision")
                .replace("semantic_cluster: fixture-cluster", f"semantic_cluster: {cluster}")
                .replace("template_family: canon-fixture", f"template_family: fam-{rid}")
                .replace("origin: model_authored\n",
                         f"origin: model_authored\nmatched_pair_with: {partner}\n"))


def _build_root_multi(tmp_path, records):
    root = tmp_path / "dataset-a"
    (root / "schema").mkdir(parents=True)
    (root / "drafts" / "revision").mkdir(parents=True)
    for fn in ("record-schema.yaml", "enums.yaml"):
        shutil.copy(os.path.join(_DA, "schema", fn), root / "schema" / fn)
    for i, txt in enumerate(records):
        (root / "drafts" / "revision" / f"r{i}.md").write_text(txt, encoding="utf-8")
    return str(root)


def test_matched_pair_nonexistent_rejected(tmp_path):
    r = _pair_record("dsa-rev-a", "dsa-rev-ghost", "c-a")
    problems, _ = val.validate(_build_root_multi(tmp_path, [r]))
    assert any("does not exist" in p for p in problems)


def test_matched_pair_nonreciprocal_rejected(tmp_path):
    a = _pair_record("dsa-rev-a", "dsa-rev-b", "c-a")
    b = _pair_record("dsa-rev-b", "dsa-rev-c", "c-b")   # points elsewhere
    problems, _ = val.validate(_build_root_multi(tmp_path, [a, b]))
    assert any("not reciprocal" in p for p in problems)


def test_matched_pair_reciprocal_ok(tmp_path):
    a = _pair_record("dsa-rev-a", "dsa-rev-b", "c-a")
    b = _pair_record("dsa-rev-b", "dsa-rev-a", "c-b")
    problems, _ = val.validate(_build_root_multi(tmp_path, [a, b]))
    assert not any("reciprocal" in p or "does not exist" in p for p in problems), problems
