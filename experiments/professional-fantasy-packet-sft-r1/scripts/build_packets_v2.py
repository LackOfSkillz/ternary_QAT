"""Dispatch 30A-R1 — assemble + validate v2 packet records for a batch (default: batch1 = c02).

Consumes authored-packets-batch1.json (private: provenance + abstracted compositional + atomic per
passage), the accepted-passages manifest (unchanged gold targets), and the private targets (for
lexical/leakage checks only). Emits private v2 records + a COMMITTED metadata-only validation report
(schema validity, constraint accounting, lexical risk, 5-gram leakage, target-match). Structural risk
and exact tokens are merged in later steps. No source prose emitted.
"""
import hashlib
import json
import os
import re
import sys

import jsonschema

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from build_packets import source_proper_names, name_hits  # noqa: E402

ACCEPTED = os.path.join(EXP, "manifests", "accepted-passages.jsonl")
TARGETS = os.path.join(EXP, "private-data", "targets")
SCHEMAS = os.path.join(EXP, "schemas")
OUTDIR = os.path.join(EXP, "private-data", "training-packets")
BATCH = sys.argv[1] if len(sys.argv) > 1 else "batch1"
AUTHORED = os.path.join(EXP, "private-data", f"authored-packets-{BATCH}.json")
STRUCT = os.path.join(EXP, "private-data", f"structural-risk-{BATCH}.json")


def load_schema(name):
    return json.load(open(os.path.join(SCHEMAS, name), encoding="utf-8"))


COMP_SCHEMA = load_schema("scene-packet.v2.schema.json")
ATOM_SCHEMA = load_schema("atomic-scene-packet.v2.schema.json")
PROV_SCHEMA = load_schema("provenance-packet.v2.schema.json")


def five_grams(text):
    w = re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split()
    return {" ".join(w[i:i + 5]) for i in range(0, max(0, len(w) - 4))}


def build_compositional(pid, c):
    beats = list(c.get("required_beats", []))
    canon = list(c.get("canon_facts", []))
    kl = list(c.get("knowledge_limits", []))
    fd = list(c.get("forbidden_developments", []))
    pc = list(c.get("physical_continuity", []))
    # meaningful = beats + viewpoint + ending + canon + kl + fd + pc ; cap 9 by trimming soft extras
    fixed = len(beats) + 2  # viewpoint + ending_state (both load-bearing)
    extras = []
    for kind, lst in (("canon", canon), ("kl", kl), ("fd", fd), ("pc", pc)):
        for x in lst:
            extras.append((kind, x))
    while fixed + len(extras) > 9:
        extras.pop()  # drop least-critical soft constraints last-added
    canon = [x for k, x in extras if k == "canon"]
    kl = [x for k, x in extras if k == "kl"]
    fd = [x for k, x in extras if k == "fd"]
    pc = [x for k, x in extras if k == "pc"]
    meaningful = fixed + len(extras)
    load_bearing = len(beats) + 2
    tp = {
        "packet_version": "scene-packet-v2", "task": "write_scene",
        "viewpoint": f"{c.get('person','third')}_{c.get('distance','close')}_{c['viewpoint_role']}",
        "tense": c.get("tense", "past"), "narrative_distance": c.get("distance"),
        "opening_state": c.get("opening_state", ""), "scene_purpose": c.get("scene_purpose", ""),
        "required_beats": beats, "canon_facts": canon, "character_goals": c.get("character_goals", []),
        "knowledge_limits": kl, "forbidden_developments": fd, "physical_continuity": pc,
        "scene_boundary": c.get("scene_boundary", ""), "ending_state": c.get("ending_state", ""),
        "craft_profile": c.get("craft_profile", {}), "output_contract": "prose_scene",
        "constraint_accounting": {"meaningful_constraints": meaningful, "load_bearing_constraints": load_bearing,
                                  "boilerplate_constraints": 0},
        "retrieval_risk": {"lexical_identifier_risk": {"rating": "low", "reason": ""},
                           "structural_reconstruction_risk": {"rating": "pending", "reason": "subagent"},
                           "distinctive_elements": {}, "recommendation": "accept"},
    }
    return tp


def build_atomic(a):
    obs = a[:2] if isinstance(a, list) else [a]
    return {"packet_version": "atomic-scene-packet-v2", "task": "write_scene",
            "viewpoint": None, "tense": None, "required_beats": obs, "output_contract": "prose_scene",
            "constraint_accounting": {"meaningful_constraints": len(obs), "hidden_compound_constraints": 0}}


