"""Blind reviewer-packet generator (Dispatch 21, Phase G).

Produces packets that let independent reviewers compare candidate outputs without any
knowledge of which checkpoint produced which candidate. The packet is deliberately
identity-free: it never contains "base", "lora", "qat", checkpoint step, loss, structural
score, or model identity. Candidate order is a deterministic, content-derived shuffle so
the ordering itself cannot leak identity, and re-runs are reproducible (no RNG — the
scripts environment forbids ``random``/``Date.now``).

A packet exposes the task, the source material, the output contract, the anonymized
candidates, and a blank review form. Golds and mechanical gate results are kept OUT of the
review body; they belong in a separate post-scoring verification section (``build_key``),
so a reviewer locks their preference before seeing them.
"""
import hashlib

# 1-5 reviewer score dimensions + preference + fatal flag
REVIEW_FORM = {
    "instruction_compliance": None, "canon_fidelity": None, "constraint_fidelity": None,
    "scope_control": None, "voice_preservation": None, "prose_quality": None,
    "repetition_control": None, "schema_or_protocol_compliance": None,
    "usefulness_to_author": None,
    "overall_preference": None,           # a candidate label, or "none"
    "fatal_flaw": None,                    # bool
    "fatal_flaw_reason": None,
}

FATAL_FLAWS = [
    "invented_canon", "contradiction", "ignored_hard_constraint", "severe_repetition",
    "incorrect_no_change_behavior", "unusable_schema", "major_voice_destruction",
    "copied_training_target", "truncated_output", "unrelated_response",
]

# strings that must NEVER appear in a packet body (identity leakage)
FORBIDDEN_IN_PACKET = ["base", "lora", "qat", "ternary", "checkpoint", "step-", "loss",
                       "preferred", "rejected", "gold", "teacher", "opus", "claude",
                       "format_valid", "mechanical"]

_LABELS = ["Candidate A", "Candidate B", "Candidate C", "Candidate D",
           "Candidate E", "Candidate F"]


def _order_key(seed, text):
    return hashlib.sha256(f"{seed}::{text}".encode("utf-8")).hexdigest()


def build_packet(record, candidates, seed="dispatch-21"):
    """Return ``(packet, key)``.

    ``candidates`` is a list of ``{"identity": <hidden id>, "output": <text>,
    "gate_summary": {...}}``. The packet is identity-free; ``key`` maps each anonymized
    label back to identity + gate summary for post-scoring un-blinding.
    """
    ordered = sorted(candidates, key=lambda c: _order_key(seed, c["output"]))
    if len(ordered) > len(_LABELS):
        raise ValueError("too many candidates for the label set")
    labelled = list(zip(_LABELS, ordered))

    ic = record.get("input", {})
    oc = record.get("output_contract", {})
    packet = {
        "record_id": record["record_id"],
        "task_family": record["task_family"],
        "task_instruction": ic.get("task_instruction", ""),
        "source_material": ic.get("source", ""),
        "context": ic.get("context", ""),
        "canon": ic.get("canon", []),
        "hard_constraints": ic.get("hard_constraints", []),
        "expected_output_contract": {
            "type": oc.get("type"), "schema_id": oc.get("schema_id"),
            "required_keys": oc.get("required_keys", []),
        },
        "candidates": [{"label": lab, "output": c["output"]} for lab, c in labelled],
        "review_form": {
            "instructions": "Score each candidate 1-5 on every dimension, choose an overall "
                            "preference, and flag any fatal flaw. Submit independently BEFORE "
                            "any discussion. Do not average away a fatal flaw.",
            "fatal_flaw_catalog": FATAL_FLAWS,
            "per_candidate": {lab: dict(REVIEW_FORM) for lab, _ in labelled},
        },
    }
    key = {
        "record_id": record["record_id"], "seed": seed,
        "unblinding": {lab: {"identity": c.get("identity"),
                             "gate_summary": c.get("gate_summary")}
                       for lab, c in labelled},
    }
    return packet, key


def anonymization_ok(packet):
    """True if no identity-leaking token appears anywhere in the packet body.

    The candidate OUTPUTS themselves are excluded from the scan (a story can legitimately
    contain the word 'loss'); only the structural/label fields are checked.
    """
    import json
    scan = dict(packet)
    scan["candidates"] = [{"label": c["label"]} for c in packet["candidates"]]
    blob = json.dumps(scan, ensure_ascii=False).lower()
    return [tok for tok in FORBIDDEN_IN_PACKET if tok in blob]
