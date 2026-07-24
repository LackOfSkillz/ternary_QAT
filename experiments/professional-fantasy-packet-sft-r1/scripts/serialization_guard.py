"""Dispatch 30F — training-serialization contamination guard.

Any future full-dataset / SFT serializer MUST call assert_training_safe() on the records it is about
to emit. It fails LOUDLY (raises HeldoutContaminationError) if a held-out evaluation record leaks into
training output — split == 'heldout_eval' or training_eligible is False. This makes the c01 held-out
set impossible to silently serialize into SFT data.

Contract (freeze/heldout-split-policy.yaml):
  reject_split: [heldout_eval]
  reject_training_eligible_false: true
  on_violation: raise
"""

REJECT_SPLITS = frozenset({"heldout_eval"})


class HeldoutContaminationError(RuntimeError):
    """Raised when a held-out / non-training-eligible record reaches a training serializer."""


def _flags(rec):
    """A record may carry flags at top level or under a 'split_meta'/'meta' block."""
    for key in ("split_meta", "meta"):
        if isinstance(rec.get(key), dict):
            return rec[key]
    return rec


def is_training_safe(rec):
    """True iff rec is eligible for SFT training output."""
    f = _flags(rec)
    if f.get("split") in REJECT_SPLITS:
        return False
    if f.get("training_eligible") is False:
        return False
    return True


def assert_training_safe(records, context="training serialization"):
    """Raise HeldoutContaminationError if ANY record is a held-out / non-training-eligible record.

    `records` is an iterable of dicts. Call this in every training/full-dataset serializer BEFORE
    writing SFT output. Never catch-and-drop: contamination must be a hard failure.
    """
    bad = []
    for i, rec in enumerate(records):
        if not is_training_safe(rec):
            f = _flags(rec)
            bad.append((rec.get("record_id") or rec.get("passage_id") or f"index_{i}",
                        f.get("split"), f.get("training_eligible")))
    if bad:
        detail = "; ".join(f"{rid} (split={sp}, training_eligible={te})" for rid, sp, te in bad[:20])
        raise HeldoutContaminationError(
            f"{context}: {len(bad)} held-out/non-training-eligible record(s) reached the training "
            f"serializer and were REJECTED (Dispatch 30F guard): {detail}")
    return True


if __name__ == "__main__":
    # self-test
    safe = [{"record_id": "x-c03-C", "split": "batch", "training_eligible": True}]
    held = [{"record_id": "abercrombe-c01-C", "split": "heldout_eval", "training_eligible": False}]
    assert_training_safe(safe)
    try:
        assert_training_safe(safe + held)
        print("FAIL: guard did not raise")
    except HeldoutContaminationError as e:
        print("OK guard raised:", str(e)[:80], "...")
