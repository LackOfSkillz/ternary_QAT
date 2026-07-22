"""Dispatch 21 (Phase C/D/F) — Dataset A.2 schema, pilot validation, split isolation."""
import importlib.util
import json
import os

import pytest

_HERE = os.path.dirname(__file__)
_A2 = os.path.join(_HERE, "..", "datasets", "dataset-a.2")
_VALIDATOR = os.path.join(_A2, "scripts", "validate_a2.py")
_PILOT = os.path.join(_A2, "pilot")

pytest.importorskip("yaml")

_spec = importlib.util.spec_from_file_location("validate_a2", _VALIDATOR)
val = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(val)


def test_pilot_validates_end_to_end():
    problems, ntr, nev = val.validate_pilot(_PILOT)
    assert problems == [], f"pilot has problems: {problems}"
    assert 20 <= ntr <= 30, f"train size {ntr} outside 20-30"
    assert 8 <= nev <= 12, f"eval size {nev} outside 8-12"


def test_pilot_split_is_clean():
    train = val.load_jsonl(os.path.join(_PILOT, "train.jsonl"))
    ev = val.load_jsonl(os.path.join(_PILOT, "evaluation.jsonl"))
    assert val.validate_split_grouping(train, ev) == []


def test_shared_story_world_split_violation_detected():
    train = [{"split_restrictions": {"group_key": "g1"}, "source_family": "f1",
              "story_world": "SHARED", "input": {"source": "aaa"}, "preferred_response": "p"}]
    ev = [{"split_restrictions": {"group_key": "g2"}, "source_family": "f2",
           "story_world": "SHARED", "input": {"source": "bbb"}, "preferred_response": "q"}]
    problems = val.validate_split_grouping(train, ev)
    assert any("story_world" in p for p in problems)


def test_shared_source_family_split_violation_detected():
    train = [{"split_restrictions": {"group_key": "g1"}, "source_family": "SHARED",
              "story_world": "w1", "input": {"source": "aaa"}, "preferred_response": "p"}]
    ev = [{"split_restrictions": {"group_key": "g2"}, "source_family": "SHARED",
           "story_world": "w2", "input": {"source": "bbb"}, "preferred_response": "q"}]
    problems = val.validate_split_grouping(train, ev)
    assert any("source_family" in p for p in problems)


def test_record_shape_rejects_missing_field():
    bad = {"record_id": "dsa2-bad-1", "dataset_version": "dataset-a.2-pilot-v1",
           "task_family": "focused_revision"}  # missing most required fields
    problems = val.validate_record_shape(bad)
    assert any("missing required field" in p for p in problems)


def test_record_shape_rejects_bad_id_prefix():
    rec = val.load_jsonl(os.path.join(_PILOT, "train.jsonl"))[0]
    rec = dict(rec)
    rec["record_id"] = "wrong-prefix-1"
    problems = val.validate_record_shape(rec)
    assert any("record_id must start with 'dsa2-'" in p for p in problems)


def test_output_contract_registry_resolves_all_pilot_schema_ids():
    from linewright.evaluation import contracts as contract_mod
    reg = contract_mod.load_registry()
    for line in open(os.path.join(_PILOT, "train.jsonl"), encoding="utf-8"):
        rec = json.loads(line)
        merged = contract_mod.resolve(rec["output_contract"], reg)
        assert merged["schema_id"] in reg
