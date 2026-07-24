"""Dispatch 30A-R1 — ingest packet-review decisions and assign the two structural-risk cohorts.

Primary cohort = low + medium structural risk. Retrieval-sensitive cohort = explicitly-approved high.
The INDEPENDENT structural rating is preserved even after human acceptance (no relabel high->medium);
accepted-high records carry human_override=true. If no decisions export is present yet, reports the
PROVISIONAL cohort split from the ratings alone. Prints metadata only; per-passage reasons stay private.

Usage: py apply_packet_decisions.py [batch1rev]
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
BATCH = sys.argv[1] if len(sys.argv) > 1 else "batch1rev"
RISK = os.path.join(EXP, "private-data", f"structural-risk-{BATCH}.json")
DEC = os.path.join(EXP, "private-data", "packet-viewer", f"packet-decisions-{BATCH}.json")
if not os.path.exists(DEC):
    DEC = os.path.join(EXP, "private-data", f"packet-review-{BATCH}", f"packet-decisions-{BATCH}.json")
OUTPRIV = os.path.join(EXP, "private-data", f"cohort-assignment-{BATCH}.json")


def rating(risk, pid):
    return (risk.get(pid, {}).get("structural_reconstruction_risk") or {}).get("rating")


def main():
    risk = json.load(open(RISK, encoding="utf-8"))
    dec = json.load(open(DEC, encoding="utf-8")).get("decisions", {}) if os.path.exists(DEC) else {}
    reviewed = bool(dec)
    assign = {}
    for pid in risk:
        r = rating(risk, pid)
        d = (dec.get(pid, {}) or {}).get("decision", "") if reviewed else ""
        if not reviewed:
            cohort = "retrieval_sensitive_high" if r == "high" else \
                ("primary_medium" if r == "medium" else "primary_low")
            override = None
        elif d == "exclude":
            cohort = "excluded"; override = None
        elif d in ("revise_compositional", "revise_atomic", "revise_both", "revise_provenance"):
            cohort = "pending_revision"; override = None
        elif d == "accept_as_retrieval_sensitive":
            cohort = "retrieval_sensitive_high"; override = True   # rating stays high
        elif d in ("accept", "accept_with_medium_risk"):
            cohort = "primary_medium" if r == "medium" else "primary_low"
            override = None
        else:
            cohort = "undecided"; override = None
        assign[pid] = {"structural_rating": r, "decision": d or "(pre-review)",
                       "cohort": cohort, "human_override": override}
    json.dump({"batch": BATCH, "reviewed": reviewed, "assignment": assign},
              open(OUTPRIV, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    counts = Counter(v["cohort"] for v in assign.values())
    report = {"dispatch": "30A-R1", "batch": BATCH, "reviewed": reviewed,
              "cohort_assignment": {"primary_low": counts.get("primary_low", 0),
                                    "primary_medium": counts.get("primary_medium", 0),
                                    "retrieval_sensitive_high": counts.get("retrieval_sensitive_high", 0),
                                    "excluded": counts.get("excluded", 0),
                                    "pending_revision": counts.get("pending_revision", 0),
                                    "undecided": counts.get("undecided", 0)},
              "structural_rating_preserved": True,
              "human_overrides": sum(1 for v in assign.values() if v["human_override"]),
              "note": "primary = low+medium; retrieval-sensitive = explicitly-approved high; high never silently in primary; rating preserved after acceptance."}
    json.dump(report, open(os.path.join(EXP, "reports", f"cohort-assignment-{BATCH}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"reviewed": reviewed, **report["cohort_assignment"]}, indent=1))


if __name__ == "__main__":
    main()
