"""Dispatch 28 (D8/D11) — aggregate the blind soft reviewers by arm (lock, unblind, per-arm means).
Calibration controls excluded from arm means. LM sub-agents only; human review waived (recorded
honestly). Writes soft-review-summary.json."""
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _REPO)
from linewright.evaluation.battery import blind

RUN = os.path.join(_REPO, "benchmarks", "runs", "linewright-prompt-effect-v1")
REVIEW_ROOT = os.path.join(RUN, "review")
ANON = os.path.join(REVIEW_ROOT, "review", "anonymous")
PRIVATE = os.path.join(RUN, "private-unblinding")
DIMS = ["prose_quality", "voice_preservation", "scope_control", "over_editing", "rigidity", "author_usefulness"]
ARMS = ["P0-Realistic", "P1-Contract", "P3-Ideal"]


def mean(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return round(sum(xs) / len(xs), 3) if xs else None


def main():
    a = json.load(open(os.path.join(ANON, "scores-reviewer-A.json"), encoding="utf-8"))["scores"]
    b = json.load(open(os.path.join(ANON, "scores-reviewer-B.json"), encoding="utf-8"))["scores"]
    by = {"A": {s["unit_id"]: s for s in a}, "B": {s["unit_id"]: s for s in b}}
    ids = sorted(set(by["A"]) | set(by["B"]))
    blind.finalize_scores(REVIEW_ROOT, [{"unit_id": u, "A": by["A"].get(u), "B": by["B"].get(u)} for u in ids])
    key = blind.unblind(REVIEW_ROOT, PRIVATE, ids)["units"]

    arm_scores = {arm: {d: [] for d in DIMS} for arm in ARMS}
    fatal = {arm: 0 for arm in ARMS}
    for u in ids:
        k = key.get(u, {})
        if k.get("calibration"):
            continue
        arm = k["arm"]
        for rv in ("A", "B"):
            s = by[rv].get(u)
            if not s:
                continue
            for d in DIMS:
                arm_scores[arm][d].append(s.get(d))
            if s.get("fatal_failure"):
                fatal[arm] += 1
    per_arm = {arm: {**{d: mean(v[d]) for d in DIMS}, "fatal": fatal[arm]} for arm, v in arm_scores.items()}

    broken = [u for u, v in key.items() if v.get("calibration")
              and any(w in str(v.get("expected", "")).lower() for w in ("broken", "fail", "reject"))]
    calib = {rv: {"broken_caught": sum(1 for u in broken if (by[rv].get(u) or {}).get("fatal_failure")),
                  "broken_total": len(broken)} for rv in ("A", "B")}

    summary = {
        "dispatch": 28, "reviewers": {"type": "two blind LM sub-agents",
            "human_review_submitted": False, "waived_for_pilot": True,
            "evidence_status": "model_review_only", "independently_human_confirmed": False},
        "per_arm_means": per_arm,
        "calibration_controls_excluded_from_arm_means": True,
        "reviewer_calibration": calib,
        "reads": {
            "prose_quality_by_arm": {arm: per_arm[arm]["prose_quality"] for arm in ARMS},
            "rigidity_by_arm": {arm: per_arm[arm]["rigidity"] for arm in ARMS},
            "over_editing_by_arm": {arm: per_arm[arm]["over_editing"] for arm in ARMS},
            "scope_control_by_arm": {arm: per_arm[arm]["scope_control"] for arm in ARMS},
        },
        "scores_locked_before_unblinding": True,
    }
    with open(os.path.join(RUN, "soft-review-summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"per_arm": per_arm, "calibration": calib}, indent=1))


if __name__ == "__main__":
    main()
