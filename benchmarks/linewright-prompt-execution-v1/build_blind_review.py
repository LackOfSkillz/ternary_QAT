"""Dispatch 28B — build arm-hidden blind review packages (ChatGPT / Claude / Gary_optional).

Selects a balanced, honest ~40-70 unit set: all P3-Ideal + their paired P1-Contract, every critical
failure / invalid-unchanged / suspected over-edit, and a balanced random sample of clean successes
per arm. Reviewers see only a neutral task brief (the author's actual request + source), never the
arm, the mechanical result, the prior decision, or contract-vs-prose status. 4 broken + 1 good
calibration controls are seeded. Deterministic selection (fixed seed).
"""
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from linewright.evaluation.battery import blind
from linewright.evaluation.calibration.records import load_calibration_set

RUN = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(
    HERE, "..", "runs", "linewright-prompt-execution-v1")
RUN = os.path.abspath(RUN)
ARM_DIR = {"P0-Realistic": "p0-realistic", "P0-Maximal": "p0-maximal",
           "P1-Contract": "p1-contract", "P3-Ideal": "p3-ideal"}
DIMS = ["prose_quality", "voice_preservation", "naturalness", "scene_coherence", "pacing",
        "scope_control", "author_usefulness", "rigidity", "over_editing", "repetition_or_slop"]
DIAG = ["fatal_failure", "fatal_failure_type", "fatal_failure_evidence", "strongest_quality",
        "main_weakness", "one_line_note", "confidence"]
SEED = 20260723
TARGET = 56


def anon(s):
    return "unit-" + hashlib.sha256(s.encode()).hexdigest()[:16]


