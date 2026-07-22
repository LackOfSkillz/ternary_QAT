"""Repetition measures for slop (Dispatch 23, slop Layer 1).

Builds on the Dispatch-21 repetition gate (linewright.evaluation.repetition) but reports the
full evidence set a slop report needs: exact duplicate sentences/clauses, per-n repeated
n-gram rates, repeated sentence/paragraph openings, and a compression ratio. Every measure
retains a verbatim evidence span. These are SIGNALS; the pass/fail verdict still comes from
the justified Dispatch-21 gate, not a new invented threshold.
"""
import re
import zlib
from collections import Counter

from linewright.evaluation import repetition as gate_rep

VERSION = "slop-repetition-v1"
NGRAM_SIZES = (3, 4, 5, 8)


def _clauses(text):
    parts = re.split(r"[.!?;:,]\s+|\n+", text or "")
    return [p.strip() for p in parts if p and p.strip()]


def _openings(units, n_words):
    return Counter(" ".join(re.findall(r"\w+", u.lower())[:n_words]) for u in units
                   if re.findall(r"\w+", u))


def repetition_measures(text):
    text = text or ""
    sents = gate_rep._sentences(text)
    substantial = [s for s in sents if len(gate_rep._tokens(s)) >= gate_rep.MIN_SENTENCE_WORDS_FOR_DUP]
    exact_sent = Counter(substantial)
    dup_sentences = {s: c for s, c in exact_sent.items() if c >= 2}
    clauses = _clauses(text)
    long_clauses = [c for c in clauses if len(gate_rep._tokens(c)) >= 3]
    dup_clauses = {c: n for c, n in Counter(long_clauses).items() if n >= 2}

    toks = gate_rep._tokens(text)
    ngram_rates = {}
    for n in NGRAM_SIZES:
        cnt, gram = gate_rep._max_ngram_repeat(toks, n)
        ngram_rates[n] = {"max_repeat": cnt, "gram": gram}

    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    para_openings = {k: v for k, v in _openings(paras, 5).items() if v >= 2}
    sent_openings = {k: v for k, v in _openings(sents, 4).items() if v >= 3}

    raw = text.encode("utf-8")
    comp = zlib.compress(raw, 9)
    compression_ratio = round(len(comp) / len(raw), 4) if raw else 1.0

    evidence = []
    for s, c in list(dup_sentences.items())[:5]:
        evidence.append({"kind": "duplicate_sentence", "count": c, "span": s[:120]})
    worst_n = max(ngram_rates, key=lambda n: ngram_rates[n]["max_repeat"])
    if ngram_rates[worst_n]["max_repeat"] >= gate_rep.MAX_NGRAM_REPEAT:
        evidence.append({"kind": "repeated_ngram", "n": worst_n,
                         "count": ngram_rates[worst_n]["max_repeat"],
                         "span": ngram_rates[worst_n]["gram"]})

    return {
        "version": VERSION,
        "exact_duplicate_sentences": sum(c for c in dup_sentences.values()) - len(dup_sentences)
        if dup_sentences else 0,
        "distinct_duplicated_sentences": len(dup_sentences),
        "exact_duplicate_clauses": sum(dup_clauses.values()) - len(dup_clauses) if dup_clauses else 0,
        "repeated_ngram_rates": {n: ngram_rates[n]["max_repeat"] for n in ngram_rates},
        "repeated_sentence_openings": len(sent_openings),
        "repeated_paragraph_openings": len(para_openings),
        "compression_ratio": compression_ratio,
        "evidence_spans": evidence,
    }
