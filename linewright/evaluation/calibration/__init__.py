"""Instrument-calibration layer (Dispatch 23, Workstream A / Layer 1).

The battery validates ITSELF before it validates a model: hidden known-good / known-broken
grader-calibration records, deterministic mechanical replay, and reviewer-reliability
classification. If this layer fails, the run's model findings are quarantined and the overall
verdict is ``insufficient_evidence`` — never averaged through.
"""
INSTRUMENT_VALID_KEYS = ("mechanical_replay_passed", "calibration_set_valid",
                         "sufficient_calibrated_reviewers")
