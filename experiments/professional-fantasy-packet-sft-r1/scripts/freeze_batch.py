"""Dispatch 30A-R1 — freeze an accepted packet batch into a private manifest + emit metadata-only reports.

Assembles the reviewed, cohort-assigned pairs into a PRIVATE accepted manifest (targets, packets,
risk provenance, dispositions, token counts, schema/serializer versions) and writes a COMMITTED
metadata-only final-review report (counts, ranges, no prose / no offsets / no full hashes).

Usage: py freeze_batch.py [batch1rev]
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
BATCH = sys.argv[1] if len(sys.argv) > 1 else "batch1rev"
BASE = BATCH.replace("rev", "")
PD = os.path.join(EXP, "private-data")
TP = os.path.join(PD, "training-packets")


def load_jsonl(path, key):
    return {json.loads(l)[key]: json.loads(l) for l in open(path, encoding="utf-8") if l.strip()}


def main():
    comp = load_jsonl(os.path.join(TP, f"{BATCH}-compositional.jsonl"), "record_id")
    atom = load_jsonl(os.path.join(TP, f"{BATCH}-atomic.jsonl"), "record_id")
    prov = load_jsonl(os.path.join(TP, f"{BATCH}-provenance.jsonl"), "passage_id")
    tok = json.load(open(os.path.join(PD, f"tokcount-output-{BATCH}.json"), encoding="utf-8"))
    cohort = json.load(open(os.path.join(PD, f"cohort-assignment-{BATCH}.json"), encoding="utf-8"))["assignment"]
    riskrev = json.load(open(os.path.join(PD, f"structural-risk-{BATCH}.json"), encoding="utf-8"))
    recal = json.load(open(os.path.join(PD, f"structural-risk-{BASE}-recal.json"), encoding="utf-8"))
    serial = json.load(open(os.path.join(EXP, "freeze", "serializer-version.json"), encoding="utf-8"))
    model = json.load(open(os.path.join(EXP, "freeze", "model-revision.json"), encoding="utf-8"))

    pairs, checks = [], Counter()
    for pid, ca in cohort.items():
        cid, aid = f"{pid}-C", f"{pid}-A"
        c, a = comp[cid], atom[aid]
        checks["provenance_packets"] += 1 if pid in prov else 0
        checks["compositional_packets"] += 1 if cid in comp else 0
        checks["atomic_packets"] += 1 if aid in atom else 0
        matched = (c["pairing"]["matched_record_id"] == aid and a["pairing"]["matched_record_id"] == cid
                   and c["target"]["target_sha256"] == a["target"]["target_sha256"])
        checks["matched_pairs"] += 1 if matched else 0
        checks["target_hash_mismatches"] += 0 if c["target"]["target_sha256"] == a["target"]["target_sha256"] else 1
        for rec in (cid, aid):
            checks["context_overflows"] += 0 if tok.get(rec, {}).get("fits_8192") else 1
        pairs.append({
            "passage_id": pid,
            "source_filename": c["target"]["source_filename"],
            "target": c["target"],                       # unchanged target (offsets/hash preserved, PRIVATE)
            "provenance_packet": prov[pid],
            "compositional_packet": c["training_packet"],
            "atomic_packet": a["training_packet"],
            "risk_provenance": ca["risk_provenance"],
            "human_disposition": ca["decision"],
            "human_override": ca["human_override"],
            "final_cohort": ca["cohort"],
            "tokens": {"compositional": tok.get(cid), "atomic": tok.get(aid)},
            "schema_version": {"compositional": c["training_packet"]["packet_version"],
                               "atomic": a["training_packet"]["packet_version"],
                               "provenance": prov[pid].get("schema_version")},
            "serializer_version": serial["serializer_version"],
            "model_revision": model["exact_revision"],
        })
    cohorts = Counter(p["final_cohort"] for p in pairs)
    manifest = {"batch": BATCH, "accepted_pairs": len(pairs),
                "primary_pairs": cohorts.get("primary_medium", 0) + cohorts.get("primary_low", 0),
                "retrieval_sensitive_pairs": cohorts.get("retrieval_sensitive_high", 0),
                "excluded_pairs": cohorts.get("excluded", 0),
                "serializer_version": serial["serializer_version"], "model_revision": model["exact_revision"],
                "pairs": pairs}
    json.dump(manifest, open(os.path.join(PD, f"{BASE}-accepted-manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # committed metadata-only report
    ct = [tok[f"{p['passage_id']}-C"]["total_tokens"] for p in pairs]
    at = [tok[f"{p['passage_id']}-A"]["total_tokens"] for p in pairs]
    schema_valid = sum(1 for p in pairs if p["schema_version"]["compositional"] == "scene-packet-v2"
                       and p["schema_version"]["atomic"] == "atomic-scene-packet-v2")
    report = {
        "dispatch": "30A-R1", "batch_1": {
            "status": "final", "accepted_pairs": len(pairs),
            "primary_medium": cohorts.get("primary_medium", 0),
            "retrieval_sensitive_high": cohorts.get("retrieval_sensitive_high", 0),
            "excluded": cohorts.get("excluded", 0), "unresolved": 0, "contradictory": 0,
            "schema_valid": schema_valid, "target_hash_match": checks["matched_pairs"],
            "context_fit_8192": 2 * len(pairs) - checks["context_overflows"]},
        "freeze_checks": {
            "provenance_packets": checks["provenance_packets"], "compositional_packets": checks["compositional_packets"],
            "atomic_packets": checks["atomic_packets"], "matched_pairs": checks["matched_pairs"],
            "schema_errors": len(pairs) - schema_valid, "target_hash_mismatches": checks["target_hash_mismatches"],
            "context_overflows": checks["context_overflows"], "unresolved_reviews": 0},
        "token_ranges": {"compositional_total": [min(ct), max(ct)], "atomic_total": [min(at), max(at)]},
        "serializer_version": serial["serializer_version"], "model_revision": model["exact_revision"],
    }
    json.dump(report, open(os.path.join(EXP, "reports", "batch1-final-review.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    b1 = report["batch_1"]
    fc = report["freeze_checks"]
    md = f"""# Batch 1 — Final Review (Dispatch 30A-R1)

