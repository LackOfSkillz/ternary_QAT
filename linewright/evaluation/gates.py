"""Mechanical evaluation-gate aggregator (Dispatch 21, Phase E).

Runs every validator over one response and returns the nine SEPARATE gate dimensions the
dispatch requires — never collapsed into a single ``structural_valid`` boolean:

    format_valid schema_valid protocol_valid constraint_valid source_fidelity
    no_change_valid repetition_valid memorization_valid behavioral_valid

``behavioral_valid`` is always ``None`` here: prose usefulness is a blinded-reviewer
judgement (Phase G), not a machine gate. ``format_valid`` is the legacy parse-only signal
kept for continuity with the Dispatch-20 evaluator so regressions are comparable.

A record is described by ``spec``:

    spec = {
        "output_contract": {...},          # see schema_validation / scope / completion
        "source": "<source passage or ''>",
        "gold": "<gold output>",
        "validation_expectations": {...},  # see constraints / preservation
        "train_targets": [ ...other golds... ],
    }
"""
from linewright.evaluation import GateResult
from linewright.evaluation import (
    schema_validation, preservation, repetition, overlap, constraints,
    scope as scope_mod, completion as completion_mod,
)


def _format_valid(output, contract):
    """The legacy parse-only signal (what the Dispatch-20 gate measured)."""
    kind = contract.get("type", "prose")
    if kind == "prose":
        return bool(output and output.strip())
    import json
    import yaml
    try:
        if kind == "json":
            json.loads((output or "").strip()); return True
        return isinstance(yaml.safe_load((output or "").strip()), (dict, list))
    except Exception:
        return False


def evaluate_response(output, spec, hit_token_cap=False):
    """Return ``{gate_name: GateResult|value}`` for one response.

    ``protocol_valid`` and ``source_fidelity`` are composed from the underlying checks:
    protocol = schema (no stray content / correct wrapper) AND completion; source_fidelity
    = no_change preservation when applicable, else the scope omitted-change check.
    """
    contract = spec.get("output_contract", {})
    source = spec.get("source", "") or ""
    gold = spec.get("gold", "") or ""
    exps = spec.get("validation_expectations", {}) or {}
    exps_pres = dict(exps)
    exps_pres.setdefault("expects_no_change", bool(contract.get("expects_no_change")))
    exps_pres.setdefault("exact_source_preservation_required",
                         bool(contract.get("exact_source_preservation_required")))

    schema = schema_validation.validate_structured(output, contract)
    rep = repetition.analyze_repetition(output)
    mem = overlap.analyze_overlap(output, gold, spec.get("train_targets"))
    con = constraints.validate_constraints(output, exps)
    scp = scope_mod.validate_scope(output, source, contract)
    comp = completion_mod.validate_completion(output, contract, hit_token_cap=hit_token_cap)
    nochange = preservation.validate_preservation(output, source, exps_pres)

    # protocol_valid: structured wrapper / stray-content / completion discipline
    proto_labels = []
    for gr in (schema, comp):
        proto_labels += [l for l in gr.failure_labels
                         if l in ("prose_outside_structure", "continued_after_task_complete",
                                  "markdown_fence_violation", "truncated_structure",
                                  "no_change_wrapper_missing", "wrong_changed_flag")]
    if nochange.valid is False:
        proto_labels += [l for l in nochange.failure_labels
                         if l in ("no_change_wrapper_missing", "wrong_changed_flag")]
    protocol = GateResult("protocol_valid",
                          valid=(len(proto_labels) == 0),
                          failure_labels=sorted(set(proto_labels)))

    # source_fidelity: preservation when no-change, else scope's omitted/expansion checks
    if nochange.valid is not None:
        source_fidelity = GateResult("source_fidelity", valid=nochange.valid,
                                     failure_labels=nochange.failure_labels,
                                     evidence=nochange.evidence)
    else:
        sf_labels = [l for l in scp.failure_labels
                     if l in ("omitted_required_change", "excessive_expansion", "runaway_length")]
        source_fidelity = GateResult("source_fidelity",
                                     valid=(None if not source else len(sf_labels) == 0),
                                     failure_labels=sf_labels)

    return {
        "format_valid": _format_valid(output, contract),
        "schema_valid": schema,
        "protocol_valid": protocol,
        "constraint_valid": con,
        "source_fidelity": source_fidelity,
        "no_change_valid": nochange,
        "repetition_valid": rep,
        "memorization_valid": mem,
        "scope_valid": scp,
        "completion_valid": comp,
        "behavioral_valid": None,   # reviewer-assigned (Phase G); never machine-set
    }


def gate_summary(gate_map):
    """Collapse a gate map to ``{name: bool|None}`` and a ``mechanical_pass`` verdict.

    ``mechanical_pass`` is True only if no machine-decidable gate is False. ``None``
    (not-applicable / reviewer-assisted) never counts as a pass or a fail.
    """
    flat = {}
    for k, v in gate_map.items():
        flat[k] = v.valid if isinstance(v, GateResult) else v
    decidable = [v for k, v in flat.items()
                 if isinstance(v, bool) and k not in ("format_valid",)]
    mechanical_pass = all(decidable) if decidable else False
    return {"gates": flat, "mechanical_pass": mechanical_pass}
