"""Constraint / canon-fidelity validator (Dispatch 21, Phase E #5).

Validates the machine-decidable parts of canon and constraint tasks against a record's
``validation_expectations``:

    {
      "constraint_ids": ["K1"],            # constraint_check: gold causal set (order-free)
      "expected_facts": ["...substring..."],   # canon: entity/fact substrings that must appear
      "forbidden_inventions": ["..."],     # substrings that must NOT appear (invented facts)
      "required_certainties": {"...": "character_belief"},
    }

Set-equality on ``constraint_ids`` reproduces the dataset's causal-set grading (a missing
or extra id fails and is named). Fact presence/absence is substring-based and reported as
evidence. Deeper semantic judgements (belief-vs-fact promotion, POV) stay reviewer-
assisted; this validator automates every check that is deterministically decidable and
flags the rest as ``reviewer_assisted``.
"""
import json

from linewright.evaluation import GateResult


def _parse(output):
    try:
        return json.loads((output or "").strip())
    except Exception:
        return None


def validate_constraints(output, expectations):
    """Return a ``constraint_valid`` :class:`GateResult`.

    ``valid`` is ``None`` when no machine-decidable expectation is present (the judgement
    is entirely reviewer-assisted) rather than a silent pass.
    """
    exp = expectations or {}
    parsed = _parse(output)
    labels, ev = [], {}
    checked_any = False

    # constraint_check: gold constraint_ids must equal the declared causal set
    if "constraint_ids" in exp:
        checked_any = True
        want = set(exp["constraint_ids"])
        got = set(parsed.get("constraint_ids", [])) if isinstance(parsed, dict) else set()
        ev["constraint_ids_expected"] = sorted(want)
        ev["constraint_ids_got"] = sorted(got)
        if got != want:
            labels.append("constraint_ignored")
            ev["constraint_ids_missing"] = sorted(want - got)
            ev["constraint_ids_extra"] = sorted(got - want)

    # canon: required facts present, forbidden inventions absent (substring, case-insensitive)
    hay = (output or "").lower()
    if exp.get("expected_facts"):
        checked_any = True
        missing = [f for f in exp["expected_facts"] if f.lower() not in hay]
        ev["expected_facts_total"] = len(exp["expected_facts"])
        ev["expected_facts_missing"] = missing
        if missing:
            labels.append("unsupported_inference")
    if exp.get("forbidden_inventions"):
        checked_any = True
        present = [f for f in exp["forbidden_inventions"] if f.lower() in hay]
        ev["forbidden_present"] = present
        if present:
            labels.append("invented_fact")

    ev["reviewer_assisted"] = bool(exp.get("reviewer_assisted", False))
    if not checked_any:
        return GateResult("constraint_valid", valid=None, evidence={"applicable": False})
    valid = not labels
    return GateResult("constraint_valid", valid=valid, failure_labels=labels, evidence=ev)
