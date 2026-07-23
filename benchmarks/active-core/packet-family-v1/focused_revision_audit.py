"""Dispatch 27 Phase B (D5) — focused-revision failure audit across base + every LoRA checkpoint.

The pilot's PRIMARY target is the multi-constraint focused-revision failure ("returns the passage
unchanged despite authorized corrections"). The frozen 14-item eval subset only tests SINGLE-fix
revision, so this audit runs a supplementary probe on the three-fix pf-focused_revision items (the
actual dominant failure) and measures, per role, whether the LoRA converts unchanged-returns into
valid revisions WITHOUT corrupting the protected line or over-editing.

Honesty note (per dispatch): the external-review reviewer-level fatal rate (~0.20) is NOT the same
measurement as this item-level unchanged-return rate; they are not compared directly.
"""
import glob
import json
import os

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FR = os.path.join(_REPO, "benchmarks", "runs", "qwen3-lora-checkpoint-curve-v1", "fr-normalized-results")
OUTDIR = os.path.join(_REPO, "training", "reports")

PROTECTED = ("The stairs went up in the dark the way she remembered, ninety-nine of them, "
             "and she counted every one.")
SIMILE = "sleeping giant"
FR_ITEMS = ["pf-focused_revision-compact", "pf-focused_revision-realistic",
            "pf-focused_revision-long_salience_repaired"]


def defects(text):
    low = text.lower()
    import re
    # 3+ consecutive sentences opening with "She "
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    run = mx = 0
    for s in sents:
        if s.startswith("She "):
            run += 1; mx = max(mx, run)
        else:
            run = 0
    return {"anachronism_present": "phone" in low,
            "purple_simile_present": SIMILE in low,
            "repeated_she_openers": mx >= 3,
            "protected_line_preserved": PROTECTED in text}


def audit_role(role_dir):
    rows = {}
    for p in glob.glob(os.path.join(role_dir, "*.json")):
        r = json.load(open(p, encoding="utf-8"))
        iid = r["benchmark_item_id"]
        if iid not in FR_ITEMS:
            continue
        text = r.get("output_text", "")
        d = defects(text)
        fixed = sum([not d["anachronism_present"], not d["purple_simile_present"], not d["repeated_she_openers"]])
        unchanged = d["anachronism_present"] and d["purple_simile_present"] and d["repeated_she_openers"]
        rows[iid] = {"fixes_applied": fixed, "unchanged_return": unchanged,
                     "protected_preserved": d["protected_line_preserved"], **d}
    return rows


def summarize(rows):
    n = len(rows)
    if not n:
        return None
    return {"n": n,
            "unchanged_return_count": sum(1 for v in rows.values() if v["unchanged_return"]),
            "unchanged_return_rate": round(sum(1 for v in rows.values() if v["unchanged_return"]) / n, 3),
            "mean_fixes_applied": round(sum(v["fixes_applied"] for v in rows.values()) / n, 3),
            "all_three_fixed_count": sum(1 for v in rows.values() if v["fixes_applied"] == 3),
            "protected_preserved_rate": round(sum(1 for v in rows.values() if v["protected_preserved"]) / n, 3)}


def main():
    role_dirs = sorted(glob.glob(os.path.join(FR, "*")))
    audit = {os.path.basename(d): audit_role(d) for d in role_dirs}
    summ = {r: summarize(rows) for r, rows in audit.items() if summarize(rows)}
    base = summ.get("qwen3_8b_base")

    def step_of(role):
        import re
        m = re.search(r"step-(\d+)", role)
        return int(m.group(1)) if m else 10**9

    ck = sorted([r for r in summ if r != "qwen3_8b_base"], key=step_of)
    reduced = []
    for r in ck:
        if base and summ[r]["unchanged_return_rate"] < base["unchanged_return_rate"]:
            reduced.append(r)
    out = {
        "dispatch": 27, "phase": "B", "primary_target": "multi_constraint_focused_revision",
        "probe_items": FR_ITEMS,
        "measurement_note": "item-level unchanged-return rate on the 3-fix revision items; NOT the "
                            "same as the external reviewer-level fatal rate (~0.20) and not compared to it.",
        "base": base,
        "per_checkpoint": summ,
        "checkpoints_reducing_unchanged_return": reduced,
        "converts_unchanged_to_valid": len(reduced) > 0,
        "over_editing_protected_line": {r: (summ[r]["protected_preserved_rate"] < 1.0) for r in summ},
    }
    os.makedirs(OUTDIR, exist_ok=True)
    import yaml
    with open(os.path.join(OUTDIR, "dispatch-27-focused-revision-audit.yaml"), "w",
              encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump({"focused_revision_audit": out}, fh, sort_keys=False, allow_unicode=True)
    print(json.dumps({"base": base, "per_checkpoint_unchanged_rate": {r: summ[r]["unchanged_return_rate"] for r in summ},
                      "reducing": reduced, "converts": out["converts_unchanged_to_valid"]}, indent=1))


if __name__ == "__main__":
    main()
