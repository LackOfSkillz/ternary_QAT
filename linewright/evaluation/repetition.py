"""Repetition / degeneration validator (Dispatch 21, Phase E #3).

The dominant Dispatch-20 failure was runaway repetition that the parse-only gate scored
valid. This validator measures repetition deterministically and reports the evidence.

A response fails ``repetition_valid`` when any of these trip:
  - an exact sentence repeats >= ``MAX_SENTENCE_REPEAT`` times,
  - a normalized sentence (lowercased, whitespace/punctuation-collapsed) repeats
    >= ``MAX_SENTENCE_REPEAT`` times,
  - some word n-gram (n in ``NGRAM_SIZES``) repeats >= ``MAX_NGRAM_REPEAT`` times,
  - a paragraph opening (first ``OPENING_WORDS`` words) repeats >= ``MAX_OPENING_REPEAT``,
  - the type-token ratio falls below ``MIN_TTR`` on a response of >= ``TTR_MIN_TOKENS`` tokens.

Thresholds are intentionally lenient so a legitimate refrain or anaphora is not punished;
the smoke degenerations exceed every one of them by a wide margin (e.g. 40x a sentence).
"""
import re
from collections import Counter

from linewright.evaluation import GateResult

MAX_SENTENCE_REPEAT = 3     # a sentence appearing 3+ times is degenerate, not a refrain
MIN_SENTENCE_WORDS_FOR_DUP = 4   # short structured field values ("established") legitimately
                                 # repeat; only count substantial sentences as duplicates.
                                 # Short-phrase loops ("the door creaks" x45) are caught by
                                 # the n-gram signal instead.
MAX_NGRAM_REPEAT = 4        # a 5..10-gram repeating 4+ times is a loop
MAX_OPENING_REPEAT = 3
OPENING_WORDS = 5
NGRAM_SIZES = (5, 6, 8, 10)
MIN_TTR = 0.34
TTR_MIN_TOKENS = 50


def _sentences(text):
    # split on sentence terminators and hard line breaks; keep non-empty trimmed pieces
    parts = re.split(r"(?<=[.!?])\s+|\n+", text or "")
    return [p.strip() for p in parts if p and p.strip()]


def _norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s.lower())).strip()


def _tokens(text):
    return re.findall(r"\w+", (text or "").lower())


def _max_ngram_repeat(tokens, n):
    if len(tokens) < n:
        return 0, None
    grams = Counter(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))
    gram, cnt = grams.most_common(1)[0]
    return cnt, " ".join(gram)


def analyze_repetition(output):
    """Return a :class:`GateResult` named ``repetition_valid`` with measured evidence."""
    text = output or ""
    sents = _sentences(text)
    toks = _tokens(text)
    labels = []
    ev = {"sentence_count": len(sents), "token_count": len(toks)}

    # exact + normalized sentence repetition (substantial sentences only; short field
    # values legitimately repeat in structured output and must not count as duplicates)
    substantial = [s for s in sents if len(_tokens(s)) >= MIN_SENTENCE_WORDS_FOR_DUP]
    exact = Counter(substantial)
    norm = Counter(_norm(s) for s in substantial if _norm(s))
    exact_top = exact.most_common(1)[0] if exact else ("", 0)
    norm_top = norm.most_common(1)[0] if norm else ("", 0)
    ev["max_exact_sentence_repeat"] = exact_top[1]
    ev["max_exact_sentence"] = exact_top[0][:80]
    ev["max_normalized_sentence_repeat"] = norm_top[1]

    # paragraph-opening repetition
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    openings = Counter(" ".join(_tokens(p)[:OPENING_WORDS]) for p in paras if _tokens(p))
    open_top = openings.most_common(1)[0] if openings else ("", 0)
    ev["max_paragraph_opening_repeat"] = open_top[1]

    # worst n-gram repeat across the configured sizes
    worst_n, worst_cnt, worst_gram = 0, 0, None
    for n in NGRAM_SIZES:
        cnt, gram = _max_ngram_repeat(toks, n)
        if cnt > worst_cnt:
            worst_n, worst_cnt, worst_gram = n, cnt, gram
    ev["worst_ngram_n"] = worst_n
    ev["worst_ngram_repeat"] = worst_cnt
    ev["worst_ngram"] = worst_gram

    # type-token ratio (lexical diversity)
    ttr = round(len(set(toks)) / len(toks), 4) if toks else 1.0
    ev["type_token_ratio"] = ttr

    if exact_top[1] >= MAX_SENTENCE_REPEAT:
        labels.append("duplicate_sentence")
    if norm_top[1] >= MAX_SENTENCE_REPEAT and "duplicate_sentence" not in labels:
        labels.append("paraphrased_sentence_repeat")
    if open_top[1] >= MAX_OPENING_REPEAT:
        labels.append("repeated_paragraph_opening")
    if worst_cnt >= MAX_NGRAM_REPEAT:
        labels.append("repeated_ngram")
    if len(toks) >= TTR_MIN_TOKENS and ttr < MIN_TTR:
        labels.append("low_lexical_diversity")

    valid = not labels
    return GateResult("repetition_valid", valid=valid, failure_labels=labels, evidence=ev)
