"""Build identity-separated blind review packets for the three-model comparison (Dispatch 26,
Deliverable 5).

Absolute-scoring units for core-prose (fast A+B) + packet-family scene/revision/continuation
outputs across all three roles, plus hidden grader-calibration items — all indistinguishable
and identity-free. Anonymous unit ids encode NO role; order is a deterministic content-hash
shuffle. The identity key lives in a SEPARATE private-unblinding root that scoring never reads
(blind.build_review_bundle enforces the separation). Genuinely-blind reviewers (sub-agents) see
only review/anonymous; external humans (Gary, ChatGPT) are recorded as pending.
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

RUN = os.path.join(_REPO, "benchmarks", "runs", "lwdb-stronger-base-v1")
NORM = os.path.join(RUN, "normalized-results")
REVIEW_ROOT = os.path.join(RUN, "review")
PRIVATE_ROOT = os.path.join(RUN, "private-unblinding")

REVIEW_DIMS = ["instruction_compliance", "scope_control", "voice_preservation", "scene_coherence",
               "pacing", "prose_quality", "canon_fidelity", "usefulness_to_author", "slop_or_repetition"]

# prose items eligible for blind review (fast core-prose A+B + all packet prose)
FAST_CORE_PREFIXES = ("lwdb-a-", "lwdb-b-")


def _anon_id(job_id):
    return "unit-" + hashlib.sha256(job_id.encode("utf-8")).hexdigest()[:16]


def main():
    results = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(NORM, "*.json")))]
    units, key = [], {}
    for r in results:
        iid = r["benchmark_item_id"]
        is_pf = iid.startswith("pf-")
        is_core = iid.startswith(FAST_CORE_PREFIXES)
        if not (is_pf or is_core):
            continue  # only prose review units
        job_id = r["job_id"]
        uid = _anon_id(job_id)
        units.append({"unit_id": uid, "kind": "candidate_output",
                      "text": r.get("output_text", ""),
                      "task_context": ("packet:" + iid.split("-", 1)[1]) if is_pf else "core-prose",
                      "review_form": {d: None for d in REVIEW_DIMS}})
        key[uid] = {"job_id": job_id, "item_id": iid, "model_role": r["model_role"]}

    # hidden calibration items, shaped like review units, indistinguishable
    cal_path = os.path.join(_REPO, "benchmarks", "calibration", "grader-calibration-set-v1.jsonl")
    for cal in load_calibration_set(cal_path):
        cid = cal["calibration_id"]
        uid = "unit-" + hashlib.sha256(f"cal::{cid}".encode()).hexdigest()[:16]
        units.append({"unit_id": uid, "kind": "candidate_output",
                      "text": cal.get("candidate_output", ""), "task_context": "core-prose",
                      "review_form": {d: None for d in REVIEW_DIMS}})
        key[uid] = {"calibration": True, "expected": cal.get("known_expected_result"), "cal_id": cid}

    # deterministic content-hash shuffle (no RNG): order by unit_id hash
    units.sort(key=lambda u: u["unit_id"])

    absolute_key = {"units": key, "dimensions": REVIEW_DIMS}
    pairwise_key = {"note": "absolute scoring locks before any pairwise preference"}
    info = blind.build_review_bundle(units, absolute_key, pairwise_key, REVIEW_ROOT, PRIVATE_ROOT)
    n_cand = sum(1 for u in units if not key[u["unit_id"]].get("calibration"))
    n_cal = len(units) - n_cand
    # identity-leak scan: no role/model token in any reviewer-facing unit id (use non-hex tokens
    # only — "4b" is a valid hex substring of a sha and would false-positive on pure-hash ids).
    role_tokens = ("ministral", "qwen", "target_base", "candidate", "bonsai")
    leaks = [u["unit_id"] for u in units
             if any(t in u["unit_id"].lower() for t in role_tokens)]
    print(json.dumps({"units": info["units"], "candidate_units": n_cand, "calibration_units": n_cal,
                      "anonymous_dir": os.path.relpath(info["anonymous_dir"], _REPO),
                      "private_dir": os.path.relpath(info["private_dir"], _REPO),
                      "identity_leaks": len(leaks)}, indent=1))


if __name__ == "__main__":
    main()
