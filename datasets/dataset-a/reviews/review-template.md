# Dataset A — Review record (template)
#
# Copy this file to reviews/<record-id>.review.md and fill it in. Reviews are the
# audit trail for promotion. No script promotes a record; promotion follows a
# completed review. Do not edit the source record's review_status to an approved
# value without a corresponding accepted review here.

record_id:            # e.g. dsa-revision-001
decision:             # one of: accept | needs_revision | reject | escalate_to_gary
requested_corrections:
  -                   # specific, actionable
ambiguity_notes:
  -                   # anything under-specified in instruction/context/gold
duplicate_risk_notes:
  -                   # near-duplicate of which record(s), and how it differs
voice_preservation_judgment:   # does the gold preserve the source voice? evidence
craft_label_accuracy:          # are craft_targets / failure_modes correct? Tier B = estimate
gold_answer_defensibility:     # is the gold the preferred minimal correction? why
reviewer:             # name/initials
review_date:          # YYYY-MM-DD (absolute)

## Narrative notes

(Free-form reviewer discussion. Cite specific lines. For Tier B labels, state the
uncertainty explicitly.)
