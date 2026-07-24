"""Dispatch 30A-R1 — ingest packet-review decisions and assign the two structural-risk cohorts.

Primary instruction-learning cohort = low + medium structural risk. Retrieval-sensitive cohort =
explicitly-approved high. The independent structural rating is PRESERVED after human acceptance
(human acceptance is a disposition, not a risk downgrade); accepted-high records carry
human_override=true. Contradictory (rating, decision) pairs are REFUSED and reported, never assigned.
Risk provenance (original + post-revision independent ratings) is kept separate, not collapsed.
If no decisions export is present, reports the PROVISIONAL split from the ratings alone.
Prints metadata only; per-passage reasons stay private.

Usage: py apply_packet_decisions.py [batch1rev]
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
BATCH = sys.argv[1] if len(sys.argv) > 1 else "batch1rev"
BASE = BATCH.replace("rev", "")  # batch1rev -> batch1 (for the original recal audit)
RISK = os.path.join(EXP, "private-data", f"structural-risk-{BATCH}.json")          # post-revision (current)
RECAL = os.path.join(EXP, "private-data", f"structural-risk-{BASE}-recal.json")    # original, same calibration
AUDITOR_CALIBRATION = "agent-B same-calibration (recal on original + audit on revised)"
for cand in (os.path.join(EXP, "private-data", "packet-viewer", f"packet-decisions-{BATCH}.json"),
             os.path.join(EXP, "private-data", f"packet-review-{BATCH}", f"packet-decisions-{BATCH}.json")):
    DEC = cand
    if os.path.exists(cand):
        break
OUTPRIV = os.path.join(EXP, "private-data", f"cohort-assignment-{BATCH}.json")

ACCEPT_REQUIRES = {"accept": "low", "accept_with_medium_risk": "medium",
                   "accept_as_retrieval_sensitive": "high"}
REVISE = ("revise_compositional", "revise_atomic", "revise_both", "revise_provenance")


def rating_of(store, pid):
    return (store.get(pid, {}).get("structural_reconstruction_risk") or {}).get("rating")


def classify(rating, decision):
    """Return (cohort, human_override, contradictory)."""
    if not decision:
        return "unresolved:undecided", None, False
    if decision == "exclude":
        return "excluded", None, False
    if decision in REVISE:
        return "unresolved:pending_revision", None, False
    if decision in ACCEPT_REQUIRES:
        if rating != ACCEPT_REQUIRES[decision]:
            return "contradictory", None, True   # refused: e.g. high + accept_with_medium_risk
        if decision == "accept":
            return "primary_low", None, False
        if decision == "accept_with_medium_risk":
            return "primary_medium", None, False
        return "retrieval_sensitive_high", True, False   # accept_as_retrieval_sensitive, rating stays high
    return "unresolved:undecided", None, False


def main():
    risk = json.load(open(RISK, encoding="utf-8"))
    recal = json.load(open(RECAL, encoding="utf-8")) if os.path.exists(RECAL) else {}
    dec = json.load(open(DEC, encoding="utf-8")).get("decisions", {}) if os.path.exists(DEC) else {}
    reviewed = bool(dec)
    assign = {}
    for pid in risk:
        r = rating_of(risk, pid)                 # current (post-revision) independent rating
        orig = rating_of(recal, pid)             # original independent rating (same calibration)
        d = (dec.get(pid, {}) or {}).get("decision", "") if reviewed else ""
        if not reviewed:
            cohort = "retrieval_sensitive_high" if r == "high" else \
                ("primary_medium" if r == "medium" else "primary_low")
            override, contra = None, False
        else:
            cohort, override, contra = classify(r, d)
        assign[pid] = {
            "decision": d or "(pre-review)",
            "cohort": cohort,
            "human_override": override,
            "contradictory": contra,
            "risk_provenance": {
                "original_independent_rating": orig,
                "post_revision_independent_rating": r,
                "auditor_calibration": AUDITOR_CALIBRATION,
                "human_disposition": d or "(pre-review)",
                "final_cohort": cohort,
            },
        }
    json.dump({"batch": BATCH, "reviewed": reviewed, "assignment": assign},
              open(OUTPRIV, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    cohorts = Counter(v["cohort"] for v in assign.values())
    unresolved = sum(c for k, c in cohorts.items() if k.startswith("unresolved") or k == "contradictory")
    ca = {"primary_low": cohorts.get("primary_low", 0),
          "primary_medium": cohorts.get("primary_medium", 0),
          "retrieval_sensitive_high": cohorts.get("retrieval_sensitive_high", 0),
          "excluded": cohorts.get("excluded", 0),
          "unresolved": unresolved}
    # risk_disposition, keyed by CURRENT independent rating (only meaningful once reviewed)
    def cur(pid):
        return rating_of(risk, pid)
    rd = {"medium_accepted": 0, "high_explicitly_accepted": 0, "high_revised": 0,
          "high_excluded": 0, "contradictory_decisions": 0} if not reviewed else {
        "medium_accepted": sum(1 for p, v in assign.items()
                               if cur(p) == "medium" and v["cohort"] == "primary_medium"),
        "high_explicitly_accepted": sum(1 for p, v in assign.items()
                                        if cur(p) == "high" and v["cohort"] == "retrieval_sensitive_high"),
        "high_revised": sum(1 for p, v in assign.items()
                            if cur(p) == "high" and v["cohort"] == "unresolved:pending_revision"),
        "high_excluded": sum(1 for p, v in assign.items()
                             if cur(p) == "high" and v["cohort"] == "excluded"),
        "contradictory_decisions": sum(1 for v in assign.values() if v["contradictory"]),
    }
    report = {"dispatch": "30A-R1", "batch": BATCH, "reviewed": reviewed,
              "cohort_assignment": ca, "risk_disposition": rd,
              "structural_rating_preserved": True,
              "human_overrides": sum(1 for v in assign.values() if v["human_override"]),
              "note": ("primary = low+medium; retrieval-sensitive = explicitly-approved high; "
                       "high never silently in primary; independent rating preserved after acceptance; "
                       "contradictory (rating, decision) pairs refused, not assigned.")}
    json.dump(report, open(os.path.join(EXP, "reports", f"cohort-assignment-{BATCH}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"reviewed": reviewed, "cohort_assignment": ca, "risk_disposition": rd}, indent=1))


if __name__ == "__main__":
    main()
