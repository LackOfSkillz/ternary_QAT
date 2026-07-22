"""Memorization / overlap validator (Dispatch 21, Phase E #4).

Measures how much a response reproduces material it should not have memorized. The
subtlety: in a focused-revision task, preserving the *source* is CORRECT behaviour, so
overlap is measured against **training targets** (other records' gold outputs) and the
record's own gold — never against the source the model was told to preserve.

Reported quantities:
  - exact / normalized match to this record's gold,
  - similarity ratio to the nearest training target,
  - longest shared character span with any training target,
  - longest shared token span with any training target.

Fails ``memorization_valid`` when the response exactly/near-exactly reproduces the gold,
or shares an implausibly long verbatim span with some *other* record's training target.
"""
import re
from difflib import SequenceMatcher

from linewright.evaluation import GateResult

NEAR_GOLD_RATIO = 0.97
MAX_TRAIN_CHAR_SPAN = 200      # verbatim span shared with another record's target
MAX_TRAIN_TOKEN_SPAN = 30


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def _longest_char_span(a, b):
    if not a or not b:
        return 0
    m = SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b))
    return m.size


def _longest_token_span(a, b):
    ta, tb = re.findall(r"\w+", a.lower()), re.findall(r"\w+", b.lower())
    if not ta or not tb:
        return 0
    m = SequenceMatcher(None, ta, tb, autojunk=False).find_longest_match(0, len(ta), 0, len(tb))
    return m.size


def analyze_overlap(output, gold, train_targets=None):
    """Return a ``memorization_valid`` :class:`GateResult`.

    ``train_targets`` is an iterable of gold outputs from OTHER (training) records.
    """
    out = output or ""
    labels, ev = [], {}
    train_targets = [t for t in (train_targets or []) if t and t != gold]

    exact = _norm(out) == _norm(gold) and bool(gold)
    ratio_gold = SequenceMatcher(None, out, gold or "", autojunk=False).ratio()
    ev["exact_gold_match"] = exact
    ev["gold_similarity_ratio"] = round(ratio_gold, 4)

    if exact:
        labels.append("exact_gold_reproduction")
    elif gold and ratio_gold >= NEAR_GOLD_RATIO:
        labels.append("near_exact_gold_reproduction")

    best_ratio, best_char, best_tok, best_id = 0.0, 0, 0, None
    for i, t in enumerate(train_targets):
        r = SequenceMatcher(None, out, t, autojunk=False).ratio()
        c = _longest_char_span(out, t)
        k = _longest_token_span(out, t)
        if c > best_char:
            best_char, best_id = c, i
        best_ratio = max(best_ratio, r)
        best_tok = max(best_tok, k)
    ev["nearest_train_ratio"] = round(best_ratio, 4)
    ev["longest_train_char_span"] = best_char
    ev["longest_train_token_span"] = best_tok

    if best_char >= MAX_TRAIN_CHAR_SPAN or best_tok >= MAX_TRAIN_TOKEN_SPAN:
        labels.append("long_train_target_overlap")

    valid = not labels
    return GateResult("memorization_valid", valid=valid, failure_labels=labels, evidence=ev)