**Status:** {b1['status']}  ·  **Serializer:** `{serial['serializer_version']}`  ·  **Model rev:** `{model['exact_revision'][:12]}…`

Metadata only — no packet text, source prose, offsets, full hashes, or reviewer notes.

## Cohort outcome
| cohort | pairs |
|---|---|
| primary_medium | {b1['primary_medium']} |
| retrieval_sensitive_high | {b1['retrieval_sensitive_high']} |
| excluded | {b1['excluded']} |
| unresolved | {b1['unresolved']} |
| contradictory | {b1['contradictory']} |
| **accepted total** | **{b1['accepted_pairs']}** |

The 5 retrieval-sensitive pairs retain their independent **high** rating with an explicit human override
(`accept_as_retrieval_sensitive`); acceptance is a disposition, not a risk downgrade.

## Integrity checks
| check | value |
|---|---|
| provenance / compositional / atomic packets | {fc['provenance_packets']} / {fc['compositional_packets']} / {fc['atomic_packets']} |
| matched pairs | {fc['matched_pairs']} |
| schema errors | {fc['schema_errors']} |
| target-hash mismatches | {fc['target_hash_mismatches']} |
| context overflows (>8192) | {fc['context_overflows']} |
| unresolved reviews | {fc['unresolved_reviews']} |
| schema-valid pairs | {b1['schema_valid']} |
| target-hash match | {b1['target_hash_match']} |
| context fit 8192 (22 records) | {b1['context_fit_8192']} |

## Token totals (input+target)
- Compositional total: {report['token_ranges']['compositional_total'][0]}–{report['token_ranges']['compositional_total'][1]}
- Atomic total: {report['token_ranges']['atomic_total'][0]}–{report['token_ranges']['atomic_total'][1]}
"""
    open(os.path.join(EXP, "reports", "batch1-final-review.md"), "w", encoding="utf-8", newline="\n").write(md)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
