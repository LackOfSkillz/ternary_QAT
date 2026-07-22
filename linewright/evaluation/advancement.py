"""Advancement rules (Dispatch 21, Phase H) — machine-checkable.

A checkpoint may reach Gary ONLY when every rule below holds. The rules are hard gates,
not a weighted average: a single fatal reviewer flag blocks advancement even if the other
two reviewers approve, and serious disagreement is surfaced for investigation rather than
averaged away.

Explicitly NOT reasons to advance (ignored by design, never accepted as inputs):
  - lower training loss,
  - a higher parse/format_valid rate,
  - winning a majority of a handful of records,
  - one impressive prose sample,
  - two reviewers approving while a third identifies a fatal flaw.
"""

REVIEWERS = ("aedan", "claude", "chatgpt")


def check_advancement(evidence):
    """Return ``{advance, blockers, needs_investigation, notes}``.

    ``evidence`` = {
        "mechanical_gates_pass": bool,
        "schema_regressions": int, "no_change_regressions": int,
        "memorization_flags": int, "material_regressions": int,
        "reviewers": {name: {"prefers_over_base": bool, "fatal_flaw": bool}},
    }
    """
    blockers, notes = [], []
    ev = evidence or {}

    if not ev.get("mechanical_gates_pass"):
        blockers.append("mechanical_gates_do_not_pass")
    for k in ("schema_regressions", "no_change_regressions", "memorization_flags",
              "material_regressions"):
        n = int(ev.get(k, 0) or 0)
        if n > 0:
            blockers.append(f"{k}={n} (must be 0)")

    reviewers = ev.get("reviewers", {}) or {}
    missing = [r for r in REVIEWERS if r not in reviewers]
    if missing:
        blockers.append(f"missing_reviewer_scores:{','.join(missing)}")

    fatal = [r for r in REVIEWERS if reviewers.get(r, {}).get("fatal_flaw")]
    if fatal:
        blockers.append(f"fatal_reviewer_flags:{','.join(fatal)}")

    prefers = {r: bool(reviewers.get(r, {}).get("prefers_over_base")) for r in REVIEWERS
               if r in reviewers}
    not_preferring = [r for r, p in prefers.items() if not p]
    if not_preferring:
        blockers.append(f"reviewers_not_preferring_over_base:{','.join(not_preferring)}")

    # disagreement is investigated, never averaged
    if prefers and (0 < sum(prefers.values()) < len(prefers)) or (fatal and len(fatal) < len(REVIEWERS)):
        notes.append("reviewer_disagreement_present — investigate the specific disagreement; "
                     "do NOT average scores to a pass")
        needs_investigation = True
    else:
        needs_investigation = False

    return {
        "advance": not blockers,
        "blockers": blockers,
        "needs_investigation": needs_investigation,
        "notes": notes,
    }


# Phase J — a new LoRA/QAT run may begin only when ALL of these are true.
READINESS_FLAGS = (
    "dataset_schema_valid", "all_records_static_valid", "behavior_coverage_approved",
    "source_family_split_clean", "story_world_split_clean", "duplicate_scan_clean",
    "memorization_scan_clean", "pilot_review_complete",
    "aedan_dataset_approval", "claude_dataset_approval", "chatgpt_dataset_approval",
)


def check_retraining_readiness(state):
    """Return ``{ready, blockers}``. Every READINESS_FLAG must be True (Phase J).

    A missing flag is treated as not-ready, never as a pass.
    """
    st = state or {}
    blockers = [f for f in READINESS_FLAGS if st.get(f) is not True]
    return {"ready": not blockers, "blockers": blockers}

