"""Per-output slop report assembler (Dispatch 23, Module J).

Assembles the deterministic / semantic / lexical-style / reviewer blocks into a
``slop-report`` (benchmarks/schemas/slop-report-schema.yaml). It NEVER produces one opaque
score; each block keeps its own evidence and confidence. Severity escalation reuses ONLY the
already-justified Dispatch-21 repetition gate (a real, documented threshold); every other
numeric is a reported signal with ``threshold_status: unvalidated``.
"""
from linewright.evaluation import GateResult
from linewright.evaluation.repetition import analyze_repetition
from linewright.evaluation.slop import deterministic as det_mod
from linewright.evaluation.slop import semantic_interfaces as sem_mod
from linewright.evaluation.slop.reviewer_checklist import VERSION as CHECKLIST_VERSION

VERSION = "slop-report-v1"


def _severity(rep_gate, det):
    """Evidence-based severity. The ONLY escalation threshold is the justified Dispatch-21
    repetition gate; short/clean outputs stay low/none/inconclusive."""
    limitations = []
    if det["short_output_metric_limitations"]:
        limitations.append("short output: diversity metrics unstable, reported not judged")
    ev = rep_gate.evidence
    worst_ngram = ev.get("worst_ngram_repeat", 0)
    ttr = ev.get("type_token_ratio", 1.0)
    if rep_gate.valid is False:
        # degenerate per the justified gate
        if worst_ngram >= 10 or ttr < 0.2:
            sev = "severe"
        else:
            sev = "high"
    elif det["exact_duplicate_sentences"] or det["repeated_paragraph_openings"]:
        sev = "moderate"
    elif det["short_output_metric_limitations"]:
        sev = "inconclusive"
    else:
        sev = "low" if (det["exact_duplicate_clauses"] or det["repeated_sentence_openings"]) else "none"
    return sev, limitations


def _dominant(rep_gate, det):
    out = []
    if rep_gate.valid is False:
        out += [l for l in rep_gate.failure_labels]
    if det["exact_duplicate_clauses"]:
        out.append("duplicate_clause")
    if det["repeated_paragraph_openings"]:
        out.append("repeated_paragraph_opening")
    return sorted(set(out))


def build_slop_report(output, *, output_id, detector_manifest_id, item_id=None, run_id=None,
                      source=None, hit_token_cap=False, input_characteristics=None,
                      semantic_detector=None, reviewer_result=None, reference_profile_id=None,
                      created_at="unset"):
    det = det_mod.deterministic_slop(output, source=source, hit_token_cap=hit_token_cap)
    rep_gate = analyze_repetition(output)
    detector = semantic_detector or sem_mod.NullSemanticDetector()
    semantic = detector.analyze(output)

    sev, limitations = _severity(rep_gate, det)
    ld = det["lexical_diversity"]

    reviewer_block = {"checklist_results": reviewer_result or [], "reviewer_ids": [],
                      "reviewer_calibration_status": {}, "agreement": None,
                      "evidence_spans": [], "checklist_version": CHECKLIST_VERSION}

    return {
        "schema": "slop-report", "schema_version": 1, "version": VERSION,
        "identity": {"slop_report_id": f"slop-{output_id}", "run_id": run_id,
                     "output_id": output_id, "item_id": item_id,
                     "detector_manifest_id": detector_manifest_id,
                     "reference_profile_id": reference_profile_id, "created_at": created_at},
        "input_characteristics": dict(input_characteristics or {},
                                      actual_length=det["token_count"],
                                      short_output_metric_limitations=det["short_output_metric_limitations"]),
        "deterministic": {
            "exact_duplicate_sentences": det["exact_duplicate_sentences"],
            "exact_duplicate_clauses": det["exact_duplicate_clauses"],
            "repeated_ngram_rates": det["repeated_ngram_rates"],
            "repeated_sentence_openings": det["repeated_sentence_openings"],
            "repeated_paragraph_openings": det["repeated_paragraph_openings"],
            "compression_ratio": det["compression_ratio"],
            "lexical_diversity": ld,
            "sentence_rhythm": det["sentence_rhythm"],
            "paragraph_shape": det["paragraph_shape"],
            "output_to_source_ratio": det["output_to_source_ratio"],
            "source_overlap": det["source_overlap"],
            "hit_token_cap": det["hit_token_cap"],
            "evidence_spans": det["evidence_spans"],
        },
        "semantic": semantic,
        "lexical_style": {"stock_phrase_hits": [], "clustered_stock_phrases": [],
                          "vague_language_signals": [], "abstraction_signals": [],
                          "specificity_signals": [], "weak_verb_signals": [],
                          "evidence_spans": [],
                          "note": "phrase inventory is one signal only; never a sole detector"},
        "reviewer": reviewer_block,
        "corpus_level": {"note": "per-run analysis lives in slop-corpus-summary (corpus.py)"},
        "summary": {
            "severity": sev,
            "dominant_failure_types": _dominant(rep_gate, det),
            "fatal_slop_failure": sev in ("severe",),
            "mechanical_confidence": "high" if rep_gate.valid is not None else "inconclusive",
            "semantic_confidence": semantic.get("detector_confidence", "unvalidated"),
            "reviewer_confidence": "inconclusive" if not reviewer_result else "moderate",
            "overall_confidence": "high" if rep_gate.valid is False else (
                "inconclusive" if det["short_output_metric_limitations"] else "moderate"),
            "limitations": limitations + [
                "numeric thresholds other than the repetition gate are unvalidated",
                "semantic detectors are interface-only in this build"],
            "likely_bottlenecks": [], "recommended_dataset_actions": [],
            "recommended_training_actions": [], "recommended_context_actions": [],
            "recommended_decoding_actions": [],
        },
    }
