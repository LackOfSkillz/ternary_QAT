"""Deterministic mechanical replay (Dispatch 23, Workstream A4/A5).

Every deterministic scorer is run at least twice on identical input. Identical booleans,
failure labels, evidence values, and defined ordering are required; a mismatch is an
INSTRUMENT failure that invalidates the run. A5: a run produces trusted findings only when
mechanical replay passed AND the calibration set is valid AND there are enough calibrated
reviewers; otherwise overall = insufficient_evidence and findings are quarantined.
"""
import hashlib
import json

from linewright.evaluation import GateResult


def _canonical(obj):
    def enc(o):
        if isinstance(o, GateResult):
            return {"valid": o.valid, "failure_labels": sorted(o.failure_labels),
                    "evidence": o.evidence, "name": o.name}
        if isinstance(o, dict):
            return {k: enc(o[k]) for k in sorted(o)}
        if isinstance(o, (list, tuple)):
            return [enc(x) for x in o]
        return o
    return json.dumps(enc(obj), sort_keys=True, ensure_ascii=False, default=str)


def result_hash(obj):
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def replay(validator_name, validator_version, fn, inp):
    """Run ``fn(inp)`` twice and compare canonical hashes. Returns an instrument-replay-result."""
    r1, r2 = fn(inp), fn(inp)
    h1, h2 = result_hash(r1), result_hash(r2)
    identical = h1 == h2
    differing = []
    if not identical:
        c1, c2 = json.loads(_canonical(r1)), json.loads(_canonical(r2))
        keys = set(c1) | set(c2) if isinstance(c1, dict) else set()
        differing = [k for k in keys if c1.get(k) != c2.get(k)]
    return {
        "schema": "instrument-replay-result",
        "validator_name": validator_name, "validator_version": validator_version,
        "input_hash": hashlib.sha256(_canonical(inp).encode("utf-8")).hexdigest(),
        "first_result_hash": h1, "replay_result_hash": h2,
        "identical": identical, "differing_fields": differing,
        "run_validity_consequence": "none" if identical else "invalidate_run",
    }


def replay_passed(replays):
    return bool(replays) and all(r["identical"] for r in replays)


def instrument_valid(replays, calibration_problems, reviewer_results, min_calibrated=1):
    """Aggregate the A5 instrument-valid rule."""
    from linewright.evaluation.calibration.reviewer import sufficient_calibrated_reviewers
    mech = replay_passed(replays)
    cal_ok = not calibration_problems
    reviewers_ok = sufficient_calibrated_reviewers(reviewer_results, min_calibrated)
    valid = mech and cal_ok and reviewers_ok
    return {
        "instrument_valid": valid,
        "mechanical_replay_passed": mech,
        "calibration_set_valid": cal_ok,
        "sufficient_calibrated_reviewers": reviewers_ok,
        "overall": "ok" if valid else "insufficient_evidence",
        "findings_status": "trusted" if valid else "quarantined",
    }
