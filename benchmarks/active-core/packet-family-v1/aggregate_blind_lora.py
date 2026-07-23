"""Dispatch 27 Phase B (D11/D12) — aggregate the blind base-vs-LoRA reviewers, lock, unblind,
apply the frozen advancement floor. LM sub-agents only (human review waived this round — recorded
honestly, NOT described as human-confirmed). Writes lora-blind-review-summary.json.
"""
import glob
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.battery import blind

RUN = os.path.join(_REPO, "benchmarks", "runs", "qwen3-lora-checkpoint-curve-v1")
REVIEW_ROOT = os.path.join(RUN, "review")
ANON = os.path.join(REVIEW_ROOT, "review", "anonymous")
PRIVATE = os.path.join(RUN, "private-unblinding")
FLOOR = {"min_prose_gain": 0.25, "min_voice_gain": 0.25, "max_instruction_drop": 0.15, "max_new_fatal": 0}
NUM = ["prose_quality", "instruction_compliance", "voice_preservation", "scene_coherence", "pacing",
       "sentence_naturalness", "scope_control", "canon_fidelity", "protected_text_preservation",
       "author_usefulness"]


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

    roles = {}
    fatal = {}
    for u in ids:
        k = key.get(u, {})
        if k.get("calibration"):
            continue
        role = k["role"]
        r = roles.setdefault(role, {d: [] for d in NUM})
        for rv in ("A", "B"):
            s = by[rv].get(u)
            if not s:
                continue
            for d in NUM:
                r[d].append(s.get(d))
            if s.get("fatal_failure"):
                fatal[role] = fatal.get(role, 0) + 1
    per_role_means = {role: {d: mean(v[d]) for d in NUM} for role, v in roles.items()}
    for role in per_role_means:
        per_role_means[role]["fatal"] = fatal.get(role, 0)

    base = per_role_means.get("qwen3_8b_base", {})
    lora_role = next((r for r in per_role_means if r != "qwen3_8b_base"), None)
    lora = per_role_means.get(lora_role, {})
    prose_gain = round((lora.get("prose_quality") or 0) - (base.get("prose_quality") or 0), 3)
    voice_gain = round((lora.get("voice_preservation") or 0) - (base.get("voice_preservation") or 0), 3)
    instr_drop = round((base.get("instruction_compliance") or 0) - (lora.get("instruction_compliance") or 0), 3)
    new_fatal = max(0, fatal.get(lora_role, 0) - fatal.get("qwen3_8b_base", 0))

    floor_pass = (prose_gain >= FLOOR["min_prose_gain"] and voice_gain >= FLOOR["min_voice_gain"]
                  and instr_drop <= FLOOR["max_instruction_drop"] and new_fatal <= FLOOR["max_new_fatal"])

    # calibration + agreement
    broken = [u for u, v in key.items() if v.get("calibration")
              and any(w in str(v.get("expected", "")).lower() for w in ("broken", "fail", "reject"))]
    calib = {rv: {"broken_caught": sum(1 for u in broken if (by[rv].get(u) or {}).get("fatal_failure")),
                  "broken_total": len(broken)} for rv in ("A", "B")}
    cand = [u for u in ids if not key.get(u, {}).get("calibration")]
    diffs = [abs((by["A"].get(u) or {}).get("prose_quality", 0) - (by["B"].get(u) or {}).get("prose_quality", 0))
             for u in cand if by["A"].get(u) and by["B"].get(u)]

    summary = {
        "dispatch": 27, "phase": "B",
        "reviewers": {"type": "two independent blind LM graders (sub-agents)",
                      "human_review_submitted": False, "human_gate_waived_this_round": True,
                      "evidence_status": "model_review_only", "independently_human_confirmed": False},
        "roles_compared": ["qwen3_8b_base", lora_role],
        "per_role_means": per_role_means,
        "prose_gain": prose_gain, "voice_gain": voice_gain, "instruction_drop": instr_drop,
        "new_fatal_best_vs_base": new_fatal,
        "advancement_floor": FLOOR, "effect_floor_passed": floor_pass,
        "reviewer_calibration": calib,
        "inter_reviewer_agreement_mean_abs_prose_diff": (round(sum(diffs) / len(diffs), 3) if diffs else None),
        "scores_locked_before_unblinding": True,
    }
    with open(os.path.join(RUN, "lora-blind-review-summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"roles": summary["roles_compared"],
                      "base_prose": base.get("prose_quality"), "lora_prose": lora.get("prose_quality"),
                      "prose_gain": prose_gain, "voice_gain": voice_gain, "instruction_drop": instr_drop,
                      "new_fatal": new_fatal, "effect_floor_passed": floor_pass,
                      "calibration": calib}, indent=1))


if __name__ == "__main__":
    main()
