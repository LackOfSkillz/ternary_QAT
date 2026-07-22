"""Finalize the existing-checkpoint curve (Dispatch 25, D8).

Scores the collected base / LoRA-10 / LoRA-20 outputs on the frozen 9-item subset (mechanical
gates + Module-J slop), writes per-item + per-checkpoint summaries, and answers the curve
questions. Threshold-locked (analysis refuses without a valid lock). No winner is declared.
"""
import glob
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.thresholds.freeze import require_locked_before_analysis
from linewright.evaluation.battery.score import load_battery, score_output

RUN_DIR = os.path.join(_REPO, "benchmarks", "runs", "lwdb-checkpoint-curve-v0")
NORM = os.path.join(RUN_DIR, "normalized-results")
ROLES = ["target_base", "lora_10", "lora_20"]


def main():
    lock = require_locked_before_analysis()
    items, contracts = load_battery()
    results = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(NORM, "*.json")))]
    rows = []
    for r in results:
        it = items[r["benchmark_item_id"]]
        c = contracts[it["behavior_contract_id"]]
        s = score_output(it, c, r.get("output_text", ""), r.get("hit_token_cap", False))
        rows.append({"item_id": r["benchmark_item_id"], "checkpoint": r["model_role"],
                     "mechanical_pass": s["mechanical"]["mechanical_pass"],
                     "failure_labels": s["mechanical"]["failure_labels"],
                     "slop_severity": s["slop"]["summary"]["severity"],
                     "hit_token_cap": r.get("hit_token_cap"), "output_tokens": r.get("output_tokens"),
                     "output_hash": r["output_hash"]})
    rows.sort(key=lambda x: (x["item_id"], ROLES.index(x["checkpoint"])))
    with open(os.path.join(RUN_DIR, "item-level-results.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2); fh.write("\n")

    def agg(role):
        rs = [r for r in rows if r["checkpoint"] == role]
        return {"jobs": len(rs),
                "mechanical_pass": sum(1 for r in rs if r["mechanical_pass"]),
                "severe_slop": sum(1 for r in rs if r["slop_severity"] == "severe"),
                "token_cap_hits": sum(1 for r in rs if r["hit_token_cap"])}
    per = {role: agg(role) for role in ROLES}

    # curve questions
    mp = {r: per[r]["mechanical_pass"] for r in ROLES}
    ss = {r: per[r]["severe_slop"] for r in ROLES}
    tc = {r: per[r]["token_cap_hits"] for r in ROLES}
    base_mp = mp["target_base"]
    early_improvement = mp["lora_10"] > base_mp or ss["lora_10"] < ss["target_base"]
    late_collapse = (ss["lora_20"] > ss["lora_10"]) or (mp["lora_20"] < mp["lora_10"])
    best = max(ROLES, key=lambda r: (mp[r], -ss[r], -tc[r]))
    onset = "step-20" if ss["lora_20"] > ss["lora_10"] else ("step-10" if ss["lora_10"] > 0 else "not observed in tested range")

    summary = {
        "run_id": "lwdb-checkpoint-curve-v0", "dispatch": 25,
        "threshold_lock": {"git_commit": lock["git_commit"], "research_sha256": lock["research_threshold_sha256"]},
        "subset_size": len({r["item_id"] for r in rows}), "checkpoints": ROLES,
        "per_checkpoint": per,
        "mechanical_pass_curve": mp, "severe_slop_curve": ss, "token_cap_curve": tc,
        "checkpoint_curve": {
            "early_improvement": early_improvement,
            "late_collapse": late_collapse,
            "degeneration_onset": onset,
            "best_observed_checkpoint": best,
            "monotone_worsening": mp["target_base"] >= mp["lora_10"] >= mp["lora_20"] and ss["lora_20"] >= ss["lora_10"] >= ss["target_base"],
        },
        "limitations": ["9-item diagnostic subset (not the full battery)",
                        "only existing checkpoints (base, step-10, step-20); step-5/15 were not saved",
                        "greedy decoding; slop thresholds unvalidated"],
        "no_winner_declared": True,
    }
    with open(os.path.join(RUN_DIR, "checkpoint-curve-summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2); fh.write("\n")
    print(json.dumps({"mechanical_pass": mp, "severe_slop": ss, "token_cap": tc,
                      "curve": summary["checkpoint_curve"]}, indent=1))


if __name__ == "__main__":
    main()
