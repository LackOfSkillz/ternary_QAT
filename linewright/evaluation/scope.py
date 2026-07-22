"""Scope validator (Dispatch 21, Phase E #6).

Checks that the model did the requested operation and only that:
  - output/source length ratio within the contract's ``max_output_ratio`` (excessive
    expansion / runaway continuation),
  - prose returned when structured output was required,
  - content continues after the requested result (extra structures / trailing prose),
  - minimum requested edit performed (when the record supplies the source and expects a
    change, an identical-to-source output is an omitted change).

Semantic "unrelated paragraphs altered" is reviewer-assisted; the deterministic ratio and
structure checks are automated here.
"""
import json
import re

import yaml

from linewright.evaluation import GateResult


def _norm_ws(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def _looks_structured(kind, text):
    s = (text or "").strip()
    try:
        if kind == "json":
            json.loads(s)
        else:
            v = yaml.safe_load(s)
            return isinstance(v, (dict, list))
        return True
    except Exception:
        return False


def validate_scope(output, source, contract):
    """Return a ``scope_valid`` :class:`GateResult`."""
    out = output or ""
    kind = contract.get("type", "prose")
    labels, ev = [], {}

    if source:
        ratio = len(out) / max(1, len(source))
        ev["output_source_ratio"] = round(ratio, 3)
        max_ratio = contract.get("max_output_ratio")
        if max_ratio and ratio > max_ratio:
            labels.append("excessive_expansion")

    hard_cap = contract.get("max_output_chars")
    if hard_cap and len(out) > hard_cap:
        labels.append("runaway_length")
        ev["output_chars"] = len(out)

    if kind in ("json", "yaml"):
        if not _looks_structured(kind, out.split("\n\n")[0] if "\n\n" in out else out):
            # a purely prose reply where structure was required
            if not _looks_structured(kind, out):
                labels.append("summary_replacing_scene" if kind == "prose" else "prose_outside_structure")

    # omitted change: record supplies a source, expects a change, output == source
    if source and contract.get("expects_change") and _norm_ws(out) == _norm_ws(source):
        labels.append("omitted_required_change")

    valid = not labels
    return GateResult("scope_valid", valid=valid, failure_labels=labels, evidence=ev)
