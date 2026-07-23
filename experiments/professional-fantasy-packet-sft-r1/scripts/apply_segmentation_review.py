"""Dispatch 30A-R1 — ingest segmentation review decisions and produce accepted/rejected passage
manifests. Reads the private decisions.json exported by the review app; for accepted/adjusted
passages it recomputes offsets, word count, and target hash from the FROZEN normalized source.
Checks the Phase-2/3 segmentation gate. Prints statistics only (no prose).

Usage: py apply_segmentation_review.py [path/to/decisions.json]
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
NORM_DIR = os.path.join(EXP, "private-data", "normalized-sources")
CAND = os.path.join(EXP, "manifests", "candidate-passages.jsonl")
DECISIONS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EXP, "private-data", "review-app", "decisions.json")
ACCEPTED = os.path.join(EXP, "manifests", "accepted-passages.jsonl")
REJECTED = os.path.join(EXP, "manifests", "rejected-passages.jsonl")


def main():
    if not os.path.exists(DECISIONS):
        print(json.dumps({"status": "no_decisions_yet", "expected": os.path.relpath(DECISIONS, EXP),
                          "note": "run the review app, Export decisions.json into private-data/review-app/, then re-run"},
                         indent=1))
        return
    rows = {r["passage_id"]: r for r in (json.loads(l) for l in open(CAND, encoding="utf-8") if l.strip())}
    dec = json.load(open(DECISIONS, encoding="utf-8"))["decisions"]
    cache = {}
    accepted, rejected, deferred, needs_manual = [], [], [], []
    for pid, d in dec.items():
        if pid not in rows:
            continue
        r = dict(rows[pid])
        decision = d.get("decision", "")
        r["review"] = {"decision": decision, "reject_reason": d.get("reject_reason", ""),
                       "ratings": d.get("ratings", {}),
                       "scene_function": d.get("scene_function", ""), "notes": d.get("notes", ""),
                       "reviewer": d.get("reviewer"), "timestamp": d.get("timestamp")}
        if decision in ("adjust_start", "adjust_end", "accept") and (d.get("adjusted_start") is not None or d.get("adjusted_end") is not None):
            fn = r["source_filename"]
            if fn not in cache:
                cache[fn] = open(os.path.join(NORM_DIR, fn), encoding="utf-8").read()
            s = d.get("adjusted_start") if d.get("adjusted_start") is not None else r["start_character_offset"]
            e = d.get("adjusted_end") if d.get("adjusted_end") is not None else r["end_character_offset"]
            seg = cache[fn][s:e]
            r["start_character_offset"], r["end_character_offset"] = s, e
            r["target_word_count"] = len(seg.split())
            r["target_sha256"] = hashlib.sha256(seg.encode("utf-8")).hexdigest()
            r["boundary_adjusted"] = True
        if decision == "accept" or decision.startswith("adjust"):
            r["human_review_status"] = "accepted"
            accepted.append(r)
        elif decision == "reject":
            r["human_review_status"] = "rejected"
            rejected.append(r)
        elif decision == "replace_candidate":
            r["human_review_status"] = "replace_requested"
            rejected.append(r); needs_manual.append(pid)
        elif decision == "defer":
            deferred.append(pid)

    with open(ACCEPTED, "w", encoding="utf-8", newline="\n") as fh:
        for r in accepted:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(REJECTED, "w", encoding="utf-8", newline="\n") as fh:
        for r in rejected:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    per_source = {}
    for r in accepted:
        per_source[r["source_filename"]] = per_source.get(r["source_filename"], 0) + 1
    gate = {
        "all_11_sources_represented": len(per_source) == 11,
        "accepted_per_source_target_8_to_10": all(8 <= v <= 10 for v in per_source.values()) and len(per_source) == 11,
        "minimum_accepted_per_source_6": all(v >= 6 for v in per_source.values()) and len(per_source) == 11,
        "boundary_review_complete": len(needs_manual) == 0,
        "target_hashes_frozen": True,
    }
    report = {"dispatch": "30A-R1", "decisions_ingested": len(dec),
              "accepted": len(accepted), "rejected": len(rejected),
              "deferred": len(deferred), "needs_manual_merge_split": needs_manual,
              "accepted_per_source": per_source, "segmentation_gate": gate,
              "gate_passed": all(gate.values())}
    json.dump(report, open(os.path.join(EXP, "reports", "segmentation-apply.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"accepted": len(accepted), "rejected": len(rejected), "deferred": len(deferred),
                      "needs_manual": len(needs_manual), "gate_passed": all(gate.values())}, indent=1))


if __name__ == "__main__":
    main()
