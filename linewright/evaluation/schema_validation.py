"""Structured-output validator (Dispatch 21, Phase E #1).

Validates a response against an output contract:

    contract = {
        "type": "json" | "yaml" | "prose",
        "required_keys": [...],
        "forbidden_keys": [...],          # e.g. "explanation" when output-only is required
        "key_types": {"key": "str"|"bool"|"list"|"dict"|"int"|"number"|"null-ok:str"},
        "container": "object" | "array",  # top-level shape
        "allow_prose_outside_structure": bool,
    }

Detects parse failures, missing required keys, forbidden extra keys, alternate key
names, wrong value types, wrong container shape, unauthorized text outside the
structure, and incomplete structures. It reports which keys were seen so a reviewer can
diagnose alternate-key drift (the QAT-20 canon case used ``speaker``/``claim`` instead
of ``entity``/``fact``).
"""
import json
import re

import yaml

from linewright.evaluation import GateResult

_PY_TYPES = {
    "str": str, "bool": bool, "int": int, "list": list, "dict": dict,
    "number": (int, float),
}


def _extract_first_structure(text, kind):
    """Best-effort parse of the first top-level JSON/YAML value in ``text``.

    Returns ``(parsed_or_None, trailing_text)`` where ``trailing_text`` is any content
    after the first structure (used to detect ``continued_after_task_complete``).
    """
    s = (text or "").strip()
    # strip a leading ```json / ```yaml fence if present (and record it as a violation upstream)
    if kind == "json":
        try:
            obj = json.loads(s)
            return obj, ""
        except Exception:
            pass
        dec = json.JSONDecoder()
        s2 = s.lstrip()
        try:
            obj, end = dec.raw_decode(s2)
            return obj, s2[end:].strip()
        except Exception:
            return None, ""
    else:  # yaml
        try:
            obj = yaml.safe_load(s)
            return (obj if isinstance(obj, (dict, list)) else None), ""
        except Exception:
            return None, ""


def _type_ok(value, spec):
    null_ok = spec.startswith("null-ok:")
    base = spec.split(":", 1)[1] if null_ok else spec
    if value is None:
        return null_ok
    if base == "bool":
        return isinstance(value, bool)
    if base == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    py = _PY_TYPES.get(base)
    return isinstance(value, py) if py else True


def validate_structured(output, contract):
    """Return a ``schema_valid`` :class:`GateResult` for ``output`` under ``contract``."""
    kind = contract.get("type", "prose")
    labels, ev = [], {"expected_type": kind}

    if kind == "prose":
        valid = bool(output and output.strip())
        if not valid:
            labels.append("empty_output")
        return GateResult("schema_valid", valid=valid, failure_labels=labels, evidence=ev)

    fence = bool(re.match(r"^\s*```", output or ""))
    if fence:
        labels.append("markdown_fence_violation")

    parsed, trailing = _extract_first_structure(output, kind)
    ev["parsed"] = parsed is not None
    if parsed is None:
        labels.append("invalid_json" if kind == "json" else "invalid_yaml")
        return GateResult("schema_valid", valid=False, failure_labels=labels,
                          evidence=ev, )

    container = contract.get("container", "object")
    if container == "object" and not isinstance(parsed, dict):
        labels.append("wrong_container_shape")
    if container == "array" and not isinstance(parsed, list):
        labels.append("wrong_container_shape")

    if trailing and not contract.get("allow_prose_outside_structure", False):
        labels.append("continued_after_task_complete")
        ev["trailing_chars"] = len(trailing)

    if isinstance(parsed, dict):
        seen = list(parsed.keys())
        ev["keys_seen"] = seen
        required = contract.get("required_keys", [])
        forbidden = contract.get("forbidden_keys", [])
        missing = [k for k in required if k not in parsed]
        extra_forbidden = [k for k in forbidden if k in parsed]
        # keys that are neither required nor explicitly forbidden but look like alternates
        unexpected = [k for k in seen if required and k not in required
                      and k not in forbidden]
        if missing:
            labels.append("missing_required_key")
            ev["missing_keys"] = missing
        if extra_forbidden:
            labels.append("forbidden_extra_key")
            ev["forbidden_present"] = extra_forbidden
        if unexpected and contract.get("strict_keys", True):
            labels.append("alternate_key_names")
            ev["unexpected_keys"] = unexpected
        for k, spec in (contract.get("key_types") or {}).items():
            if k in parsed and not _type_ok(parsed[k], spec):
                labels.append("wrong_value_type")
                ev.setdefault("type_mismatches", []).append(
                    {"key": k, "expected": spec, "got": type(parsed[k]).__name__})

        # nested item-key contract: each dict item of a listed key must carry exactly the
        # required item keys (this is where the QAT-20 canon drift lived: speaker/claim
        # instead of entity/fact inside facts[]).
        for list_key, item_keys in (contract.get("item_required_keys") or {}).items():
            val = parsed.get(list_key)
            if not isinstance(val, list):
                continue
            for idx, item in enumerate(val):
                if not isinstance(item, dict):
                    continue
                miss = [ik for ik in item_keys if ik not in item]
                extra = [ik for ik in item.keys() if ik not in item_keys]
                if miss and "missing_required_key" not in labels:
                    labels.append("missing_required_key")
                    ev.setdefault("item_missing_keys", []).append({list_key: {idx: miss}})
                if extra and "alternate_key_names" not in labels:
                    labels.append("alternate_key_names")
                    ev.setdefault("item_unexpected_keys", []).append({list_key: {idx: extra}})

    valid = not labels
    gr = GateResult("schema_valid", valid=valid, failure_labels=labels, evidence=ev)
    gr.evidence["parsed_value"] = parsed
    return gr
