"""Dispatch 27 Phase A — build a PRECISION-blind bundle (BF16 vs Q4) for blind prose review.

30 units (15 tasks x 2 precisions), precision hidden, anonymous ids encode no precision, plus
hidden calibration controls. Identity key (unit -> precision) lives in a separate private-
unblinding root scoring never reads. Reviewers (LM sub-agents = supporting; Gary + independent
human = deciding) score prose blind; scores lock before unblinding.
"""
import glob
import hashlib
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.battery import blind
from linewright.evaluation.calibration.records import load_calibration_set

RUN = os.path.join(_REPO, "benchmarks", "runs", "qwen-prose-confirmation-v1")
Q4 = os.path.join(RUN, "normalized-results", "q4")
D26 = os.path.join(_REPO, "benchmarks", "runs", "lwdb-stronger-base-v1", "normalized-results")
REVIEW_ROOT = os.path.join(RUN, "review")
PRIVATE_ROOT = os.path.join(RUN, "private-unblinding")
DIMS = ["prose_quality", "voice_preservation", "instruction_compliance", "scene_coherence",
        "pacing", "sentence_naturalness", "scope_control", "canon_fidelity", "repetition_or_slop"]
CONF = ["lwdb-a-length-short", "lwdb-a-length-long", "lwdb-a-quiet-scene", "lwdb-c-restraint-fix",
        "lwdb-b-voice-terse", "lwdb-b-voice-lyrical", "lwdb-g-turn-single",
        "pf-scene_drafting-bare", "pf-scene_drafting-realistic", "pf-scene_drafting-long",
        "pf-focused_revision-compact", "pf-focused_revision-realistic",
        "pf-focused_revision-long_salience_repaired",
        "pf-canon_sensitive_continuation-realistic", "pf-canon_sensitive_continuation-long"]


def _anon(s):
    return "unit-" + hashlib.sha256(s.encode()).hexdigest()[:16]


def main():
    units, key = [], {}
    q4 = {json.load(open(p, encoding="utf-8"))["benchmark_item_id"]: json.load(open(p, encoding="utf-8"))
          for p in glob.glob(os.path.join(Q4, "*.json"))}
    bf16 = {}
    for p in glob.glob(os.path.join(D26, "*qwen3_8b_non_thinking.json")):
        r = json.load(open(p, encoding="utf-8"))
        if r["benchmark_item_id"] in CONF:
            bf16[r["benchmark_item_id"]] = r
    for iid in CONF:
        for prec, rec in (("bf16", bf16[iid]), ("q4", q4[iid])):
            uid = _anon(f"{iid}::{prec}")
            units.append({"unit_id": uid, "kind": "candidate_output", "task_context": iid,
                          "text": rec.get("output_text", ""), "review_form": {d: None for d in DIMS}})
            key[uid] = {"item_id": iid, "precision": prec}
    cal_path = os.path.join(_REPO, "benchmarks", "calibration", "grader-calibration-set-v1.jsonl")
    for cal in load_calibration_set(cal_path)[:6]:
        uid = _anon(f"cal::{cal['calibration_id']}")
        units.append({"unit_id": uid, "kind": "candidate_output", "task_context": "core-prose",
                      "text": cal.get("candidate_output", ""), "review_form": {d: None for d in DIMS}})
        key[uid] = {"calibration": True, "expected": cal.get("known_expected_result")}
    units.sort(key=lambda u: u["unit_id"])
    blind.build_review_bundle(units, {"units": key, "dimensions": DIMS}, {}, REVIEW_ROOT, PRIVATE_ROOT)
    leaks = [u["unit_id"] for u in units if any(t in u["unit_id"].lower() for t in ("bf16", "q4", "gguf"))]
    # focused reviewer packet (identity-free)
    packet = [{"unit_id": u["unit_id"], "task_context": u["task_context"], "text": u["text"]} for u in units]
    with open(os.path.join(REVIEW_ROOT, "review", "anonymous", "reviewer-packet.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(packet, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"units": len(units), "precision_units": 30, "calibration": len(units) - 30,
                      "identity_leaks": len(leaks)}, indent=1))


if __name__ == "__main__":
    main()
