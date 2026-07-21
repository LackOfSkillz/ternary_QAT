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


# ---- constraint_check causal-set grading ----

CONSTRAINT_GOOD = """---
id: dsa-constraint-999
dataset: dataset-a
split: unassigned
review_status: draft
task_type: constraint_check
operating_mode: constraint_bound
difficulty: medium
template_family: constraint-fixture
semantic_cluster: constraint-fixture-cluster
provenance: model-authored fixture by claude-opus-4-8
origin: model_authored
source_type: synthetic_internal
license_status: unverified
teacher_model: claude-opus-4-8
teacher_terms_status: pending_review
excluded_from_training: true
causal_constraint_ids:
  - C1
  - C2
expected_properties:
  - valid JSON
---

## Instruction
Check continuity.

## Context
Declared canon constraints:
- C1 (established fact): first fact.
- C2 (established fact): second fact.
- C3 (established fact): third fact.

Draft passage: it breaks C1 and C2 at once.

## Gold Response
```json
{"violation": true, "type": "factual_contradiction", "constraint_ids": ["C1", "C2"], "explanation": "x", "evidence": "y"}
```

## Evaluation
ok.

## Reviewer Notes
Fixture.
"""


def test_constraint_causal_set_ok(tmp_path):
    problems, _ = val.validate(_build_root(tmp_path, CONSTRAINT_GOOD))
    assert problems == [], problems


def test_constraint_partial_set_rejected(tmp_path):
    bad = CONSTRAINT_GOOD.replace('"constraint_ids": ["C1", "C2"]',
                                  '"constraint_ids": ["C1"]')
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("!= causal set" in p for p in problems), problems


def test_constraint_extra_id_rejected(tmp_path):
    bad = CONSTRAINT_GOOD.replace('"constraint_ids": ["C1", "C2"]',
                                  '"constraint_ids": ["C1", "C2", "C3"]')
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("extra ['C3']" in p for p in problems), problems


def test_constraint_undeclared_id_rejected(tmp_path):
    bad = CONSTRAINT_GOOD.replace('"constraint_ids": ["C1", "C2"]',
                                  '"constraint_ids": ["C1", "Z9"]')
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("undeclared constraint 'Z9'" in p for p in problems), problems


def test_constraint_duplicate_id_rejected(tmp_path):
    bad = CONSTRAINT_GOOD.replace('"constraint_ids": ["C1", "C2"]',
                                  '"constraint_ids": ["C1", "C1"]')
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("duplicate" in p for p in problems), problems


def test_constraint_nonviolation_nonempty_set_rejected(tmp_path):
    bad = CONSTRAINT_GOOD.replace('"violation": true', '"violation": false')
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("non-violation must have empty" in p for p in problems), problems


# ---- invention_budget + no-change protocol (focused_revision) ----

REV_GOOD = """---
id: dsa-revision-999
dataset: dataset-a
split: unassigned
review_status: draft
task_type: focused_revision
operating_mode: source_bound
difficulty: easy
template_family: rev-fixture
semantic_cluster: rev-fixture-cluster
style_profile: none
craft_targets:
  - significant_detail
protected_craft:
  - flat_affect
authorized_changes:
  - change one sentence
unauthorized_changes:
  - rewriting everything
anti_slop_targets:
  - generic_atmosphere
anti_slop_risks:
  - unauthorized_rewrite
failure_modes:
  - generic_atmosphere
invention_budget:
  level: bounded
  allowed:
    - one concrete detail
  prohibited:
    - new backstory
provenance: model-authored fixture by claude-opus-4-8
origin: model_authored
source_type: synthetic_internal
license_status: unverified
teacher_model: claude-opus-4-8
teacher_terms_status: pending_review
excluded_from_training: true
expected_properties:
  - one sentence changed
---

## Instruction
Revise one sentence.

## Context
The source passage that is unique to this revision fixture record.

## Gold Response
The revised passage that is unique to this revision fixture record.

## Protected Elements
- something

## Rejected Response
A bad rewrite unique to this fixture.

## Rejection Reasons
- unauthorized_rewrite: bad.

## Evaluation
Diff it.

## Reviewer Notes
Fixture.
"""

_IB_BLOCK = ("invention_budget:\n  level: bounded\n  allowed:\n"
             "    - one concrete detail\n  prohibited:\n    - new backstory\n")


def test_invention_budget_valid_ok(tmp_path):
    problems, _ = val.validate(_build_root(tmp_path, REV_GOOD))
    assert problems == [], problems


def test_invention_budget_missing_rejected(tmp_path):
    bad = REV_GOOD.replace(_IB_BLOCK, "")
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("invention_budget" in p for p in problems), problems


def test_invention_budget_none_with_allowance_rejected(tmp_path):
    bad = REV_GOOD.replace("level: bounded", "level: none")
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("must not declare affirmative allowances" in p for p in problems), problems


def test_invention_budget_bounded_without_allowance_rejected(tmp_path):
    bad = REV_GOOD.replace("  allowed:\n    - one concrete detail\n", "  allowed: []\n")
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("must list at least one allowance" in p for p in problems), problems


def test_invention_budget_open_without_prohibition_rejected(tmp_path):
    bad = (REV_GOOD.replace("level: bounded", "level: open")
                   .replace("  prohibited:\n    - new backstory\n", "  prohibited: []\n"))
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("must still state prohibitions" in p for p in problems), problems


def test_no_change_text_match_ok(tmp_path):
    gold = ("## Gold Response\n```json\n"
            '{"changed": false, "reason": "No genuine defect found.", '
            '"text": "The source passage that is unique to this revision fixture record."}\n'
            "```\n")
    ok = REV_GOOD.replace(
        "## Gold Response\nThe revised passage that is unique to this revision fixture record.\n",
        gold)
    problems, _ = val.validate(_build_root(tmp_path, ok))
    assert not any("no-change" in p for p in problems), problems


def test_no_change_text_mismatch_rejected(tmp_path):
    gold = ("## Gold Response\n```json\n"
            '{"changed": false, "reason": "No genuine defect found.", '
            '"text": "completely different text that does not match the source"}\n'
            "```\n")
    bad = REV_GOOD.replace(
        "## Gold Response\nThe revised passage that is unique to this revision fixture record.\n",
        gold)
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("no-change gold" in p for p in problems), problems


# ---- public-domain provenance ----

def test_public_domain_requires_block_rejected(tmp_path):
    bad = GOOD.replace("source_type: synthetic_internal", "source_type: public_domain")
    problems, _ = val.validate(_build_root(tmp_path, bad))
    assert any("public_domain_source" in p for p in problems), problems
