"""Truncation / completion validator (Dispatch 21, Phase E #7).

Detects output that stopped before it was finished:
  - empty output,
  - structured output that starts like JSON/YAML but does not parse (unclosed / cut off),
  - prose that ends mid-sentence (no terminal punctuation / quote),
  - generation that ran to the token budget (``hit_token_cap`` supplied by the caller),
  - empty required fields in a parsed object.
"""
import json
import re

import yaml

from linewright.evaluation import GateResult

_TERMINALS = tuple('.!?)"”’') + ("...",)


def validate_completion(output, contract, hit_token_cap=False):
    """Return a ``completion_valid`` :class:`GateResult`.

    ``hit_token_cap`` should be True when generation terminated on max_new_tokens rather
    than an end-of-sequence token — a strong truncation signal.
    """
    out = output or ""
    kind = contract.get("type", "prose")
    labels, ev = [], {"hit_token_cap": bool(hit_token_cap)}

    if not out.strip():
        return GateResult("completion_valid", valid=False,
                          failure_labels=["empty_output"], evidence=ev)

    if hit_token_cap:
        labels.append("incomplete_output")

    if kind in ("json", "yaml"):
        s = out.strip()
        looks = s[:1] in "{[" or (kind == "yaml" and ":" in s.split("\n", 1)[0])
        parses = False
        try:
            if kind == "json":
                json.loads(s); parses = True
            else:
                parses = isinstance(yaml.safe_load(s), (dict, list))
        except Exception:
            parses = False
        ev["parses"] = parses
        if looks and not parses:
            labels.append("truncated_structure")
        if parses:
            obj = json.loads(s) if kind == "json" else yaml.safe_load(s)
            if isinstance(obj, dict):
                # an empty list is a valid "none found" answer (e.g. insufficient_evidence:
                # []); only null / empty-string required fields signal truncation.
                empty = [k for k in contract.get("required_keys", [])
                         if k in obj and (obj[k] is None or obj[k] == "")]
                if empty:
                    labels.append("incomplete_output")
                    ev["empty_required_fields"] = empty
    else:
        stripped = out.rstrip()
        ends_clean = stripped.endswith(_TERMINALS)
        ev["ends_with_terminal"] = ends_clean
        if not ends_clean:
            labels.append("incomplete_output")

    valid = not labels
    return GateResult("completion_valid", valid=valid, failure_labels=labels, evidence=ev)
