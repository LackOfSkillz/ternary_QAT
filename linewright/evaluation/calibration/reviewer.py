"""Reviewer-reliability classification (Dispatch 23, Workstream A3).

Classifies a reviewer from their performance on the hidden calibration set:
``calibrated`` / ``conditionally_usable`` / ``unreliable_for_run``. The MECHANISM is
implemented; the numeric cutoffs are PROVISIONAL and clearly marked unvalidated — they are
tuned against real calibration data in a later dispatch. A reviewer classified
``unreliable_for_run`` contributes nothing to that run's model-quality findings.
"""
THRESHOLD_PROFILE_VERSION = "provisional_unvalidated-v1"

# Provisional cutoffs (status: provisional_unvalidated). Missing a fatal flaw on a
# known-broken item is the most serious error and caps the classification.
PROVISIONAL = {
    "status": "provisional_unvalidated",
    "calibrated": {"min_known_good_frac": 0.8, "min_known_broken_frac": 0.8, "max_fatal_missed": 0},
    "conditionally_usable": {"min_known_good_frac": 0.6, "min_known_broken_frac": 0.6, "max_fatal_missed": 1},
}


def classify(reviewer_id, run_id, scored_items, profile=None):
    """``scored_items`` = [{calibration_id, known_expected ('accept'|'reject'),
    reviewer_decision ('accept'|'reject'), fatal_flaw_expected(bool), fatal_flaw_caught(bool)}].

    Returns a reviewer-calibration result dict (benchmarks/schemas/reviewer-calibration-schema.yaml).
    """
    prof = profile or PROVISIONAL
    kg = [s for s in scored_items if s["known_expected"] == "accept"]
    kb = [s for s in scored_items if s["known_expected"] == "reject"]
    kg_correct = sum(1 for s in kg if s["reviewer_decision"] == "accept")
    kb_correct = sum(1 for s in kb if s["reviewer_decision"] == "reject")
    false_accepts = sum(1 for s in kb if s["reviewer_decision"] == "accept")
    false_rejects = sum(1 for s in kg if s["reviewer_decision"] == "reject")
    fatal_missed = sum(1 for s in kb if s.get("fatal_flaw_expected") and not s.get("fatal_flaw_caught"))

    kg_frac = kg_correct / len(kg) if kg else 1.0
    kb_frac = kb_correct / len(kb) if kb else 1.0

    c = prof["calibrated"]
    cu = prof["conditionally_usable"]
    if (kg_frac >= c["min_known_good_frac"] and kb_frac >= c["min_known_broken_frac"]
            and fatal_missed <= c["max_fatal_missed"]):
        cls, basis = "calibrated", "meets provisional calibrated cutoffs"
    elif (kg_frac >= cu["min_known_good_frac"] and kb_frac >= cu["min_known_broken_frac"]
          and fatal_missed <= cu["max_fatal_missed"]):
        cls, basis = "conditionally_usable", "meets provisional conditional cutoffs"
    else:
        cls, basis = "unreliable_for_run", "below provisional conditional cutoffs or missed a fatal flaw"

    return {
        "schema": "reviewer-calibration", "reviewer_id": reviewer_id, "run_id": run_id,
        "calibration_items": [s["calibration_id"] for s in scored_items],
        "known_good_total": len(kg), "known_good_correct": kg_correct,
        "known_broken_total": len(kb), "known_broken_correct": kb_correct,
        "caught_known_good": kg_correct, "caught_known_broken": kb_correct,
        "false_accepts": false_accepts, "false_rejects": false_rejects,
        "fatal_flaws_missed": fatal_missed,
        "classification": cls, "classification_basis": basis,
        "threshold_profile_version": THRESHOLD_PROFILE_VERSION,
    }


def usable_reviewers(results):
    """Reviewers whose scores may contribute to model-quality findings (not unreliable)."""
    return [r["reviewer_id"] for r in results if r["classification"] != "unreliable_for_run"]


def sufficient_calibrated_reviewers(results, minimum=1):
    """At least ``minimum`` reviewers classified ``calibrated`` (provisional gate)."""
    n = sum(1 for r in results if r["classification"] == "calibrated")
    return n >= minimum
