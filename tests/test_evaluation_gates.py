"""Dispatch 21 (Phase E/G/H) — mechanical gates, reviewer packets, advancement rules.

Covers the dispatch test list: exact / whitespace no-change preservation, missing /
forbidden / alternate keys (top-level and nested), prose-outside-structure, duplicate and
normalized-duplicate sentences, repeated n-grams, incomplete JSON/YAML, exact and
near-exact target overlap, empty / runaway / ratio scope, packet anonymization, candidate
order randomization, hidden identity, and fatal-flaw advancement blocking.
"""
from linewright.evaluation.preservation import validate_preservation
from linewright.evaluation.schema_validation import validate_structured
from linewright.evaluation.repetition import analyze_repetition
from linewright.evaluation.overlap import analyze_overlap
from linewright.evaluation.scope import validate_scope
from linewright.evaluation.completion import validate_completion
from linewright.evaluation.reviewer_packet import build_packet, anonymization_ok
from linewright.evaluation.advancement import check_advancement, check_retraining_readiness
import json


# ---------------- preservation ----------------

def test_exact_no_change_preservation_passes():
    src = "The lamp guttered and did not go out."
    out = json.dumps({"changed": False, "reason": "clean", "text": src})
    r = validate_preservation(out, src, {"expects_no_change": True})
    assert r.valid is True and not r.failure_labels


def test_whitespace_difference_fails_exact_preservation():
    src = "one  two   three"
    out = json.dumps({"changed": False, "reason": "clean", "text": "one two three"})
    r = validate_preservation(out, src, {"expects_no_change": True,
                                         "exact_source_preservation_required": True})
    assert r.valid is False and "exact_preservation_failure" in r.failure_labels


def test_bare_prose_no_change_missing_wrapper():
    src = "A clean sentence that needs no fix."
    r = validate_preservation(src, src, {"expects_no_change": True})
    assert r.valid is False and "no_change_wrapper_missing" in r.failure_labels


# ---------------- schema ----------------

def test_missing_required_key():
    r = validate_structured(json.dumps({"facts": []}),
                            {"type": "json", "required_keys": ["facts", "insufficient_evidence"]})
    assert r.valid is False and "missing_required_key" in r.failure_labels


def test_forbidden_extra_key():
    r = validate_structured(json.dumps({"changed": False, "reason": "x", "text": "y", "explanation": "no"}),
                            {"type": "json", "required_keys": ["changed", "reason", "text"],
                             "forbidden_keys": ["explanation"], "strict_keys": False})
    assert r.valid is False and "forbidden_extra_key" in r.failure_labels


def test_alternate_top_level_keys():
    r = validate_structured(json.dumps({"facts": [], "note": "x"}),
                            {"type": "json", "required_keys": ["facts", "insufficient_evidence"],
                             "strict_keys": True})
    assert "alternate_key_names" in r.failure_labels or "missing_required_key" in r.failure_labels


def test_alternate_nested_item_keys():
    # the real QAT-20 canon drift: speaker/claim instead of entity/fact inside facts[]
    out = json.dumps({"facts": [{"speaker": "a", "claim": "b"}], "insufficient_evidence": []})
    r = validate_structured(out, {"type": "json",
                                  "required_keys": ["facts", "insufficient_evidence"],
                                  "strict_keys": True,
                                  "item_required_keys": {"facts": ["entity", "fact", "certainty", "evidence"]}})
    assert r.valid is False and "alternate_key_names" in r.failure_labels


def test_prose_where_structure_required():
    r = validate_structured("just some prose", {"type": "json", "required_keys": ["a"]})
    assert r.valid is False and "invalid_json" in r.failure_labels


# ---------------- repetition ----------------

def test_duplicate_sentences():
    out = "The cat sat on the mat. The cat sat on the mat. The cat sat on the mat."
    r = analyze_repetition(out)
    assert r.valid is False and "duplicate_sentence" in r.failure_labels


def test_normalized_duplicate_sentences():
    out = "The cat sat over there. the cat sat over there! The cat sat over there"
    r = analyze_repetition(out)
    assert r.valid is False and ("paraphrased_sentence_repeat" in r.failure_labels
                                 or "duplicate_sentence" in r.failure_labels)


def test_repeated_ngrams_short_phrase_loop():
    out = "the door creaks " * 10
    r = analyze_repetition(out)
    assert r.valid is False and "repeated_ngram" in r.failure_labels


def test_clean_structured_values_not_flagged():
    # repeated short field values ("established") must NOT count as repetition
    out = json.dumps({"facts": [{"certainty": "established"}, {"certainty": "established"},
                                {"certainty": "character_belief"}, {"certainty": "established"}]})
    r = analyze_repetition(out)
    assert r.valid is True


