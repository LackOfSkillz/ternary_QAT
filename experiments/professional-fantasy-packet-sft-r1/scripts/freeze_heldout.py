"""Dispatch 30F — freeze the c01 HELD-OUT evaluation set (private) + emit eval-ready records.

Assembles the 11 c01 pairs into a PRIVATE held-out manifest carrying the permanent split flags,
evaluation cohorts, and evaluation dispositions (NEVER training dispositions). Also writes
private eval-ready jsonl under private-data/eval/. Emits a COMMITTED metadata-only report.

Usage: py freeze_heldout.py
"""
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
PD = os.path.join(EXP, "private-data")
TP = os.path.join(PD, "training-packets")
EVAL = os.path.join(PD, "eval")
BATCH = "heldc01"                      # internal tooling name; SET_ID is the real identity
SET_ID = "heldout-c01"

EVAL_COHORT = {"low": "heldout_low", "medium": "heldout_medium", "high": "heldout_retrieval_sensitive"}
EVAL_DISPOSITION = {"low": "include_in_heldout_eval",
                    "medium": "include_in_heldout_eval_with_medium_risk",
                    "high": "include_in_heldout_retrieval_probe"}


def load_jsonl(path, key):
    return {json.loads(l)[key]: json.loads(l) for l in open(path, encoding="utf-8") if l.strip()}


def main():
    comp = load_jsonl(os.path.join(TP, f"{BATCH}-compositional.jsonl"), "record_id")
    atom = load_jsonl(os.path.join(TP, f"{BATCH}-atomic.jsonl"), "record_id")
    prov = load_jsonl(os.path.join(TP, f"{BATCH}-provenance.jsonl"), "passage_id")
    tok = json.load(open(os.path.join(PD, f"tokcount-output-{BATCH}rev.json"), encoding="utf-8"))
    riskrev = json.load(open(os.path.join(PD, f"structural-risk-{BATCH}rev.json"), encoding="utf-8"))
    recal = json.load(open(os.path.join(PD, f"structural-risk-{BATCH}-recal.json"), encoding="utf-8"))
    purity = json.load(open(os.path.join(PD, f"atomic-purity-{BATCH}.json"), encoding="utf-8"))
    serial = json.load(open(os.path.join(EXP, "freeze", "serializer-version.json"), encoding="utf-8"))
    model = json.load(open(os.path.join(EXP, "freeze", "model-revision.json"), encoding="utf-8"))

    FLAGS = {"split": "heldout_eval", "training_eligible": False, "evaluation_eligible": True,
             "retrieval_safety_probe": True, "decision_authority": "Dispatch 30F", "set_id": SET_ID}

    os.makedirs(EVAL, exist_ok=True)
    pairs, checks = [], Counter()
    ecomp, eatom, etgt = [], [], []
    for pid in prov:
        cid, aid = f"{pid}-C", f"{pid}-A"
        c, a = comp[cid], atom[aid]
        rating = (riskrev[pid]["structural_reconstruction_risk"] or {}).get("rating")
        orig = (recal.get(pid, {}).get("structural_reconstruction_risk") or {}).get("rating")
        matched = (c["pairing"]["matched_record_id"] == aid
                   and c["target"]["target_sha256"] == a["target"]["target_sha256"])
        checks["matched_pairs"] += 1 if matched else 0
        checks["target_hash_mismatches"] += 0 if c["target"]["target_sha256"] == a["target"]["target_sha256"] else 1
        for rec in (cid, aid):
            checks["context_overflows"] += 0 if tok.get(rec, {}).get("fits_8192") else 1
        pairs.append({
            "passage_id": pid, "set_id": SET_ID, **FLAGS,
            "evaluation_cohort": EVAL_COHORT.get(rating), "evaluation_disposition": EVAL_DISPOSITION.get(rating),
            "target": c["target"],                       # unchanged target (offsets/hash, PRIVATE)
            "provenance_packet": prov[pid], "compositional_packet": c["training_packet"],
            "atomic_packet": a["training_packet"],
            "original_structural_rating": orig, "post_revision_structural_rating": rating,
            "atomic_purity": purity.get(pid, {}).get("verdict"),
            "tokens": {"compositional": tok.get(cid), "atomic": tok.get(aid)},
            "schema_version": {"compositional": c["training_packet"]["packet_version"],
                               "atomic": a["training_packet"]["packet_version"],
                               "provenance": prov[pid].get("schema_version")},
            "serializer_version": serial["serializer_version"], "model_revision": model["exact_revision"],
        })
        # eval-ready records (private) — each carries the split flags so any consumer sees them
        ecomp.append({"record_id": cid, **FLAGS, "arm": "compositional",
                      "training_packet": c["training_packet"], "target": c["target"]})
        eatom.append({"record_id": aid, **FLAGS, "arm": "atomic",
                      "training_packet": a["training_packet"], "target": a["target"]})
        seg = json.load(open(os.path.join(PD, "targets", pid + ".json"), encoding="utf-8"))["text"]
        etgt.append({"passage_id": pid, **FLAGS, "target_sha256": c["target"]["target_sha256"], "target": seg})

    cohorts = Counter(p["evaluation_cohort"] for p in pairs)
    manifest = {"set_id": SET_ID, "records": len(pairs), "training_eligible": 0,
                "evaluation_eligible": len(pairs),
                "evaluation_cohorts": {"heldout_low": cohorts.get("heldout_low", 0),
                                       "heldout_medium": cohorts.get("heldout_medium", 0),
                                       "heldout_retrieval_sensitive": cohorts.get("heldout_retrieval_sensitive", 0)},
                "serializer_version": serial["serializer_version"], "model_revision": model["exact_revision"],
                "pairs": pairs}
    json.dump(manifest, open(os.path.join(PD, f"{SET_ID}-manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    for path, rows in ((f"{SET_ID}-compositional.jsonl", ecomp), (f"{SET_ID}-atomic.jsonl", eatom),
                       (f"{SET_ID}-targets.jsonl", etgt)):
        with open(os.path.join(EVAL, path), "w", encoding="utf-8", newline="\n") as fh:
            for x in rows:
                fh.write(json.dumps(x, ensure_ascii=False) + "\n")
    json.dump(manifest, open(os.path.join(EVAL, f"{SET_ID}-manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"set_id": SET_ID, "records": len(pairs),
                      "evaluation_cohorts": manifest["evaluation_cohorts"],
                      "matched_pairs": checks["matched_pairs"], "hash_mismatches": checks["target_hash_mismatches"],
                      "context_overflows": checks["context_overflows"],
                      "eval_files": [f"eval/{SET_ID}-{s}.jsonl" for s in ("compositional", "atomic", "targets")]},
                     indent=1))


if __name__ == "__main__":
    main()
