"""Mechanical evaluation gates for LineWright checkpoints (Dispatch 21, Phase E).

The Dispatch-20 smoke runs proved that a single ``format_valid`` (parse-only) check
is dangerously insufficient: a 20-step checkpoint emitted ``"The door creaks"`` forty
times and the evaluator scored it ``format_valid = true`` because non-empty prose
parses. These validators exist to reject obviously unusable output *without* requiring
subjective prose review, and to keep the gate dimensions SEPARATE (never collapsed into
one boolean) so a regression in one behavior is visible.

Every validator returns a :class:`GateResult`: a boolean verdict, a list of controlled
``failure_labels`` (see ``datasets/dataset-a/schema/enums.yaml`` plus the Dispatch-21
mechanical extensions), and an ``evidence`` mapping with the measured quantities that
produced the verdict. Validators report evidence, not just a boolean — a reviewer must
be able to see *why* something failed.

``behavioral_valid`` is deliberately NOT produced here: prose quality / usefulness is a
reviewer judgement (Phase G), never a mechanical gate. The aggregator leaves it ``None``.
"""
from dataclasses import dataclass, field, asdict


@dataclass
class GateResult:
    """One gate dimension's verdict.

    ``valid`` is tri-state: ``True`` / ``False`` for a machine-decidable check, or
    ``None`` when the check does not apply to this record (e.g. no-change validation on a
    record that is not a no-change case) or is reviewer-assisted. ``None`` must never be
    silently treated as a pass.
    """
    name: str
    valid: object = None            # True | False | None (not-applicable / reviewer-assisted)
    failure_labels: list = field(default_factory=list)
    evidence: dict = field(default_factory=dict)

    def as_dict(self):
        return asdict(self)


# Mechanical failure labels introduced by Dispatch 21 that the craft-focused
# ``failure_label`` enum in the dataset schema does not cover. The Opus teacher never
# produces these, so no rejected example taught them — which is precisely why the tiny
# 20-step checkpoints degenerated undetected.
MECHANICAL_FAILURE_LABELS = [
    # format / schema / protocol
    "invalid_json", "invalid_yaml", "prose_outside_structure", "markdown_fence_violation",
    "truncated_structure", "missing_required_key", "forbidden_extra_key",
    "alternate_key_names", "wrong_value_type", "wrong_container_shape", "null_policy_violation",
    "no_change_wrapper_missing", "wrong_changed_flag", "exact_preservation_failure",
    "explanation_when_output_only_required", "continued_after_task_complete",
    # repetition / degeneration
    "duplicate_sentence", "paraphrased_sentence_repeat", "repeated_fact",
    "repeated_paragraph_opening", "repeated_ngram", "circular_dialogue",
    "low_information_continuation", "low_lexical_diversity",
    "empty_output", "incomplete_output", "runaway_length", "generic_filler",
    # scope
    "unrelated_rewrite", "excessive_expansion", "omitted_required_change",
    "multiple_changes_when_one_requested", "summary_replacing_scene",
    # memorization
    "exact_gold_reproduction", "near_exact_gold_reproduction",
    "long_train_target_overlap", "source_family_leakage", "paraphrased_duplicate",
]

__all__ = ["GateResult", "MECHANICAL_FAILURE_LABELS"]
