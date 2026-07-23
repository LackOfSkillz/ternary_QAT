"""Dispatch 30A-R1 — Phases 4-5: assemble matched atomic/compositional records from back-translated
packets.

Inputs (all private/git-ignored): accepted-passages.jsonl, the per-passage target payloads, and an
authored-packets.json holding the human/Aedan-authored MECHANICS-level scene structure (abstracted,
no prose). Outputs: git-ignored provenance-packets.jsonl + atomic-records.jsonl +
compositional-records.jsonl, and a COMMITTED metadata-only report (counts / retrieval-risk /
validation status). The training packet is the model-visible, retrieval-key-free instruction; the
gold target stays the unchanged professional passage (offset+hash). No source prose is emitted.
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import verifier as V  # noqa: E402
from segment_scenes import STOP_NAMES  # noqa: E402

NORM_DIR = os.path.join(EXP, "private-data", "normalized-sources")
TARGETS = os.path.join(EXP, "private-data", "targets")
ACCEPTED = os.path.join(EXP, "manifests", "accepted-passages.jsonl")
AUTHORED = os.path.join(EXP, "private-data", "authored-packets.json")
PROV = os.path.join(EXP, "manifests", "provenance-packets.jsonl")
ATOMIC = os.path.join(EXP, "manifests", "atomic-records.jsonl")
COMPO = os.path.join(EXP, "manifests", "compositional-records.jsonl")
SYS_PROMPT_V = "lw-scene-executor-v1"
PACKET_SCHEMA_V = "scene-packet.schema.json@1"


# capitalized tokens that are ordinary English words, not source-identifying names
COMMON_CAP = {"Will", "Win", "Hope", "Grace", "Rose", "Mark", "May", "Art", "Rush", "Wren", "Ser",
              "Lord", "Lady", "King", "Queen", "Sun", "Moon", "North", "South", "East", "West",
              "Good", "Well", "Even", "Still", "Once", "Long", "Cold", "Dark", "Wood", "Stone",
              "River", "Hill", "Gate", "Hall", "House", "Bell", "Rain", "Storm", "Winter"}


def source_proper_names(text, k=12):
    freq = {}
    for t in re.findall(r"\b[A-Z][a-z]{3,}\b", text):   # len>=4
        if t not in STOP_NAMES and t not in COMMON_CAP:
            freq[t] = freq.get(t, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:k]]


def name_hits(tp, names):
    # case-SENSITIVE, whole-word: a genuine leak appears as the capitalized name, not a lowercase
    # common word (abstracted packets use lowercase roles).
    blob = json.dumps(tp, ensure_ascii=False)
    return [n for n in names if re.search(r"\b" + re.escape(n) + r"\b", blob)]


def person_and_tense(text):
    narr = V.narration_only(text)
    person = "first" if re.search(r"\b(I|me|my)\b", narr) and len(re.findall(r"\b(I|my)\b", narr)) >= 3 else "third"
    past = len(V._PAST_NARR.findall(narr)); pres = len(V._PRESENT_NARR.findall(narr))
    tense = "present" if pres > past and pres >= 3 else "past"
    return person, tense


def training_packet(pid, a, person, tense):
    """Model-visible packet: abstracted scene mechanics only. No source identifiers/names/wording.
    Never embeds the passage id. Caps meaningful constraints at 8 (>=4 load-bearing)."""
    load = [b for b in a["beats"] if b["imp"] == "load_bearing"][:5]
    canon = [c for c in a.get("canon", []) if c["imp"] in ("load_bearing", "supportive")]
    canon = canon[:max(0, 6 - len(load))]          # keep meaningful (load+canon+2) <= 8
    comp_constraints = load + canon
    return {
        "schema_version": 1,
        "viewpoint": f"{person}_{a.get('distance','close')}_{a['viewpoint_role']}",
        "tense": tense, "scene_purpose": a["scene_purpose"], "opening_state": a["opening_state"],
        "required_beats": [b["t"] for b in load],
        "canon_facts": [c["t"] for c in canon],
        "character_goals": a.get("character_goals", []),
        "knowledge_limits": a.get("knowledge_limits", []),
        "forbidden_developments": a.get("forbidden_developments", []),
        "scene_boundary": a["scene_boundary"], "ending_state": a["ending_state"],
        "craft_profile": a.get("craft", {}), "output_contract": "prose_scene",
        "_meaningful": len(comp_constraints) + 2,   # + viewpoint + ending_state
        "_load_bearing": len(load) + 1,             # + ending_state as load-bearing
    }


def retrieval_risk(tp, names):
    hits = len(name_hits(tp, names))
    return "high" if hits >= 3 else "medium" if hits >= 1 else "low"


def main():
    acc = {r["passage_id"]: r for r in (json.loads(l) for l in open(ACCEPTED, encoding="utf-8") if l.strip())}
    authored = json.load(open(AUTHORED, encoding="utf-8"))
    prov_rows, atomic_rows, compo_rows, report = [], [], [], []
    for pid, r in acc.items():
        if pid not in authored:
            report.append({"passage_id": pid, "status": "MISSING_AUTHORED_PACKET"}); continue
        a = authored[pid]
        seg = json.load(open(os.path.join(TARGETS, pid + ".json"), encoding="utf-8"))["text"]
        names = source_proper_names(seg)
        person, tense = person_and_tense(seg)
        tp = training_packet(pid, a, person, tense)
        target = {"source_filename": r["source_filename"], "source_sha256": r["source_sha256"],
                  "start_character_offset": r["start_character_offset"],
                  "end_character_offset": r["end_character_offset"],
                  "target_hash": r["target_sha256"], "target_word_count": r["target_word_count"],
                  "target_token_count": r.get("target_token_count"), "target_text_unchanged": True}
        rr = retrieval_risk(tp, names)
        # validation: training packet must not carry source identifiers or names
        banned = [r["source_filename"], os.path.splitext(r["source_filename"])[0], pid,
                  (a.get("author") or ""), (a.get("title") or "")]
        blob = json.dumps(tp, ensure_ascii=False).lower()
        id_leak = [b for b in banned if b and b.lower() in blob]
        name_leak = name_hits(tp, names)
        meaningful, load_bearing = tp["_meaningful"], tp["_load_bearing"]
        comp_ok = 5 <= meaningful <= 8 and load_bearing >= 4
        atomic_constraints = a["atomic"][:2]
        atomic_ok = 1 <= len(atomic_constraints) <= 2
        valid = (not id_leak) and (not name_leak) and comp_ok and atomic_ok and rr != "high"

        prov_rows.append({"passage_id": pid, "provenance_packet": a, "source_filename": r["source_filename"]})
        base_target = {"target": target, "pairing": {"matched_record_id": None}}
        comp_rec = {"record_id": f"{pid}-C", "arm": "compositional",
                    "training_packet": {k: v for k, v in tp.items() if not k.startswith("_")},
                    "abstraction_notes": a.get("retrieval_risk_self", ""), "retrieval_risk": rr,
                    "target": target, "pairing": {"matched_record_id": f"{pid}-A", "same_target_as_matched": True},
                    "constraint_accounting": {"meaningful_constraints": meaningful, "load_bearing_constraints": load_bearing}}
        atom_tp = {**{k: v for k, v in tp.items() if not k.startswith("_")}, "arm": "atomic",
                   "required_beats": atomic_constraints, "canon_facts": [], "character_goals": [],
                   "knowledge_limits": [], "forbidden_developments": []}
        atom_rec = {"record_id": f"{pid}-A", "arm": "atomic", "training_packet": atom_tp,
                    "retrieval_risk": rr, "target": target,
                    "pairing": {"matched_record_id": f"{pid}-C", "same_target_as_matched": True},
                    "constraint_accounting": {"meaningful_constraints": len(atomic_constraints),
                                              "load_bearing_constraints": len(atomic_constraints)}}
        compo_rows.append(comp_rec); atomic_rows.append(atom_rec)
        report.append({"passage_id": pid, "source_filename": r["source_filename"],
                       "target_word_count": r["target_word_count"], "target_token_count": r.get("target_token_count"),
                       "compositional_constraints": meaningful, "load_bearing_constraints": load_bearing,
                       "atomic_constraints": len(atomic_constraints), "retrieval_risk": rr,
                       "packet_validation": "valid" if valid else "needs_revision",
                       "issues": {"id_leak": bool(id_leak), "name_leak": name_leak[:3],
                                  "compositional_range_ok": comp_ok, "atomic_range_ok": atomic_ok},
                       "recommend_exclusion": rr == "high" or bool(id_leak)})
    for path, rows in [(PROV, prov_rows), (ATOMIC, atomic_rows), (COMPO, compo_rows)]:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for x in rows:
                fh.write(json.dumps(x, ensure_ascii=False) + "\n")
    rep = {"dispatch": "30A-R1", "phase": "4-5", "system_prompt_version": SYS_PROMPT_V,
           "packet_schema_version": PACKET_SCHEMA_V, "paired_records": len(compo_rows),
           "all_valid": all(x.get("packet_validation") == "valid" for x in report),
           "records": report}
    json.dump(rep, open(os.path.join(EXP, "reports", "packet-backtranslation-report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"paired_records": len(compo_rows), "all_valid": rep["all_valid"],
                      "retrieval_risk": {x["passage_id"]: x.get("retrieval_risk") for x in report if "retrieval_risk" in x}}, indent=1))


if __name__ == "__main__":
    main()