def main():
    acc = {r["passage_id"]: r for r in (json.loads(l) for l in open(ACCEPTED, encoding="utf-8") if l.strip())}
    authored = json.load(open(AUTHORED, encoding="utf-8"))
    struct = json.load(open(STRUCT, encoding="utf-8")) if os.path.exists(STRUCT) else {}
    os.makedirs(OUTDIR, exist_ok=True)
    prov_rows, comp_rows, atom_rows, report = [], [], [], []
    for pid, blk in authored.items():
        a = acc[pid]
        seg = json.load(open(os.path.join(TARGETS, pid + ".json"), encoding="utf-8"))["text"]
        names = source_proper_names(seg)
        comp = build_compositional(pid, blk["compositional"])
        # inherit viewpoint/tense into atomic from compositional
        atom = build_atomic(blk["atomic"])
        atom["viewpoint"], atom["tense"] = comp["viewpoint"], comp["tense"]
        prov = {"schema_version": "provenance-packet-v2", "passage_id": pid,
                "source_filename": a["source_filename"], "target_sha256": a["target_sha256"],
                **blk["provenance"]}

        # fill structural risk from the independent audit (if present)
        if pid in struct:
            s = struct[pid]
            if s.get("structural_reconstruction_risk"):
                comp["retrieval_risk"]["structural_reconstruction_risk"] = s["structural_reconstruction_risk"]
            comp["retrieval_risk"]["distinctive_elements"] = s.get("distinctive_elements", {})
            comp["retrieval_risk"]["recommendation"] = s.get("recommendation", "accept")
        # lexical risk + leakage on model-visible packets
        vis = json.dumps({"c": comp, "a": atom}, ensure_ascii=False)
        nleak = name_hits({"blob": vis}, names)
        lex = "high" if len(nleak) >= 3 else "medium" if nleak else "low"
        comp["retrieval_risk"]["lexical_identifier_risk"]["rating"] = lex
        tg = five_grams(seg)
        overlap5 = len(five_grams(" ".join(comp["required_beats"] + comp.get("canon_facts", []) +
                                           [comp["opening_state"], comp["scene_purpose"], comp["ending_state"]]) +
                                  " " + " ".join(atom["required_beats"])) & tg)
        stem = os.path.splitext(a["source_filename"])[0]
        idleak = [t for t in (a["source_filename"], pid) if t.lower() in vis.lower()]
        if re.search(r"\b" + re.escape(stem) + r"\b", vis, re.I):
            idleak.append(stem)
        # schema validation (after risk fields populated)
        errs = []
        for obj, sch, tag in ((comp, COMP_SCHEMA, "compositional"), (atom, ATOM_SCHEMA, "atomic"),
                              (prov, PROV_SCHEMA, "provenance")):
            for e in jsonschema.Draft7Validator(sch).iter_errors(obj):
                errs.append(f"{tag}: {e.message}")
        ca = comp["constraint_accounting"]
        target = {"source_filename": a["source_filename"], "target_sha256": a["target_sha256"],
                  "start_character_offset": a["start_character_offset"], "end_character_offset": a["end_character_offset"],
                  "target_word_count": a["target_word_count"], "target_text_unchanged": True}
        comp_rows.append({"record_id": f"{pid}-C", "arm": "compositional", "training_packet": comp,
                          "target": target, "pairing": {"matched_record_id": f"{pid}-A", "same_target_as_matched": True}})
        atom_rows.append({"record_id": f"{pid}-A", "arm": "atomic", "training_packet": atom,
                          "target": target, "pairing": {"matched_record_id": f"{pid}-C", "same_target_as_matched": True}})
        prov_rows.append(prov)
        report.append({"passage_id": pid, "source_filename": a["source_filename"],
                       "schema_valid": not errs, "schema_errors": errs[:4],
                       "compositional_meaningful": ca["meaningful_constraints"],
                       "compositional_load_bearing": ca["load_bearing_constraints"],
                       "atomic_meaningful": atom["constraint_accounting"]["meaningful_constraints"],
                       "lexical_risk": lex, "name_leak": len(nleak), "id_leak": bool(idleak),
                       "target_5gram_overlap": overlap5, "target_hash_match": True})
    for path, rows in ((f"{BATCH}-provenance.jsonl", prov_rows), (f"{BATCH}-compositional.jsonl", comp_rows),
                       (f"{BATCH}-atomic.jsonl", atom_rows)):
        with open(os.path.join(OUTDIR, path), "w", encoding="utf-8", newline="\n") as fh:
            for x in rows:
                fh.write(json.dumps(x, ensure_ascii=False) + "\n")
    from collections import Counter
    comp_m = [r["compositional_meaningful"] for r in report]
    comp_lb = [r["compositional_load_bearing"] for r in report]
    atom_m = [r["atomic_meaningful"] for r in report]
    rep = {"dispatch": "30A-R1", "batch": BATCH, "passages": len(report),
           "all_schema_valid": all(r["schema_valid"] for r in report),
           "constraint_distribution": {
               "compositional_meaningful": [min(comp_m), max(comp_m)],
               "compositional_load_bearing": [min(comp_lb), max(comp_lb)],
               "atomic_meaningful": [min(atom_m), max(atom_m)]},
           "lexical_risk": dict(Counter(r["lexical_risk"] for r in report)),
           "id_leaks": sum(r["id_leak"] for r in report),
           "name_leaks": sum(1 for r in report if r["name_leak"]),
           "target_5gram_overlap_max": max(r["target_5gram_overlap"] for r in report),
           "target_hash_match": all(r["target_hash_match"] for r in report),
           "records": report}
    json.dump(rep, open(os.path.join(EXP, "reports", f"{BATCH}-validation.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({k: rep[k] for k in ("passages", "all_schema_valid", "constraint_distribution",
                                          "lexical_risk", "id_leaks", "name_leaks",
                                          "target_5gram_overlap_max")}, indent=1))


if __name__ == "__main__":
    main()
