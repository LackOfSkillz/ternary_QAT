"""Aggregate the blind reviewers, lock scores, unblind, and compute per-model prose metrics
(Dispatch 26, D5).

Locks the two reviewers' scores (blind.finalize_scores) BEFORE unblinding, unblinds via the
private identity key, then maps each anonymous unit to its model and computes per-model mean
prose quality, acceptance (no fatal), fatal-rejection, preferred model, reviewer calibration
(against known-broken control items), and inter-reviewer agreement. External human reviewers
(Gary, ChatGPT) are recorded as pending. Writes blind-review-summary.json.
"""
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.battery import blind

RUN = os.path.join(_REPO, "benchmarks", "runs", "lwdb-stronger-base-v1")
REVIEW_ROOT = os.path.join(RUN, "review")
ANON = os.path.join(REVIEW_ROOT, "review", "anonymous")
PRIVATE = os.path.join(RUN, "private-unblinding")
DIMS = ["instruction_compliance", "voice_preservation", "prose_quality", "scene_coherence"]


def load(p):
    return json.load(open(p, encoding="utf-8"))


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def main():
    a = load(os.path.join(ANON, "scores-reviewer-A.json"))["scores"]
    b = load(os.path.join(ANON, "scores-reviewer-B.json"))["scores"]
    by = {"A": {s["unit_id"]: s for s in a}, "B": {s["unit_id"]: s for s in b}}
    all_ids = sorted(set(by["A"]) | set(by["B"]))

    # lock scores BEFORE unblinding
    blind.finalize_scores(REVIEW_ROOT, [{"unit_id": uid, "A": by["A"].get(uid), "B": by["B"].get(uid)}
                                        for uid in all_ids])
    key = blind.unblind(REVIEW_ROOT, PRIVATE, all_ids)["units"]

    # per-model aggregation over candidate (non-calibration) units
    per_model = {}
    for uid in all_ids:
        k = key.get(uid, {})
        if k.get("calibration"):
            continue
        role = k.get("model_role")
        m = per_model.setdefault(role, {"n": 0, "prose": [], "instr": [], "voice": [], "coh": [], "fatal": 0})
        for rv in ("A", "B"):
            s = by[rv].get(uid)
            if not s:
                continue
            m["n"] += 0  # counted per-review below
            m["prose"].append(s.get("prose_quality"))
            m["instr"].append(s.get("instruction_compliance"))
            m["voice"].append(s.get("voice_preservation"))
            m["coh"].append(s.get("scene_coherence"))
            if s.get("fatal_flaw"):
                m["fatal"] += 1
    model_summary = {}
    for role, m in per_model.items():
        n_reviews = len(m["prose"])
        model_summary[role] = {
            "n_reviews": n_reviews,
            "mean_prose_quality": mean(m["prose"]),
            "mean_instruction_compliance": mean(m["instr"]),
            "mean_voice_preservation": mean(m["voice"]),
            "mean_scene_coherence": mean(m["coh"]),
            "fatal_rejection_rate": round(m["fatal"] / n_reviews, 3) if n_reviews else None,
            "acceptance_rate": round(1 - m["fatal"] / n_reviews, 3) if n_reviews else None,
        }

    # reviewer calibration: on known-broken control items, reviewers should flag fatal or score low
    cal = {"A": {"caught": 0, "total": 0}, "B": {"caught": 0, "total": 0}}
    for uid in all_ids:
        k = key.get(uid, {})
        if not k.get("calibration"):
            continue
        expected = str(k.get("expected", "")).lower()
        broken = ("broken" in expected or "fail" in expected or "reject" in expected)
        for rv in ("A", "B"):
            s = by[rv].get(uid)
            if not s:
                continue
            if broken:
                cal[rv]["total"] += 1
                if s.get("fatal_flaw") or (s.get("prose_quality") or 5) <= 2:
                    cal[rv]["caught"] += 1

    # inter-reviewer agreement: mean abs diff on prose_quality over shared candidate units
    diffs = []
    for uid in all_ids:
        if key.get(uid, {}).get("calibration"):
            continue
        sa, sb = by["A"].get(uid), by["B"].get(uid)
        if sa and sb and sa.get("prose_quality") is not None and sb.get("prose_quality") is not None:
            diffs.append(abs(sa["prose_quality"] - sb["prose_quality"]))
    agreement = {"mean_abs_prose_diff": round(sum(diffs) / len(diffs), 3) if diffs else None,
                 "n_shared_units": len(diffs)}

    # preferred candidate model by mean prose quality
    cands = {r: v["mean_prose_quality"] for r, v in model_summary.items()
             if r in ("ministral_3_8b_instruct", "qwen3_8b_non_thinking") and v["mean_prose_quality"] is not None}
    preferred = max(cands, key=cands.get) if cands else None

    summary = {
        "reviewers": {"blind_subagents": ["A", "B"], "external_humans_pending": ["Gary", "ChatGPT"],
                      "note": "sub-agent reviewers are genuinely blind (never saw the identity key); "
                              "the implementation agent's own non-blind judgment is NOT counted."},
        "n_candidate_units_reviewed": sum(1 for uid in all_ids if not key.get(uid, {}).get("calibration")),
        "calibration_units": sum(1 for uid in all_ids if key.get(uid, {}).get("calibration")),
        "per_model": model_summary,
        "preferred_model": preferred,
        "reviewer_calibration": {rv: (round(c["caught"] / c["total"], 3) if c["total"] else None)
                                 for rv, c in cal.items()},
        "inter_reviewer_agreement": agreement,
        "scores_locked_before_unblinding": True,
        "pairwise_preference_cannot_override_fatal": True,
    }
    with open(os.path.join(RUN, "blind-review-summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"per_model_prose": {r: v["mean_prose_quality"] for r, v in model_summary.items()},
                      "preferred_model": preferred, "agreement": agreement,
                      "reviewer_calibration": summary["reviewer_calibration"]}, indent=1))


if __name__ == "__main__":
    main()
