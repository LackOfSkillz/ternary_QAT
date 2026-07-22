"""Exact-preservation / no-change protocol validator (Dispatch 21, Phase E #2).

For a no-change case the contract requires the model to return the structured wrapper
    {"changed": false, "reason": <brief>, "text": <source>}
with ``text`` equal to the source. Dispatch 20 showed every checkpoint failing this:
they emitted bare prose (no wrapper) or looped the source. Only two records in the whole
of Dataset A ever teach the wrapper, and none teach ``changed: true`` — a core gap.

``validate_preservation`` handles two modes:
  - ``exact``: ``returned text == source`` byte-for-byte (used when the record forbids
    even whitespace normalization).
  - ``normalized``: whitespace-collapsed equality (the current Dataset A no-change rule).

The default is ``normalized`` unless the contract sets
``exact_source_preservation_required: true``.
"""
import json
import re

from linewright.evaluation import GateResult


def _norm_ws(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def validate_preservation(output, source, contract):
    """Return a ``no_change_valid`` :class:`GateResult`.

    ``contract`` must carry ``expects_no_change`` (bool). When it is falsy the check is
    not applicable and ``valid`` is ``None`` (never a silent pass).
    """
    if not contract.get("expects_no_change"):
        return GateResult("no_change_valid", valid=None,
                          evidence={"applicable": False})

    exact = bool(contract.get("exact_source_preservation_required"))
    labels, ev = [], {"mode": "exact" if exact else "normalized"}

    parsed = None
    try:
        parsed = json.loads((output or "").strip())
    except Exception:
        parsed = None

    if not isinstance(parsed, dict) or "changed" not in parsed:
        labels.append("no_change_wrapper_missing")
        ev["wrapper_present"] = False
        return GateResult("no_change_valid", valid=False, failure_labels=labels, evidence=ev)

    ev["wrapper_present"] = True
    if parsed.get("changed") is not False:
        labels.append("wrong_changed_flag")
        ev["changed_flag"] = parsed.get("changed")

    text = parsed.get("text", "")
    if exact:
        match = text == source
    else:
        match = _norm_ws(text) == _norm_ws(source)
    ev["text_matches_source"] = match
    if not match:
        labels.append("exact_preservation_failure")
        ev["source_len"] = len(source or "")
        ev["returned_len"] = len(text or "")

    valid = not labels
    return GateResult("no_change_valid", valid=valid, failure_labels=labels, evidence=ev)
