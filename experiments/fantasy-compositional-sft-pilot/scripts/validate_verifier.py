"""Dispatch 30A — validate the packet-execution verifier (Phase 3) against a manually-labeled
fixture set of ORIGINAL mini-scenes. Covers clear passes, clear failures, ambiguous cases,
protected false positives (single signature family), real stacks, dialogue-heavy first-person,
varied punctuation, and short/long scenes. Emits reports/verifier-report.md and freezes the
verifier version + hash. No third-party prose is used.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import verifier as V  # noqa: E402

# Each fixture: verification block + original output + expected per-check verdicts.
# expect maps a deterministic check-type -> expected 'passed'; stacks_gt0 flags the stacking detector;
# hard_all_pass is the expected joint hard verdict.
FIX = [
    {"id": "f01_clear_pass", "cat": "clear_pass",
     "v": {"pov": {"name": "Kessa"}, "tense": "past", "required_present": ["bronze key"],
           "forbidden_absent": ["dragon"], "ending_state_present": ["the gate opened"]},
     "out": "Kessa crept along the wall. She found the bronze key beneath a loose stone and turned it in the lock. The gate opened.",
     "expect": {"viewpoint": True, "tense": True, "required_name_or_fact": True, "forbidden_event": True, "ending_state": True},
     "stacks_gt0": False, "hard_all_pass": True},

    {"id": "f02_fail_pov_first_person", "cat": "clear_fail",
     "v": {"pov": {"name": "Kessa"}, "tense": "past", "required_present": ["bronze key"],
           "ending_state_present": ["the gate opened"]},
     "out": "Kessa crept forward. I found the bronze key and turned it in the lock. The gate opened.",
     "expect": {"viewpoint": False, "required_name_or_fact": True, "ending_state": True},
     "stacks_gt0": False, "hard_all_pass": False},

    {"id": "f03_fail_forbidden", "cat": "clear_fail",
     "v": {"pov": {"name": "Kessa"}, "tense": "past", "required_present": ["bronze key"],
           "forbidden_absent": ["dragon"], "ending_state_present": ["the gate opened"]},
     "out": "Kessa found the bronze key. A dragon roared beyond the wall. The gate opened.",
     "expect": {"viewpoint": True, "required_name_or_fact": True, "forbidden_event": False, "ending_state": True},
     "stacks_gt0": False, "hard_all_pass": False},

    {"id": "f04_fail_missing_required", "cat": "clear_fail",
     "v": {"pov": {"name": "Kessa"}, "tense": "past", "required_present": ["bronze key"],
           "ending_state_present": ["the gate opened"]},
     "out": "Kessa searched the wall but found nothing useful. She waited a long while. The gate opened.",
     "expect": {"viewpoint": True, "required_name_or_fact": False, "ending_state": True},
     "stacks_gt0": False, "hard_all_pass": False},

    {"id": "f05_ambiguous_tense_low_conf", "cat": "ambiguous",
     "v": {"pov": {"name": "Kessa"}, "tense": "past", "required_present": ["bronze key"],
           "ending_state_present": ["the gate opened"]},
     "out": "Kessa by the gate. The bronze key in her palm. The gate opened.",
     "expect": {"viewpoint": True, "tense": True, "required_name_or_fact": True, "ending_state": True},
     "stacks_gt0": False, "hard_all_pass": True, "tense_conf": "low"},

    {"id": "f06_protected_false_positive", "cat": "protected_false_positive",
     "v": {"pov": {"name": "Bram"}, "tense": "past", "required_present": ["the letter"],
           "ending_state_present": ["he burned it"]},
     "out": "Bram read the letter by candlelight—the last one she ever sent. His hands were steady. He burned it.",
     "expect": {"viewpoint": True, "tense": True, "required_name_or_fact": True, "ending_state": True},
     "stacks_gt0": False, "hard_all_pass": True},

    {"id": "f07_real_stack", "cat": "real_stack",
     "v": {"pov": {"name": "Mara"}, "tense": "past", "required_present": ["the bridge"],
           "ending_state_present": ["she crossed"]},
     "out": "Mara reached the bridge. Her heart pounded like a drum—wild and desperate. She crossed.",
     "expect": {"viewpoint": True, "tense": True, "required_name_or_fact": True, "ending_state": True},
     "stacks_gt0": True, "hard_all_pass": True},

    {"id": "f08_dialogue_heavy_first_person_ok", "cat": "dialogue_heavy",
     "v": {"pov": {"name": "Tam"}, "tense": "past", "required_present": ["the door"],
           "ending_state_present": ["the door stayed shut"]},
     "out": "\"I won't go,\" Tam said. \"I can't.\" He shook his head and stepped back from the door. The door stayed shut.",
     "expect": {"viewpoint": True, "required_name_or_fact": True, "ending_state": True},
     "stacks_gt0": False, "hard_all_pass": True},

    {"id": "f09_varied_punctuation_isolated", "cat": "varied_punctuation",
     "v": {"pov": {"name": "Aldric"}, "tense": "past", "required_present": ["the road"],
           "ending_state_present": ["he walked on"]},
     "out": "Aldric took the road; the night was cold. Rain fell like a veil of silver. Wounded, he walked on.",
     "expect": {"viewpoint": True, "tense": True, "required_name_or_fact": True, "ending_state": True},
     "stacks_gt0": False, "hard_all_pass": True},

    {"id": "f10_short_scene", "cat": "short_scene",
     "v": {"pov": {"name": "Kessa"}, "tense": "past", "required_present": ["bronze key"],
           "ending_state_present": ["the gate opened"]},
     "out": "Kessa found the bronze key, and the gate opened.",
     "expect": {"viewpoint": True, "required_name_or_fact": True, "ending_state": True},
     "stacks_gt0": False, "hard_all_pass": True},

    {"id": "f11_long_scene", "cat": "long_scene",
     "v": {"pov": {"name": "Sable"}, "tense": "past", "required_present": ["the lantern"],
           "forbidden_absent": ["snow"], "ending_state_present": ["the hatch closed"]},
     "out": ("Sable descended the ladder. The air grew colder as she went. She lit the lantern and held it high. "
             "Shadows moved along the wet stone. She counted the doors as she passed them. The seventh was ajar. "
             "She stepped through and set the lantern down. The hatch closed behind her."),
     "expect": {"viewpoint": True, "tense": True, "required_name_or_fact": True, "forbidden_event": True, "ending_state": True},
     "stacks_gt0": False, "hard_all_pass": True},

    {"id": "f12_present_tense_pass", "cat": "present_tense",
     "v": {"pov": {"name": "Nal"}, "tense": "present", "required_present": ["the well"],
           "ending_state_present": ["the bucket"]},
     "out": "Nal walks to the well and looks down. She reaches for the rope. The bucket goes into the dark.",
     "expect": {"viewpoint": True, "tense": True, "required_name_or_fact": True, "ending_state": True},
     "stacks_gt0": False, "hard_all_pass": True, "tense_conf": "high"},

    {"id": "f13_ending_missing", "cat": "clear_fail",
     "v": {"pov": {"name": "Corin"}, "tense": "past", "required_present": ["the deck"],
           "ending_state_present": ["the ship sank"]},
     "out": "Corin clung to the deck. The crew bailed water through the night. They fought the storm until dawn.",
     "expect": {"viewpoint": True, "required_name_or_fact": True, "ending_state": False},
     "stacks_gt0": False, "hard_all_pass": False},

    {"id": "f14_knowledge_boundary_violation", "cat": "clear_fail",
     "v": {"pov": {"name": "Elen"}, "tense": "past", "required_present": ["the market"],
           "knowledge_boundary_absent": ["her brother is the traitor"], "ending_state_present": ["she turned home"]},
     "out": "Elen crossed the market at dusk. She did not yet know her brother is the traitor. She turned home.",
     "expect": {"viewpoint": True, "required_name_or_fact": True, "knowledge_boundary_lexical": False, "ending_state": True},
     "stacks_gt0": False, "hard_all_pass": False},
]


def main():
    checks_total = checks_correct = 0
    false_pos = false_neg = 0
    rows = []
    for f in FIX:
        r = V.verify(f["out"], f["v"], output_id=f["id"], packet_id=f["id"])
        got = {}
        for d in r["deterministic"]:
            got.setdefault(d["check"], d["passed"])  # first of each type
        row = {"id": f["id"], "cat": f["cat"], "mismatches": [],
               "stacks": r["signature_stacking_count"], "hard_all_pass": r["hard_constraints_all_pass"]}
        for check, exp in f["expect"].items():
            checks_total += 1
            g = got.get(check)
            if g == exp:
                checks_correct += 1
            else:
                row["mismatches"].append(f"{check}: got {g} expected {exp}")
                if g is False and exp is True:
                    false_pos += 1
                elif g is True and exp is False:
                    false_neg += 1
        if bool(r["signature_stacking_count"] > 0) != f["stacks_gt0"]:
            row["mismatches"].append(f"stacks>0: got {r['signature_stacking_count']>0} expected {f['stacks_gt0']}")
        if r["hard_constraints_all_pass"] != f["hard_all_pass"]:
            row["mismatches"].append(f"hard_all_pass: got {r['hard_constraints_all_pass']} expected {f['hard_all_pass']}")
        if "tense_conf" in f:
            tconf = next((d["confidence"] for d in r["deterministic"] if d["check"] == "tense"), None)
            if tconf != f["tense_conf"]:
                row["mismatches"].append(f"tense_conf: got {tconf} expected {f['tense_conf']}")
        rows.append(row)

    accuracy = round(checks_correct / checks_total, 3) if checks_total else 0
    all_ok = all(not r["mismatches"] for r in rows)
    ver_hash = hashlib.sha256(open(os.path.join(HERE, "verifier.py"), "rb").read()).hexdigest()
    version = "v1"

    report = {
        "dispatch": "30A", "phase": 3, "verifier_version": version, "verifier_hash": ver_hash,
        "fixtures": len(FIX), "checks_total": checks_total, "checks_correct": checks_correct,
        "fixture_check_accuracy": accuracy, "false_positives": false_pos, "false_negatives": false_neg,
        "all_fixtures_pass": all_ok,
        "categories_covered": sorted({f["cat"] for f in FIX}),
        "rows": rows,
    }
    os.makedirs(os.path.join(EXP, "reports"), exist_ok=True)
    json.dump(report, open(os.path.join(EXP, "reports", "verifier-validation.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    md = [f"# Verifier validation — Phase 3 (Dispatch 30A)", "",
          f"- Verifier: `{version}`  hash `{ver_hash[:16]}…`",
          f"- Fixtures: {len(FIX)} · check-level accuracy **{accuracy}** ({checks_correct}/{checks_total})",
          f"- False positives (flagged valid prose): {false_pos} · false negatives (missed defect): {false_neg}",
          f"- All fixtures pass: **{all_ok}**",
          f"- Categories: {report['categories_covered']}", ""]
    if not all_ok:
        md += ["## Mismatches"]
        for r in rows:
            if r["mismatches"]:
                md += [f"- {r['id']}: " + "; ".join(r["mismatches"])]
    open(os.path.join(EXP, "reports", "verifier-report.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md))

    # freeze verifier version + hash if clean
    vv = json.load(open(os.path.join(EXP, "freeze", "verifier-version.json"), encoding="utf-8"))
    vv["status"] = "frozen" if all_ok else "validation_failed"
    vv["verifier_version"] = version
    vv["verifier_hash"] = ver_hash
    vv["fixture_accuracy"] = accuracy
    json.dump(vv, open(os.path.join(EXP, "freeze", "verifier-version.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"accuracy": accuracy, "all_fixtures_pass": all_ok, "false_pos": false_pos,
                      "false_neg": false_neg, "frozen": all_ok}, indent=1))
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
