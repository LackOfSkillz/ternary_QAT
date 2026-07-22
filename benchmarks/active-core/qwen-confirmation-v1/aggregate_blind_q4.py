"""Dispatch 27 Phase A — aggregate blind precision reviewers, lock, unblind, compare BF16 vs Q4.

Locks the two reviewers' scores before unblinding, unblinds via the private key, maps each unit
to its precision, computes per-precision blind means + BF16->Q4 deltas, and applies the frozen
qwen-q4-confirmation-floor-v0. LM sub-agents are SUPPORTING evidence; Gary + an independent human
remain the deciding gate. Writes blind-precision-summary.json.
"""
import json
import os
import sys

import yaml

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.battery import blind

RUN = os.path.join(_REPO, "benchmarks", "runs", "qwen-prose-confirmation-v1")
REVIEW_ROOT = os.path.join(RUN, "review")
ANON = os.path.join(REVIEW_ROOT, "review", "anonymous")
PRIVATE = os.path.join(RUN, "private-unblinding")
FLOOR = os.path.join(_REPO, "benchmarks", "thresholds", "qwen-q4-confirmation-floor-v0.yaml")
DIMS = ["prose_quality", "voice_preservation", "instruction_compliance", "sentence_naturalness"]


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def main():
    a = json.load(open(os.path.join(ANON, "scores-reviewer-A.json"), encoding="utf-8"))["scores"]
    b = json.load(open(os.path.join(ANON, "scores-reviewer-B.json"), encoding="utf-8"))["scores"]
    by = {"A": {s["unit_id"]: s for s in a}, "B": {s["unit_id"]: s for s in b}}
    ids = sorted(set(by["A"]) | set(by["B"]))
    blind.finalize_scores(REVIEW_ROOT, [{"unit_id": u, "A": by["A"].get(u), "B": by["B"].get(u)} for u in ids])
    key = blind.unblind(REVIEW_ROOT, PRIVATE, ids)["units"]

    prec = {"bf16": {d: [] for d in DIMS}, "q4": {d: [] for d in DIMS}}
    fatal = {"bf16": 0, "q4": 0}
    for u in ids:
        k = key.get(u, {})
        if k.get("calibration"):
            continue
        p = k["precision"]
        for rv in ("A", "B"):
            s = by[rv].get(u)
            if not s:
                continue
            for d in DIMS:
                prec[p][d].append(s.get(d))
            if s.get("fatal_flaw"):
                fatal[p] += 1
    means = {p: {d: mean(prec[p][d]) for d in DIMS} for p in ("bf16", "q4")}
    deltas = {d: round((means["bf16"][d] or 0) - (means["q4"][d] or 0), 3) for d in DIMS}
    new_fatal = max(0, fatal["q4"] - fatal["bf16"])

    floor = yaml.safe_load(open(FLOOR, encoding="utf-8"))["q4_preservation"]
    checks = {
        "prose_drop_ok": deltas["prose_quality"] <= floor["max_mean_prose_drop_5pt"]["value"],
        "voice_drop_ok": deltas["voice_preservation"] <= floor["max_mean_voice_preservation_drop_5pt"]["value"],
        "instruction_drop_ok": deltas["instruction_compliance"] <= floor["max_instruction_compliance_drop_5pt"]["value"],
        "new_fatal_ok": new_fatal <= floor["max_new_fatal_rejections"]["value"],
    }
    # reviewer calibration on known-broken controls
    cal = {"A": [0, 0], "B": [0, 0]}
    for u in ids:
        k = key.get(u, {})
        if not k.get("calibration"):
            continue
        broken = any(w in str(k.get("expected", "")).lower() for w in ("broken", "fail", "reject"))
        for rv in ("A", "B"):
            s = by[rv].get(u)
            if s and broken:
                cal[rv][1] += 1
                if s.get("fatal_flaw") or (s.get("prose_quality") or 5) <= 2:
                    cal[rv][0] += 1
    summary = {
        "dispatch": 27, "phase": "A", "reviewers": {"lm_subagents": ["A", "B"],
            "external_humans_pending": ["Gary", "at_least_one_independent"],
            "role": "supporting_only (humans are the deciding gate)"},
        "blind_means": means, "bf16_to_q4_deltas": deltas, "q4_new_fatal_rejections": new_fatal,
        "floor_checks": checks, "q4_blind_prose_preservation_pass_LM_only": all(checks.values()),
        "reviewer_calibration": {rv: (round(c[0] / c[1], 3) if c[1] else None) for rv, c in cal.items()},
        "scores_locked_before_unblinding": True,
    }
    with open(os.path.join(RUN, "blind-precision-summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"means": means, "deltas": deltas, "new_fatal": new_fatal, "checks": checks,
                      "lm_pass": summary["q4_blind_prose_preservation_pass_LM_only"],
                      "calibration": summary["reviewer_calibration"]}, indent=1))


if __name__ == "__main__":
    main()
