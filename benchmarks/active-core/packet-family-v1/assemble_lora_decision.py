"""Dispatch 27 Phase B — apply the frozen LoRA advancement rule and select a branch.

Reads the mechanical checkpoint curve + the blind base-vs-LoRA prose summary and applies the
precommitted advancement rule (spec qwen3-8b-lora-pilot-v1). Effect floors: blind prose gain
>=0.25, voice gain >=0.25, instruction drop <=0.15, zero new fatal, zero critical/severe-slop/
token-cap/reasoning regressions. Writes dispatch-27-lora-decision.{yaml,md}.
"""
import json
import os
import sys

import yaml

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RUN = os.path.join(_REPO, "benchmarks", "runs", "qwen3-lora-checkpoint-curve-v1")
CURVE = os.path.join(RUN, "checkpoint-curve-summary.json")
BLIND = os.path.join(RUN, "lora-blind-review-summary.json")
OUT = os.path.join(_REPO, "training", "reports")

FLOORS = {"min_prose_gain": 0.25, "min_voice_gain": 0.25, "max_instruction_drop": 0.15,
          "max_new_fatal": 0}


def main():
    curve = json.load(open(CURVE, encoding="utf-8"))
    base = curve["curve"]["qwen3_8b_base"]
    pb = os.path.join(_REPO, "training", "reports", "dispatch-27-provisional-best-checkpoint.yaml")
    best = yaml.safe_load(open(pb, encoding="utf-8"))["provisional_best"]["checkpoint"]  # authoritative D7 pick
    regr = curve["critical_regressions_vs_base"]
    blind = json.load(open(BLIND, encoding="utf-8")) if os.path.exists(BLIND) else None

    # mechanical preconditions (from the curve)
    best_regr = regr.get(best, 99) if best else 99
    mech = {
        "provisional_best_checkpoint": best,
        "critical_regressions_at_best": best_regr,
        "reasoning_leak_at_best": (curve["curve"].get(best, {}).get("reasoning_trace_rate")
                                   if best else None),
        "core_prose_not_worse": (curve["curve"].get(best, {}).get("core_prose_pass_rate", 0)
                                 >= base["core_prose_pass_rate"]) if best else False,
        "structured_not_worse": (curve["curve"].get(best, {}).get("structured_output_validity", 0)
                                 >= base["structured_output_validity"]) if best else False,
    }

    # blind prose deltas (best - base), if the blind review has run
    prose_gain = voice_gain = instr_drop = new_fatal = None
    if blind:
        b = blind.get("per_role_means", {})
        base_m = b.get("qwen3_8b_base", {})
        best_m = b.get(best, {})
        if base_m and best_m:
            prose_gain = round(best_m.get("prose_quality", 0) - base_m.get("prose_quality", 0), 3)
            voice_gain = round(best_m.get("voice_preservation", 0) - base_m.get("voice_preservation", 0), 3)
            instr_drop = round(base_m.get("instruction_compliance", 0) - best_m.get("instruction_compliance", 0), 3)
            new_fatal = blind.get("new_fatal_best_vs_base", 0)

    # ---- advancement rule ----
    reasons = []
    advances = False
    if best is None:
        branch = "revise_LoRA_recipe"
        reasons.append("no checkpoint was mechanically eligible (all had a critical regression, "
                       "severe-slop/token-cap increase, or reasoning leak) — the recipe, not the base, "
                       "is the problem to change.")
    elif best_regr > 0 or (mech["reasoning_leak_at_best"] or 0) > 0:
        branch = "revise_LoRA_recipe"
        reasons.append(f"the best checkpoint still carries {best_regr} critical regression(s) / leak.")
    elif blind is None:
        branch = "run_one_bounded_confirmation"
        reasons.append("mechanical curve is clean but the blind base-vs-LoRA prose review has not run yet.")
    elif (prose_gain is not None and prose_gain >= FLOORS["min_prose_gain"]
          and voice_gain >= FLOORS["min_voice_gain"] and instr_drop <= FLOORS["max_instruction_drop"]
          and (new_fatal or 0) <= FLOORS["max_new_fatal"] and mech["core_prose_not_worse"]
          and mech["structured_not_worse"]):
        branch = "select_LoRA_checkpoint"
        advances = True
        reasons.append(f"advancement rule PASSES: blind prose +{prose_gain}, voice +{voice_gain}, "
                       f"instruction drop {instr_drop} (<=0.15), zero critical regressions, structured "
                       "+ core-prose not worse.")
    else:
        # neutral / below-floor gains with no critical regression -> dataset is the lever
        below = []
        if prose_gain is not None and prose_gain < FLOORS["min_prose_gain"]:
            below.append(f"prose gain {prose_gain} < {FLOORS['min_prose_gain']}")
        if voice_gain is not None and voice_gain < FLOORS["min_voice_gain"]:
            below.append(f"voice gain {voice_gain} < {FLOORS['min_voice_gain']}")
        branch = "revise_Dataset_A3"
        reasons.append("the conservative pilot is NON-DESTRUCTIVE (no critical regression, no "
                       "degeneration) but the blind prose gain is below the effect floor "
                       f"({', '.join(below) or 'neutral'}). At 42 training records this is the "
                       "expected feasibility signal: the pipeline works and the recipe is safe, but "
                       "the dataset is too small/thin to move prose — scale + curate Dataset A.3 "
                       "(toward the 200-500 target, teacher-diversified, Gate-3 reviewed) before "
                       "retraining. NOT retain_Qwen_base, because the lever to pull is the dataset, "
                       "not abandoning tuning.")

    decision = {
        "dispatch": 27, "phase": "B", "provisional": True, "final_commercial_ship_certification": False,
        "advancement_floors": FLOORS,
        "mechanical_preconditions": mech,
        "blind_prose": ({"prose_gain": prose_gain, "voice_gain": voice_gain,
                         "instruction_drop": instr_drop, "new_fatal": new_fatal}
                        if blind else "PENDING"),
        "branch": branch, "lora_advances": advances,
        "selected_checkpoint": best if advances else None,
        "rationale": reasons,
        "rejected_branches": [b for b in ["select_LoRA_checkpoint", "retain_Qwen_base",
                              "revise_Dataset_A3", "revise_LoRA_recipe", "run_one_bounded_confirmation",
                              "stop_Qwen_tuning_direction"] if b != branch],
        "qat_authorized": advances,   # QAT spec is created only if a checkpoint is selected
        "qat_started": False,
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "dispatch-27-lora-decision.yaml"), "w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump({"lora_decision": decision}, fh, sort_keys=False, allow_unicode=True)
    print(json.dumps({"branch": branch, "lora_advances": advances, "selected": decision["selected_checkpoint"],
                      "blind_prose": decision["blind_prose"], "qat_authorized": decision["qat_authorized"]}, indent=1))
    return decision


if __name__ == "__main__":
    main()