def main():
    tasks = {t["task_id"]: t for t in (json.loads(l) for l in
             open(os.path.join(HERE, "task-manifest.jsonl"), encoding="utf-8") if l.strip())}
    item = json.load(open(os.path.join(RUN, "item-level-results.json"), encoding="utf-8"))
    p3_subset = json.load(open(os.path.join(HERE, "p3-ideal-subset.json"), encoding="utf-8"))["tasks"]

    outputs = {}
    for arm, d in ARM_DIR.items():
        dd = os.path.join(RUN, "normalized-results", d)
        if not os.path.isdir(dd):
            continue
        for fn in os.listdir(dd):
            if fn.endswith(".json"):
                r = json.load(open(os.path.join(dd, fn), encoding="utf-8"))
                outputs[(r["task_id"], arm)] = r.get("normalized_text", r.get("output_text", ""))

    rnd = random.Random(SEED)
    selected = set()
    # 1. all P3-Ideal + paired P1-Contract
    for tid in p3_subset:
        selected.add((tid, "P3-Ideal"))
        selected.add((tid, "P1-Contract"))
    # 2. every critical failure / invalid unchanged / suspected over-edit
    for key, it in item.items():
        tid, arm = key.split("::")
        if it["critical_failure"] or it["invalid_unchanged"] or it["unauthorized_edit"]:
            selected.add((tid, arm))
    # 3. balanced random sample of clean successes per arm up to TARGET
    clean_by_arm = {}
    for key, it in item.items():
        tid, arm = key.split("::")
        if it["clean_execution"] and (tid, arm) not in selected:
            clean_by_arm.setdefault(arm, []).append((tid, arm))
    for arm in clean_by_arm:
        rnd.shuffle(clean_by_arm[arm])
    ai = 0
    arms_cycle = ["P0-Realistic", "P0-Maximal", "P1-Contract", "P3-Ideal"]
    while len(selected) < TARGET:
        arm = arms_cycle[ai % len(arms_cycle)]
        ai += 1
        pool = clean_by_arm.get(arm, [])
        if pool:
            selected.add(pool.pop())
        if ai > 400:
            break

    units, key = [], {}
    for (tid, arm) in sorted(selected):
        text = outputs.get((tid, arm), "")
        if not text.strip():
            continue
        t = tasks[tid]
        brief = t["compiler_inputs"]["user_request"]
        src = t["source_passage"]
        task_brief = "The author asked:\n" + brief + (("\n\nPassage:\n" + src) if src else "")
        uid = anon(f"{tid}::{arm}")
        units.append({"unit_id": uid, "task_context": task_brief, "text": text,
                      "review_form": {**{d: None for d in DIMS}, **{d: None for d in DIAG}}})
        key[uid] = {"task_id": tid, "arm": arm}

    # calibration: 4 broken + 1 good
    cal_path = os.path.join(HERE, "..", "calibration", "grader-calibration-set-v1.jsonl")
    cal_path = os.path.abspath(cal_path)
    cals = load_calibration_set(cal_path)
    broken = [c for c in cals if any(w in str(c.get("known_expected_result", "")).lower()
              for w in ("broken", "fail", "reject", "bad"))][:4]
    good = [c for c in cals if c not in broken][:1]
    for c in broken + good:
        uid = anon(f"cal::{c['calibration_id']}")
        units.append({"unit_id": uid, "task_context": "The author asked for a short revision.",
                      "text": c.get("candidate_output", ""),
                      "review_form": {**{d: None for d in DIMS}, **{d: None for d in DIAG}}})
        key[uid] = {"calibration": True, "expected": c.get("known_expected_result")}

    units.sort(key=lambda u: u["unit_id"])
    review_root = os.path.join(RUN, "review")
    private_root = os.path.join(RUN, "private-unblinding")
    blind.build_review_bundle(units, {"units": key, "dimensions": DIMS + DIAG}, {}, review_root, private_root)

    leaks = [u["unit_id"] for u in units if any(w in u["unit_id"].lower()
             for w in ("p0", "p1", "p3", "realistic", "maximal", "contract", "ideal", "arm"))]
    # also scan visible text for arm-identifying tokens
    text_leaks = [u["unit_id"] for u in units if any(w in u["task_context"].lower()
                  for w in ("p0-", "p1-", "p3-", "lw-research-contract", "lw-ideal-packet"))]
    packet = [{"unit_id": u["unit_id"], "task_context": u["task_context"], "text": u["text"]} for u in units]
    anon_dir = os.path.join(review_root, "anonymous")
    os.makedirs(anon_dir, exist_ok=True)
    json.dump(packet, open(os.path.join(anon_dir, "reviewer-packet.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n_cal = sum(1 for u in units if key[u["unit_id"]].get("calibration"))
    _write_packages(review_root, packet)
    summary = {"units": len(units), "candidate": len(units) - n_cal, "calibration": n_cal,
               "broken_controls": len(broken), "good_controls": len(good),
               "id_leaks": len(leaks), "text_leaks": len(text_leaks),
               "arm_distribution": _armdist(key)}
    json.dump(summary, open(os.path.join(RUN, "review-build-summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(summary, indent=1))


def _write_packages(review_root, packet):
    readme = ("# Blind prose review — LineWright fiction outputs\n\n"
              "You are reviewing anonymous fiction-writing outputs from a language model. Each unit has "
              "a task brief (what the author asked for) and the model's output. You do NOT know which "
              "system or prompt style produced any output — judge only what you see.\n\n"
              "Score every unit on the 1-5 rubric in SCORING-RUBRIC.md and record a fatal_failure flag "
              "where warranted. A few hidden calibration controls are mixed in; score them like any "
              "other unit. Return your scores in the shape of completed-review-template.json.\n")
    instr = ("# Scoring instructions\n\n"
             "1. Read the task brief, then the output.\n"
             "2. Judge the output AGAINST THE VISIBLE BRIEF — not against a hidden ideal answer.\n"
             "3. Score all 10 dimensions 1-5 (see SCORING-RUBRIC.md). Higher is better, including "
             "over_editing (5 = disciplined, only what was asked) and rigidity (5 = natural, not "
             "mechanical).\n"
             "4. Set fatal_failure true only for outputs an author could not use as drafted "
             "(corrupted protected text, ignored the request, invented major content, broke the "
             "requested format, or incoherent prose). Give the type and one-line evidence.\n"
             "5. Do not try to guess the system or prompt style. Do not reward length or formality.\n")
    rubric = ("# Rubric (1-5, higher is better)\n\n"
              "- prose_quality — sentence craft, imagery, control\n"
              "- voice_preservation — keeps the author's established voice\n"
              "- naturalness — reads like human prose, not a checklist\n"
              "- scene_coherence — internally consistent, follows\n"
              "- pacing — rhythm and momentum\n"
              "- scope_control — changed only what was asked\n"
              "- author_usefulness — would a novelist use this draft\n"
              "- rigidity — 5 natural / 1 stiff, mechanical\n"
              "- over_editing — 5 disciplined / 1 rewrote untouched material\n"
              "- repetition_or_slop — 5 clean / 1 repetitive, padded\n\n"
              "Diagnostics: fatal_failure (bool), fatal_failure_type, fatal_failure_evidence, "
              "strongest_quality, main_weakness, one_line_note, confidence (1-5).\n")
    tmpl = {"reviewer_id": "REPLACE_ME", "scores": [
        {"unit_id": p["unit_id"], **{d: None for d in DIMS},
         "fatal_failure": None, "fatal_failure_type": "", "fatal_failure_evidence": "",
         "strongest_quality": "", "main_weakness": "", "one_line_note": "", "confidence": None}
        for p in packet]}
    checklist = ("# Submission checklist\n\n"
                 f"- [ ] Every one of the {len(packet)} units has a score for all 10 dimensions\n"
                 "- [ ] fatal_failure set on every unit (true/false)\n"
                 "- [ ] You did not attempt to identify the source system/prompt of any unit\n"
                 "- [ ] reviewer_id filled in\n")
    units_md = ["# Anonymous review units", ""]
    for p in packet:
        units_md += [f"## {p['unit_id']}", "", "**Task brief:**", p["task_context"], "",
                     "**Output:**", p["text"], "", "---", ""]
    import yaml as _yaml
    for reviewer in ("ChatGPT", "Claude", "Gary_optional"):
        d = os.path.join(review_root, "packages", reviewer)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "README-FIRST.md"), "w", encoding="utf-8", newline="\n").write(readme)
        open(os.path.join(d, "SCORING-INSTRUCTIONS.md"), "w", encoding="utf-8", newline="\n").write(instr)
        open(os.path.join(d, "SCORING-RUBRIC.md"), "w", encoding="utf-8", newline="\n").write(rubric)
        open(os.path.join(d, "SUBMISSION-CHECKLIST.md"), "w", encoding="utf-8", newline="\n").write(checklist)
        open(os.path.join(d, "ANONYMOUS-REVIEW-UNITS.md"), "w", encoding="utf-8", newline="\n").write("\n".join(units_md))
        json.dump(packet, open(os.path.join(d, "reviewer-packet.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        t = dict(tmpl); t["reviewer_id"] = reviewer
        json.dump(t, open(os.path.join(d, "completed-review-template.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        _yaml.safe_dump(t, open(os.path.join(d, "completed-review-template.yaml"), "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)


def _armdist(key):
    from collections import Counter
    return dict(Counter(v.get("arm", "calibration") for v in key.values()))


if __name__ == "__main__":
    main()
