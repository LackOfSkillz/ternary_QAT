"""Deterministic lexical-diversity metrics (Dispatch 23, slop Layer 1).

Standard NLP measures (source_supported as measures; their use as slop signals is
engineering_inference — see the research review). All are deterministic and versioned.
Short texts are unstable for MTLD/HDD, so callers must honour the ``short_output`` flag from
``deterministic.py``; these functions still return a value but it is not a verdict.

No external dependency: uses stdlib + math only.
"""
import math
import re

VERSION = "lexical-v1"


def tokens(text):
    return re.findall(r"[a-zA-Z']+", (text or "").lower())


def unique_token_ratio(toks):
    return round(len(set(toks)) / len(toks), 4) if toks else 1.0


def hapax_rate(toks):
    from collections import Counter
    if not toks:
        return 0.0
    c = Counter(toks)
    return round(sum(1 for w in c if c[w] == 1) / len(toks), 4)


def mattr(toks, window=50):
    """Moving-average type-token ratio. Falls back to plain TTR for short texts."""
    if len(toks) <= window:
        return unique_token_ratio(toks)
    ratios = []
    for i in range(len(toks) - window + 1):
        w = toks[i:i + window]
        ratios.append(len(set(w)) / window)
    return round(sum(ratios) / len(ratios), 4)


def _mtld_pass(toks, threshold=0.72):
    factors = 0.0
    types = set()
    count = 0
    for t in toks:
        count += 1
        types.add(t)
        ttr = len(types) / count
        if ttr <= threshold:
            factors += 1
            types, count = set(), 0
    if count > 0:
        ttr = len(types) / count if count else 1.0
        factors += (1 - ttr) / (1 - threshold)
    return len(toks) / factors if factors else float(len(toks))


def mtld(toks, threshold=0.72):
    """Measure of Textual Lexical Diversity (bidirectional mean). Length-robust."""
    if len(toks) < 10:
        return round(float(len(set(toks))), 4)
    fwd = _mtld_pass(toks, threshold)
    bwd = _mtld_pass(list(reversed(toks)), threshold)
    return round((fwd + bwd) / 2, 4)


def hdd(toks, sample=42):
    """HD-D: mean contribution of each type to the TTR of a random sample of size `sample`
    (McCarthy & Jarvis 2010), via the hypergeometric distribution. Length-guarded."""
    n = len(toks)
    if n == 0:
        return 0.0
    if n < sample:
        sample = n
    from collections import Counter
    counts = Counter(toks)
    total = 0.0
    for w, freq in counts.items():
        # P(at least one token of type w in a sample of `sample` from n) via complement
        try:
            p_none = math.comb(n - freq, sample) / math.comb(n, sample)
        except (ValueError, ZeroDivisionError):
            p_none = 0.0
        contrib = (1 - p_none) * (1 / sample)
        total += contrib
    return round(total, 4)


def lexical_diversity(text):
    toks = tokens(text)
    return {
        "version": VERSION,
        "token_count": len(toks),
        "unique_token_ratio": unique_token_ratio(toks),
        "mattr": mattr(toks),
        "mtld": mtld(toks),
        "hdd": hdd(toks),
        "hapax_rate": hapax_rate(toks),
    }
