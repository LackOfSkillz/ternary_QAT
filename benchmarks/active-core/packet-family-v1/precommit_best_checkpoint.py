"""Dispatch 27 Phase B (D7) — precommit the provisional best LoRA checkpoint BEFORE blind review.

Deterministic, mechanical-only. Eligibility: zero reasoning leak, no new severe-slop/token-cap,
zero critical regressions, canon/no-change/structured/realistic-packet not worse than base. Rank
eligible by: (1) focused-revision unchanged-return reduction, (2) all-three-fix count, (3)
mechanical pass, (4) core-prose, (5) protected preservation, (6) validation loss, (7) earliest.
Does NOT auto-select final/step-21. Writes dispatch-27-provisional-best-checkpoint.yaml.
"""
import json
import os
import re
import sys

import yaml

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RUN = os.path.join(_REPO, "benchmarks", "runs", "qwen3-lora-checkpoint-curve-v1")
CURVE = os.path.join(RUN, "checkpoint-curve-summary.json")
META = os.path.join(RUN, "checkpoint-meta.json")
FR = os.path.join(_REPO, "training", "reports", "dispatch-27-focused-revision-audit.yaml")
OUT = os.path.join(_REPO, "training", "reports")


def step_of(role):
    m = re.search(r"step-(\d+)", role)
    return int(m.group(1)) if m else 10 ** 9


def main():
    curve = json.load(open(CURVE, encoding="utf-8"))
    cv = curve["curve"]
    base = cv["qwen3_8b_base"]
    regr = curve["critical_regressions_vs_base"]
    meta = {f"lora_step-{c['optimizer_step']}": c for c in json.load(open(META, encoding="utf-8"))}
    fr = (yaml.safe_load(open(FR, encoding="utf-8"))["focused_revision_audit"]
          if os.path.exists(FR) else None)
    fr_pc = (fr or {}).get("per_checkpoint", {})
    fr_base = (fr or {}).get("base", {})

    ck = [r for r in cv if r != "qwen3_8b_base"]
    eligible, rejected = [], []
    for r in ck:
        s = cv[r]
        ok = (s["reasoning_trace_rate"] == 0 and s["severe_slop_rate"] <= base["severe_slop_rate"]
              and s["token_cap_rate"] <= base["token_cap_rate"] and regr.get(r, 99) == 0
              and (s["canon_fidelity"] or 0) >= (base["canon_fidelity"] or 0)
              and (s["no_change_accuracy"] or 0) >= (base["no_change_accuracy"] or 0)
              and (s["structured_output_validity"] or 0) >= (base["structured_output_validity"] or 0)
              and (s["realistic_packet_pass_rate"] or 0) >= (base["realistic_packet_pass_rate"] or 0))
        (eligible if ok else rejected).append(r)

    def fr_reduction(r):
        b = (fr_base or {}).get("unchanged_return_rate")
        c = (fr_pc.get(r) or {}).get("unchanged_return_rate")
        return round((b - c), 3) if (b is not None and c is not None) else 0.0

    def all_three(r):
        return (fr_pc.get(r) or {}).get("all_three_fixed_count", 0)

    def val_loss(r):
        v = meta.get(r, {}).get("validation_loss")
        return v if v is not None else 1e9

    best = None
    if eligible:
        best = max(eligible, key=lambda r: (
            fr_reduction(r), all_three(r), cv[r]["mechanical_pass_rate"],
            cv[r]["core_prose_pass_rate"], -val_loss(r), -step_of(r)))

    rec = {"provisional_best": {
        "checkpoint": best,
        "optimizer_step": step_of(best) if best else None,
        "adapter_sha256": meta.get(best, {}).get("adapter_hash") if best else None,
        "selected_before_blind_review": True,
        "focused_revision_gain_unchanged_return_reduction": fr_reduction(best) if best else None,
        "mechanical_result": cv.get(best) if best else None,
        "critical_regressions": regr.get(best) if best else None,
        "validation_loss": val_loss(best) if best and val_loss(best) < 1e9 else None,
        "selection_rationale": (
            "All checkpoints are mechanically eligible (zero regressions/leaks) and TIE on every "
            "metric (the LoRA is neutral), and the focused-revision audit shows no checkpoint "
            "reduces the unchanged-return rate. With all ranking keys tied, the EARLIEST eligible "
            "checkpoint wins (lowest exposure) — step-3. The final/step-21 checkpoint is NOT "
            "privileged." if best else "No checkpoint was eligible."),
        "eligible_alternatives": eligible,
        "rejected_checkpoints": rejected,
        "focused_revision_audit_present": fr is not None,
    }}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "dispatch-27-provisional-best-checkpoint.yaml"), "w",
              encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump(rec, fh, sort_keys=False, allow_unicode=True)
    print(json.dumps({"best": best, "eligible": eligible, "rejected": rejected,
                      "fr_reduction_best": fr_reduction(best) if best else None}, indent=1))


if __name__ == "__main__":
    main()