# ---------------- completion ----------------

def test_incomplete_json():
    r = validate_completion('{"a": 1, "b":', {"type": "json"})
    assert r.valid is False and "truncated_structure" in r.failure_labels


def test_empty_output():
    r = validate_completion("   ", {"type": "prose"})
    assert r.valid is False and "empty_output" in r.failure_labels


# ---------------- overlap / memorization ----------------

def test_exact_gold_reproduction():
    g = "She came down to the river and the water took her name."
    r = analyze_overlap(g, g, [])
    assert r.valid is False and "exact_gold_reproduction" in r.failure_labels


def test_near_exact_gold_reproduction():
    g = "The generator ran all night in the yard and by dawn the fuel was entirely gone here."
    out = g[:-2] + "!"  # one-char change, >0.97 ratio
    r = analyze_overlap(out, g, [])
    assert "near_exact_gold_reproduction" in r.failure_labels


def test_long_training_target_overlap():
    target = "x " * 200  # a long training target
    out = "prefix " + target
    r = analyze_overlap(out, "different gold", [target])
    assert r.valid is False and "long_train_target_overlap" in r.failure_labels


# ---------------- scope ----------------

def test_runaway_output_length():
    r = validate_scope("z" * 5000, "short source", {"type": "prose", "max_output_chars": 1000})
    assert "runaway_length" in r.failure_labels


def test_output_source_ratio_limit():
    src = "a short source passage here"
    out = src + " " + ("padding words " * 40)
    r = validate_scope(out, src, {"type": "prose", "max_output_ratio": 1.5})
    assert "excessive_expansion" in r.failure_labels


def test_omitted_required_change():
    src = "Their eyes meet across the yard and lock again."
    r = validate_scope(src, src, {"type": "prose", "expects_change": True})
    assert "omitted_required_change" in r.failure_labels


# ---------------- reviewer packet ----------------

def _record():
    return {"record_id": "dsa2-x-1", "task_family": "focused_revision",
            "input": {"task_instruction": "fix it", "source": "the source", "canon": [],
                      "hard_constraints": []},
            "output_contract": {"type": "prose", "schema_id": "prose-v1"}}


def test_packet_anonymization_no_identity_leak():
    cands = [{"identity": "base", "output": "alpha output"},
             {"identity": "qat-step-20", "output": "beta output"}]
    packet, key = build_packet(_record(), cands)
    assert anonymization_ok(packet) == []
    # packet body carries no 'identity'; the key does
    assert all("identity" not in c for c in packet["candidates"])
    assert "base" in json.dumps(key)


def test_candidate_order_is_content_derived_not_input_order():
    a = {"identity": "base", "output": "zzz first by input"}
    b = {"identity": "lora", "output": "aaa second by input"}
    p1, _ = build_packet(_record(), [a, b], seed="s")
    p2, _ = build_packet(_record(), [b, a], seed="s")
    # same content + seed -> identical anonymized order regardless of input order
    assert [c["output"] for c in p1["candidates"]] == [c["output"] for c in p2["candidates"]]


def test_packet_hides_model_identity_labels():
    cands = [{"identity": "ternary-qat", "output": "one"}, {"identity": "base", "output": "two"}]
    packet, _ = build_packet(_record(), cands)
    labels = [c["label"] for c in packet["candidates"]]
    assert labels == ["Candidate A", "Candidate B"]


# ---------------- advancement ----------------

def _good_evidence():
    return {"mechanical_gates_pass": True, "schema_regressions": 0, "no_change_regressions": 0,
            "memorization_flags": 0, "material_regressions": 0,
            "reviewers": {n: {"prefers_over_base": True, "fatal_flaw": False}
                          for n in ("aedan", "claude", "chatgpt")}}


def test_advancement_passes_when_all_hold():
    assert check_advancement(_good_evidence())["advance"] is True


def test_fatal_flaw_blocks_even_with_two_approvals():
    ev = _good_evidence()
    ev["reviewers"]["chatgpt"]["fatal_flaw"] = True
    res = check_advancement(ev)
    assert res["advance"] is False
    assert any("fatal_reviewer_flags" in b for b in res["blockers"])
    assert res["needs_investigation"] is True


def test_advancement_blocks_on_schema_regression():
    ev = _good_evidence()
    ev["schema_regressions"] = 1
    assert check_advancement(ev)["advance"] is False


def test_readiness_gate_requires_all_flags():
    partial = {f: True for f in ["dataset_schema_valid", "all_records_static_valid"]}
    res = check_retraining_readiness(partial)
    assert res["ready"] is False and res["blockers"]
