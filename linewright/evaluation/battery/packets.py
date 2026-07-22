"""Blind reviewer packets for the fast battery (Dispatch 24, Workstream K).

Absolute scoring FIRST: each output is a standalone, identity-free review unit; calibration
outputs are mixed in indistinguishably. Only after absolute scores lock do close/important
items get a pairwise (base vs candidate) packet. No model role/name/checkpoint/host/method/
timing/loss ever reaches a reviewer; unit order is a deterministic content-derived shuffle.
"""
import hashlib
import json

from linewright.evaluation.reviewer_packet import (build_packet, anonymization_ok,
                                                    REVIEW_FORM, FATAL_FLAWS)
from linewright.evaluation.slop.reviewer_checklist import CHECKLIST

# Precise identity tokens that never legitimately appear in benchmark CONTENT (the review
# form / checklist boilerplate is excluded from the scan, and 'removable_without_loss' /
# 'step-by-step' are content, not identity — so bare 'loss'/'step-' are not used).
_FORBIDDEN = ["target_base", "new_candidate", "gx10", "checkpoint", "model_role",
              "model_identity", "lora", "ternary-qat", "training loss", "untouched base",
              "tuned candidate"]
_CONTENT_FIELDS = ("unit_id", "task_instruction", "source", "context", "canon",
                   "hard_constraints", "expected_output_type")


def _uid(seed, salt):
    return "u" + hashlib.sha256(f"{seed}:{salt}".encode("utf-8")).hexdigest()[:16]


def _review_form():
    f = dict(REVIEW_FORM)
    f["slop_checklist"] = [{"id": c["id"], "question": c["question"], "positive": None,
                            "evidence_spans": [], "severity": None, "confidence": None}
                           for c in CHECKLIST]
    return f


def _unit(seed, salt, item, output_text):
    ic = item["input"]
    return {"unit_id": _uid(seed, salt),
            "task_instruction": ic["task_instruction"], "source": ic.get("source", ""),
            "context": ic.get("context", ""), "canon": ic.get("canon", []),
            "hard_constraints": ic.get("hard_constraints", []),
            "expected_output_type": item["output_contract"].get("schema_id"),
            "output_text": output_text,
            "review_form": _review_form(),
            "fatal_flaw_catalog": FATAL_FLAWS}


def build_absolute_packets(normalized_results, items_by_id, calibration_records=None, seed="lwdb-fast-v1"):
    """Return (units, key). ``units`` is the shuffled, identity-free absolute-scoring set;
    ``key`` maps each unit_id back to identity/calibration for post-scoring un-blinding."""
    units, key = [], {}
    for r in normalized_results:
        iid, role = r["benchmark_item_id"], r["model_role"]
        salt = f"real:{r.get('result_id') or iid + ':' + role}"
        u = _unit(seed, salt, items_by_id[iid], r.get("output_text", ""))
        units.append(u)
        key[u["unit_id"]] = {"kind": "candidate", "item_id": iid, "model_role": role}
    for i, cr in enumerate(calibration_records or []):
        # calibration outputs are mixed in indistinguishably (same review-unit shape)
        pseudo_item = {"input": {"task_instruction": cr["source_item_shape"].get(
            "instruction", "Evaluate this response against its task."),
            "source": cr["source_item_shape"].get("source", "")},
            "output_contract": {"schema_id": cr["source_item_shape"].get(
                "output_contract", {}).get("schema_id", "prose-v1")}}
        u = _unit(seed, f"cal:{cr['calibration_id']}:{i}", pseudo_item, cr["candidate_output"])
        units.append(u)
        key[u["unit_id"]] = {"kind": "calibration", "calibration_id": cr["calibration_id"],
                             "known_expected_result": cr["known_expected_result"]}
    # deterministic content-derived shuffle (order cannot leak identity)
    units.sort(key=lambda u: hashlib.sha256((seed + u["output_text"]).encode("utf-8")).hexdigest())
    return units, key


def build_pairwise_packets(normalized_results, items_by_id, seed="lwdb-fast-v1-pw"):
    """Per item, a blind base-vs-candidate pairwise packet (built AFTER absolute locks)."""
    by_item = {}
    for r in normalized_results:
        by_item.setdefault(r["benchmark_item_id"], []).append(r)
    packets, keys = [], {}
    for iid, results in sorted(by_item.items()):
        if len(results) < 2:
            continue
        item = items_by_id[iid]
        record = {"record_id": iid, "task_family": item["task_family"], "input": item["input"],
                  "output_contract": item["output_contract"]}
        cands = [{"identity": r["model_role"], "output": r.get("output_text", "")} for r in results]
        packet, key = build_packet(record, cands, seed=seed)
        packets.append(packet)
        keys[iid] = key
    return packets, keys


def identity_leak_check(units):
    """Return the list of units whose body contains any identity-leaking token (should be []).
    The output_text itself is excluded (a story may legitimately contain a word like 'host')."""
    leaks = []
    for u in units:
        scan = {k: u.get(k) for k in _CONTENT_FIELDS}
        blob = json.dumps(scan, ensure_ascii=False).lower()
        hit = [t for t in _FORBIDDEN if t in blob]
        if hit:
            leaks.append({"unit_id": u["unit_id"], "tokens": hit})
    return leaks
