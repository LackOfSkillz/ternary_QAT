"""Deterministic slop-metric orchestrator (Dispatch 23, slop Layer 1).

Assembles the repetition, lexical, and rhythm measures plus output-length behaviour into the
``deterministic`` block of a slop report. Deterministic and versioned: identical input ->
identical output. Short outputs set ``short_output_metric_limitations`` and their diversity
metrics are reported WITH that caveat, never as a verdict. Source overlap is reported
separately from slop (it is a fidelity signal, not a slop signal).
"""
import re

from linewright.evaluation.slop import lexical, rhythm, repetition

VERSION = "slop-deterministic-v1"
SHORT_OUTPUT_TOKENS = 40   # below this, diversity metrics are unstable (flagged, not judged)


def _norm_ws(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def deterministic_slop(output, source=None, hit_token_cap=False):
    text = output or ""
    toks = lexical.tokens(text)
    rep = repetition.repetition_measures(text)
    lex = lexical.lexical_diversity(text)
    rhy = rhythm.sentence_rhythm(text)
    para = rhythm.paragraph_shape(text)

    out_src_ratio = None
    source_overlap = None
    if source:
        out_src_ratio = round(len(text) / max(1, len(source)), 4)
        # source overlap is a FIDELITY signal, kept separate from slop
        s_norm, o_norm = _norm_ws(source).lower(), _norm_ws(text).lower()
        source_overlap = 1.0 if s_norm and s_norm in o_norm else 0.0

    return {
        "version": VERSION,
        "token_count": len(toks),
        "short_output_metric_limitations": len(toks) < SHORT_OUTPUT_TOKENS,
        "exact_duplicate_sentences": rep["exact_duplicate_sentences"],
        "exact_duplicate_clauses": rep["exact_duplicate_clauses"],
        "repeated_ngram_rates": rep["repeated_ngram_rates"],
        "repeated_sentence_openings": rep["repeated_sentence_openings"],
        "repeated_paragraph_openings": rep["repeated_paragraph_openings"],
        "compression_ratio": rep["compression_ratio"],
        "lexical_diversity": {k: lex[k] for k in
                              ("unique_token_ratio", "mattr", "mtld", "hdd", "hapax_rate")},
        "sentence_rhythm": {k: rhy[k] for k in ("mean", "variance", "entropy")},
        "paragraph_shape": para,
        "output_to_source_ratio": out_src_ratio,
        "source_overlap": source_overlap,          # separate from slop
        "hit_token_cap": bool(hit_token_cap),
        "evidence_spans": rep["evidence_spans"],
    }
