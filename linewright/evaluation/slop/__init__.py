"""Module J — Slop Detection and Stylistic Degradation (Dispatch 23).

Slop = undesirable writing behaviours (repetition, semantic redundancy, stock-phrase
concentration, voice flattening, generic explanatory endings, corpus-level sameness, ...).

This package is NOT an AI-authorship detector. It never collapses to one opaque score: it
reports deterministic, semantic (interface-only here), lexical/style, and reviewer evidence
separately, each with evidence spans and its own confidence. All numeric thresholds are
UNVALIDATED until calibration (a later dispatch); the only severity signal used now reuses
the already-justified Dispatch-21 repetition gate, and the report says so.

Design commitments (see training/docs/slop-detection-research-review-v1.md):
  - deterministic measures are diagnostic signals, not automatic gates;
  - deliberate repetition, concise prose, lyrical/unusual syntax, and genre motifs are NOT
    slop and must not be auto-flagged;
  - every finding retains verbatim evidence spans; a scalar without passages is insufficient;
  - short outputs are flagged and diversity metrics reported with that caveat.
"""

SUITE_VERSION = "slop-suite-v1"
THRESHOLD_STATUS = "unvalidated"

__all__ = ["SUITE_VERSION", "THRESHOLD_STATUS"]
