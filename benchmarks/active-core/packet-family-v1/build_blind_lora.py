"""Dispatch 27 Phase B (D9) — build a blind base-vs-LoRA prose bundle emphasizing the PRIMARY
target (multi-constraint focused revision), plus voice / restrained scene / canon-continuation /
no-change, with hidden calibration controls.

Blindly compares Qwen3 base vs the provisional best LoRA checkpoint (chosen from the mechanical
curve BEFORE this runs). Identity (role) is hidden; the private key lives in a separate directory.
Genuinely-blind sub-agent reviewers score prose; the human gate may be waived this round (recorded
honestly, NOT described as human-confirmed).
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

RUN = os.path.join(_REPO, "benchmarks", "runs", "qwen3-lora-checkpoint-curve-v1")
NORM = os.path.join(RUN, "normalized-results")
FR = os.path.join(RUN, "fr-normalized-results")
CURVE = os.path.join(RUN, "checkpoint-curve-summary.json")
REVIEW_ROOT = os.path.join(RUN, "review")
PRIVATE_ROOT = os.path.join(RUN, "private-unblinding")
DIMS = ["prose_quality", "instruction_compliance", "voice_preservation", "scene_coherence",
        "pacing", "sentence_naturalness", "scope_control", "canon_fidelity",
        "protected_text_preservation", "author_usefulness"]

# focused revision (primary target) from the FR probe; the rest from the frozen-subset eval
FR_ITEMS = ["pf-focused_revision-compact", "pf-focused_revision-realistic",
            "pf-focused_revision-long_salience_repaired", "lwdb-c-restraint-fix"]
NORM_ITEMS = ["lwdb-b-voice-terse", "lwdb-b-voice-lyrical", "lwdb-a-length-short",
              "lwdb-a-quiet-scene" if False else "lwdb-a-length-long", "lwdb-d-canon-apply",
              "lwdb-c-restraint-clean", "pf-scene_drafting-realistic"]


def _anon(s):
    return "unit-" + hashlib.sha256(s.encode()).hexdigest()[:16]


def load_dir(base):
    out = {}
    for role_dir in glob.glob(os.path.join(base, "*")):
        role = os.path.basename(role_dir)
        out[role] = {json.load(open(p, encoding="utf-8"))["benchmark_item_id"]:
                     json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(role_dir, "*.json"))}
    return out


def main():
    import yaml
    pb = os.path.join(_REPO, "training", "reports", "dispatch-27-provisional-best-checkpoint.yaml")
    best = yaml.safe_load(open(pb, encoding="utf-8"))["provisional_best"]["checkpoint"]  # authoritative D7 pick
    if not best:
        print(json.dumps({"skipped": "no eligible provisional-best checkpoint; blind review not run",
                          "branch_hint": "proceed to decision without a promotional blind review"}))
        return
    roles = ["qwen3_8b_base", best]
    norm = load_dir(NORM)
    fr = load_dir(FR)

    units, key = [], {}
    for iid in NORM_ITEMS:
        for r in roles:
            rec = (norm.get(r) or {}).get(iid)
            if rec and rec.get("output_text", "").strip():
                uid = _anon(f"{iid}::{r}")
                units.append({"unit_id": uid, "task_context": iid, "text": rec["output_text"],
                              "review_form": {d: None for d in DIMS}})
                key[uid] = {"item_id": iid, "role": r}
    for iid in FR_ITEMS:
        for r in roles:
            rec = (fr.get(r) or {}).get(iid)
            if rec and rec.get("output_text", "").strip():
                uid = _anon(f"{iid}::{r}")
                units.append({"unit_id": uid, "task_context": iid, "text": rec["output_text"],
                              "review_form": {d: None for d in DIMS}})
                key[uid] = {"item_id": iid, "role": r}
    # hidden calibration controls
    cal_path = os.path.join(_REPO, "benchmarks", "calibration", "grader-calibration-set-v1.jsonl")
    for cal in load_calibration_set(cal_path)[:5]:
        uid = _anon(f"cal::{cal['calibration_id']}")
        units.append({"unit_id": uid, "task_context": "review", "text": cal.get("candidate_output", ""),
                      "review_form": {d: None for d in DIMS}})
        key[uid] = {"calibration": True, "expected": cal.get("known_expected_result")}

    units.sort(key=lambda u: u["unit_id"])
    blind.build_review_bundle(units, {"units": key, "dimensions": DIMS}, {}, REVIEW_ROOT, PRIVATE_ROOT)
    leaks = [u["unit_id"] for u in units if any(t in u["unit_id"].lower()
             for t in ("qwen", "lora", "base", "step", "checkpoint"))]
    packet = [{"unit_id": u["unit_id"], "task_context": u["task_context"], "text": u["text"]} for u in units]
    with open(os.path.join(REVIEW_ROOT, "review", "anonymous", "reviewer-packet.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(packet, fh, ensure_ascii=False, indent=1)
    n_cal = sum(1 for u in units if key[u["unit_id"]].get("calibration"))
    print(json.dumps({"roles_compared": roles, "best": best, "units": len(units),
                      "candidate_units": len(units) - n_cal, "calibration_units": n_cal,
                      "identity_leaks": len(leaks)}, indent=1))


if __name__ == "__main__":
    main()
