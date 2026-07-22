"""Blind-scoring access separation (Dispatch 25, D7).

Blindness is enforced by ACCESS SEPARATION, not convention. Anonymous review artifacts live
under ``review/anonymous/``; the identity/unblinding keys live under a SEPARATE
``private-unblinding/`` root that scoring code never reads. Scores must be locked (hashed)
before any unblinding; unblinding refuses if the score-locks are absent. A reviewer process
that tries to open the identity key fails.
"""
import hashlib
import json
import os

PRIVATE_DIRNAME = "private-unblinding"
ANON_DIR = os.path.join("review", "anonymous")


class ScoreLockError(RuntimeError):
    pass


class UnblindError(RuntimeError):
    pass


class IdentityAccessError(RuntimeError):
    pass


def _w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)


def build_review_bundle(units, absolute_key, pairwise_key, review_root, private_root):
    """Write anonymous units + blank scoring forms under review_root/anonymous, and the keys
    under private_root. private_root MUST be outside review_root (separation invariant)."""
    if os.path.abspath(private_root).startswith(os.path.abspath(review_root) + os.sep):
        raise ValueError("private-unblinding must live OUTSIDE the review directory")
    anon = os.path.join(review_root, ANON_DIR)
    for u in units:
        # reviewer-facing filenames + ids must not encode role/identity
        assert "target_base" not in u["unit_id"] and "candidate" not in u["unit_id"], \
            "anonymous unit id must not encode role"
        _w(os.path.join(anon, "absolute-units", u["unit_id"] + ".json"), u)
        _w(os.path.join(anon, "scoring-forms", u["unit_id"] + ".json"),
           {"unit_id": u["unit_id"], "review_form": u["review_form"], "submitted": False})
    _w(os.path.join(private_root, "identity-key.json"), absolute_key)
    _w(os.path.join(private_root, "pairwise-key.json"), pairwise_key)
    return {"anonymous_dir": anon, "private_dir": private_root, "units": len(units)}


def finalize_scores(review_root, filled_forms):
    """Lock reviewer scores by hashing each finalized form. Touches ONLY review_root — never
    the private-unblinding directory."""
    lockdir = os.path.join(review_root, ANON_DIR, "score-locks")
    os.makedirs(lockdir, exist_ok=True)
    locks = {}
    for form in filled_forms:
        blob = json.dumps(form, sort_keys=True, ensure_ascii=False).encode("utf-8")
        h = hashlib.sha256(blob).hexdigest()
        _w(os.path.join(lockdir, form["unit_id"] + ".lock.json"),
           {"unit_id": form["unit_id"], "score_sha256": h, "locked": True})
        locks[form["unit_id"]] = h
    return locks


def scores_locked(review_root, unit_ids):
    lockdir = os.path.join(review_root, ANON_DIR, "score-locks")
    return all(os.path.exists(os.path.join(lockdir, uid + ".lock.json")) for uid in unit_ids)


def unblind(review_root, private_root, unit_ids):
    """Reveal identity ONLY after every score is locked. Raises otherwise."""
    if not scores_locked(review_root, unit_ids):
        raise UnblindError("cannot unblind before all scores are locked")
    key_path = os.path.join(private_root, "identity-key.json")
    if not os.path.exists(key_path):
        raise UnblindError("identity key missing")
    return json.load(open(key_path, encoding="utf-8"))


def assert_scoring_is_blind(private_root, scoring_callable):
    """Run scoring_callable() with reads of private_root denied; re-raise only genuine
    identity-access attempts. Returns the callable's result if it never touched private_root."""
    import builtins
    real_open = builtins.open
    priv = os.path.abspath(private_root)

    def guarded(path, *a, **k):
        if os.path.abspath(str(path)).startswith(priv):
            raise IdentityAccessError(f"scoring attempted to open identity data: {path}")
        return real_open(path, *a, **k)

    builtins.open = guarded
    try:
        return scoring_callable()
    finally:
        builtins.open = real_open
