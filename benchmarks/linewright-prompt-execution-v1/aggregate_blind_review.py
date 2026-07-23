"""Dispatch 28B — lock, unblind, and aggregate the two blind reviewers by arm. Calibration controls
excluded from arm means. LM sub-agents only; human review waived (recorded honestly). Writes
soft-review-summary.json. Enforces score-lock-before-unblind via the blind battery."""
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _REPO)
from linewright.evaluation.battery import blind

RUN = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(__file__), "..", "runs", "linewright-prompt-execution-v1")
RUN = os.path.abspath(RUN)
REVIEW_ROOT = os.path.join(RUN, "review")
ANON = os.path.join(REVIEW_ROOT, "anonymous")
PRIVATE = os.path.join(RUN, "private-unblinding")
DIMS = ["prose_quality", "voice_preservation", "naturalness", "scene_coherence", "pacing",
        "scope_control", "author_usefulness", "rigidity", "over_editing", "repetition_or_slop"]
ARMS = ["P0-Realistic", "P0-Maximal", "P1-Contract", "P3-Ideal"]


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
    per_arm = {arm: {**{d: mean(v[d]) for d in DIMS}, "fatal": fatal[arm],
                     "units": len([u for u in ids if key.get(u, {}).get("arm") == arm])}
               for arm, v in arm_scores.items()}

    # calibration: broken controls should be caught (fatal true)
    broken = [u for u, v in key.items() if v.get("calibration")
              and any(w in str(v.get("expected", "")).lower() for w in ("broken", "fail", "reject", "bad", "invalid"))]
    good = [u for u, v in key.items() if v.get("calibration") and u not in broken]
    calib = {rv: {"broken_caught": sum(1 for u in broken if (by[rv].get(u) or {}).get("fatal_failure")),
                  "broken_total": len(broken),
                  "good_flagged_fatal": sum(1 for u in good if (by[rv].get(u) or {}).get("fatal_failure")),
                  "good_total": len(good)} for rv in ("A", "B")}

    # reviewer agreement: mean abs diff on prose_quality across shared candidate units
    diffs = []
    for u in ids:
        if key.get(u, {}).get("calibration"):
            continue
        sa, sb = by["A"].get(u), by["B"].get(u)
        if sa and sb and isinstance(sa.get("prose_quality"), (int, float)) and isinstance(sb.get("prose_quality"), (int, float)):
            diffs.append(abs(sa["prose_quality"] - sb["prose_quality"]))
    agreement = {"prose_quality_mean_abs_diff": round(sum(diffs) / len(diffs), 3) if diffs else None,
                 "n": len(diffs)}

    # soft anti-results: P1 vs P0-Maximal, P3 vs P1 (prose/voice/rigidity/over_editing deltas)
    def d(a1, a2, dim):
        x, y = per_arm[a1].get(dim), per_arm[a2].get(dim)
        return round(x - y, 3) if (x is not None and y is not None) else None
    soft_anti = {
        "p1_vs_p0max": {dim: d("P1-Contract", "P0-Maximal", dim) for dim in
                        ("prose_quality", "voice_preservation", "rigidity", "over_editing")},
        "p3ideal_vs_p1": {dim: d("P3-Ideal", "P1-Contract", dim) for dim in
                          ("prose_quality", "voice_preservation", "rigidity", "over_editing")},
    }

    summary = {
        "dispatch": "28B", "reviewers": {"type": "two blind LM sub-agents",
            "human_review_submitted": False, "waived_for_pilot": True,
            "evidence_status": "model_review_only", "independently_human_confirmed": False},
        "per_arm_means": per_arm, "reviewer_calibration": calib, "reviewer_agreement": agreement,
        "soft_anti_results": soft_anti,
        "calibration_controls_excluded_from_arm_means": True, "scores_locked_before_unblinding": True,
    }
    json.dump(summary, open(os.path.join(RUN, "soft-review-summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"per_arm": {a: {"prose": per_arm[a]["prose_quality"], "voice": per_arm[a]["voice_preservation"],
                                      "scope": per_arm[a]["scope_control"], "over_edit": per_arm[a]["over_editing"],
                                      "rigidity": per_arm[a]["rigidity"], "useful": per_arm[a]["author_usefulness"],
                                      "fatal": per_arm[a]["fatal"], "units": per_arm[a]["units"]} for a in ARMS},
                      "calibration": calib, "agreement": agreement}, indent=1))


if __name__ == "__main__":
    main()
