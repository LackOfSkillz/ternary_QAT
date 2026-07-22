"""Sentence-rhythm and paragraph-shape metrics (Dispatch 23, slop Layer 1).

Sentence-length mean/variance/entropy capture rhythm collapse (uniform sentence length is a
degeneration signal), but LOW variance is legitimate in terse styles — these are diagnostic
signals, never a standalone verdict. Deterministic, versioned, dependency-free.
"""
import math
import re

VERSION = "rhythm-v1"


def _sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text or "")
    return [p.strip() for p in parts if p and p.strip()]


def _words(s):
    return re.findall(r"\w+", s)


def sentence_rhythm(text):
    lengths = [len(_words(s)) for s in _sentences(text)]
    if not lengths:
        return {"version": VERSION, "count": 0, "mean": 0.0, "variance": 0.0, "entropy": 0.0}
    n = len(lengths)
    mean = sum(lengths) / n
    variance = sum((x - mean) ** 2 for x in lengths) / n
    # entropy over the distribution of (binned) sentence lengths
    from collections import Counter
    dist = Counter(lengths)
    entropy = 0.0
    for c in dist.values():
        p = c / n
        entropy -= p * math.log2(p)
    return {"version": VERSION, "count": n, "mean": round(mean, 3),
            "variance": round(variance, 3), "entropy": round(entropy, 4)}


def paragraph_shape(text):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    lens = [len(_words(p)) for p in paras]
    return {"version": VERSION, "paragraph_count": len(paras),
            "word_lengths": lens,
            "mean_words": round(sum(lens) / len(lens), 2) if lens else 0.0}
