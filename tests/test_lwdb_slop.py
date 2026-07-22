"""Dispatch 23 — slop detector (Module J) invariants.

Deterministic detection works; deliberate repetition / concision / lyrical prose are NOT
auto-flagged; evidence spans are retained; no single phrase hit auto-fails; no unvalidated
threshold is presented as empirical truth; the report keeps every evidence family separate.
"""
import json

import pytest

from linewright.evaluation.slop.deterministic import deterministic_slop
from linewright.evaluation.slop.rhythm import sentence_rhythm
from linewright.evaluation.slop.lexical import lexical_diversity
from linewright.evaluation.slop.repetition import repetition_measures
from linewright.evaluation.slop.report import build_slop_report
from linewright.evaluation.slop.corpus import corpus_slop_summary

DEG = "The door creaks. " * 30
CLEAN_LONG = ("He checked the nets and the lines and did not like the sky. By noon the wind "
              "had come around hard from the north, and the little boats were already running "
              "for the harbor mouth, low and fast against a bruise-colored horizon that "
              "promised a long and sleepless night for everyone who worked the water.")


def _report(text, **kw):
    return build_slop_report(text, output_id="o", detector_manifest_id="m", **kw)


def test_exact_and_ngram_repetition_detected():
    m = repetition_measures(DEG)
    assert m["repeated_ngram_rates"][5] >= 4
    r = _report(DEG)
    assert r["summary"]["severity"] in ("high", "severe")
    assert "repeated_ngram" in r["summary"]["dominant_failure_types"]


def test_repeated_openings_detected():
    text = "\n\n".join(["The wind rose over the hill and then it fell again slowly."] * 3
                       + ["Something entirely different happened next in the valley below."])
    m = repetition_measures(text)
    assert m["repeated_paragraph_openings"] >= 1


def test_rhythm_and_lexical_are_deterministic():
    assert sentence_rhythm(CLEAN_LONG) == sentence_rhythm(CLEAN_LONG)
    assert lexical_diversity(CLEAN_LONG) == lexical_diversity(CLEAN_LONG)
    assert deterministic_slop(CLEAN_LONG) == deterministic_slop(CLEAN_LONG)


def test_short_output_limitation_reported():
    d = deterministic_slop("A short line.")
    assert d["short_output_metric_limitations"] is True
    r = _report("A short line.")
    assert r["summary"]["severity"] == "inconclusive"


def test_source_overlap_separate_from_slop():
    src = "The generator ran all night in the yard."
    d = deterministic_slop(src, source=src)
    assert d["source_overlap"] == 1.0
    # source overlap is a fidelity signal reported separately; it is not a slop failure type
    r = _report(src, source=src)
    assert "source_overlap" not in r["summary"]["dominant_failure_types"]


def test_deliberate_repetition_not_flagged_severe():
    anaphora = ("I remember the rain on the roof. I remember the smell of wet ash. I "
                "remember the way she counted the jars and never wrote the number down.")
    assert _report(anaphora)["summary"]["severity"] not in ("high", "severe")


def test_concise_and_lyrical_not_autofailed():
    for text in (CLEAN_LONG,
                 "Down she came to the river the way winter comes to a year, slowly and then "
                 "all at once, and the water took the syllables of her name toward a sea that "
                 "keeps no accounts and in the end forgets nothing at all."):
        assert _report(text)["summary"]["severity"] not in ("high", "severe")


def test_high_diversity_incoherence_not_falsely_declared_clean():
    # deterministic layer cannot judge coherence; the report must NOT claim high-confidence
    # clean — semantic stays unvalidated and limitations say so.
    r = _report(CLEAN_LONG)
    assert r["summary"]["semantic_confidence"] == "unvalidated"
    assert any("interface-only" in l or "unvalidated" in l for l in r["summary"]["limitations"])


def test_evidence_spans_retained():
    r = _report(DEG)
    assert r["deterministic"]["evidence_spans"], "degenerate output must retain evidence spans"


def test_no_single_phrase_hit_auto_fails():
    # a lone stock phrase in otherwise clean prose is not a failure
    r = _report("It was a dark and stormy night, and the old sailor mended his nets in silence.")
    assert r["lexical_style"]["stock_phrase_hits"] == []
    assert r["summary"]["severity"] not in ("high", "severe")


def test_no_unvalidated_threshold_presented_as_truth():
    r = _report(CLEAN_LONG)
    assert any("unvalidated" in l for l in r["summary"]["limitations"])


def test_report_has_all_evidence_families_and_separate_confidences():
    r = _report(DEG)
    for fam in ("deterministic", "semantic", "lexical_style", "reviewer", "corpus_level", "summary"):
        assert fam in r
    s = r["summary"]
    for c in ("mechanical_confidence", "semantic_confidence", "reviewer_confidence", "overall_confidence"):
        assert c in s
    for rec in ("recommended_dataset_actions", "recommended_training_actions",
                "recommended_context_actions", "recommended_decoding_actions"):
        assert rec in s


def test_report_severity_supports_inconclusive_and_records_detector():
    r = _report("Tiny.")
    assert r["summary"]["severity"] == "inconclusive"
    assert r["identity"]["detector_manifest_id"] == "m"
    assert r["semantic"]["detector_id"]


def test_corpus_summary_references_evidence_outputs():
    outs = [{"output_id": "a", "text": "The night was dark and cold and long. " + DEG},
            {"output_id": "b", "text": "The night was dark and cold and long. Then dawn came."}]
    cs = corpus_slop_summary(outs, "target_base")
    assert cs["opening_pattern_clusters"]
    assert cs["evidence_output_ids"]
    assert cs["confidence"] in ("high", "moderate", "low", "inconclusive")
