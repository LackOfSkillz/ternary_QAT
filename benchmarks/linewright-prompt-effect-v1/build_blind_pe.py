"""Dispatch 28 (D8) — build an arm-hidden blind soft-review bundle. Focuses on the ideal-subset
tasks across P0-Realistic / P1-Contract / P3-Ideal to test whether higher mechanical compliance
comes with prose rigidity / over-editing (the H7 anti-result on soft metrics the machine can't
judge). Arm identity hidden; private key separate; calibration controls seeded.
"""
import glob
import hashlib
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _REPO)
from linewright.evaluation.battery import blind
from linewright.evaluation.calibration.records import load_calibration_set

RUN = os.path.join(_REPO, "benchmarks", "runs", "linewright-prompt-effect-v1")
NORM = os.path.join(RUN, "normalized-results")
REVIEW_ROOT = os.path.join(RUN, "review")
PRIVATE_ROOT = os.path.join(RUN, "private-unblinding")
IDEAL = ["fr-01", "fr-05", "fr-07", "fr-09", "pt-01", "pt-05", "cn-01", "vp-02", "nc-04", "sd-01"]
ARMS = ["P0-Realistic", "P1-Contract", "P3-Ideal"]
DIMS = ["prose_quality", "voice_preservation", "scope_control", "over_editing", "rigidity",
        "author_usefulness"]


def _anon(s):
    return "unit-" + hashlib.sha256(s.encode()).hexdigest()[:16]


def main():
    outputs = {}
    for p in glob.glob(os.path.join(NORM, "*.json")):
        r = json.load(open(p, encoding="utf-8"))
        outputs[(r["task_id"], r["arm"])] = r.get("output_text", "")
    units, key = [], {}
    for tid in IDEAL:
        for arm in ARMS:
            text = outputs.get((tid, arm), "")
            if not text.strip():
                continue
            uid = _anon(f"{tid}::{arm}")
            units.append({"unit_id": uid, "task_context": tid, "text": text,
                          "review_form": {d: None for d in DIMS}})
            key[uid] = {"task_id": tid, "arm": arm}
    cal_path = os.path.join(_REPO, "benchmarks", "calibration", "grader-calibration-set-v1.jsonl")
    for cal in load_calibration_set(cal_path)[:4]:
        uid = _anon(f"cal::{cal['calibration_id']}")
        units.append({"unit_id": uid, "task_context": "review", "text": cal.get("candidate_output", ""),
                      "review_form": {d: None for d in DIMS}})
        key[uid] = {"calibration": True, "expected": cal.get("known_expected_result")}
    units.sort(key=lambda u: u["unit_id"])
    blind.build_review_bundle(units, {"units": key, "dimensions": DIMS}, {}, REVIEW_ROOT, PRIVATE_ROOT)
    leaks = [u["unit_id"] for u in units if any(t in u["unit_id"].lower()
             for t in ("p0", "p1", "p3", "realistic", "maximal", "contract", "ideal", "arm"))]
    packet = [{"unit_id": u["unit_id"], "task_context": u["task_context"], "text": u["text"]} for u in units]
    with open(os.path.join(REVIEW_ROOT, "review", "anonymous", "reviewer-packet.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(packet, fh, ensure_ascii=False, indent=1)
    n_cal = sum(1 for u in units if key[u["unit_id"]].get("calibration"))
    print(json.dumps({"units": len(units), "candidate": len(units) - n_cal, "calibration": n_cal,
                      "arms": ARMS, "tasks": len(IDEAL), "identity_leaks": len(leaks)}, indent=1))


if __name__ == "__main__":
    main()
