"""Threshold freeze enforcement (Dispatch 25, D3).

Computes content hashes, verifies each threshold file is committed and has no working-tree
modifications, writes a lock record referencing the commit + hashes, and refuses to continue
analysis if either file is missing, uncommitted, or modified after lock. A changed threshold
does not silently relock — it invalidates the decision run.
"""
import hashlib
import json
import os
import subprocess

from linewright import config as C
from linewright.evaluation.thresholds import RESEARCH_THRESHOLD, STARTER_THRESHOLD, LOCK_PATH
from linewright.evaluation.thresholds.loader import load, validate_metadata


def content_hash(path):
    return hashlib.sha256(open(C.abs_repo(path), "rb").read()).hexdigest()


def _git(args):
    return subprocess.run(["git"] + args, cwd=C.REPO_ROOT, capture_output=True, text=True)


def is_tracked(path):
    r = _git(["ls-files", "--error-unmatch", path])
    return r.returncode == 0


def is_clean(path):
    """True if the tracked file has no staged/unstaged working-tree modifications."""
    r = _git(["status", "--porcelain", "--", path])
    return r.returncode == 0 and r.stdout.strip() == ""


def head_commit():
    r = _git(["rev-parse", "HEAD"])
    return r.stdout.strip() if r.returncode == 0 else None


def write_lock(out_path=LOCK_PATH):
    """Write the lock record. Raises if a threshold is missing/uncommitted/modified or invalid."""
    for path in (RESEARCH_THRESHOLD, STARTER_THRESHOLD):
        if not os.path.exists(C.abs_repo(path)):
            raise FileNotFoundError(f"threshold missing: {path}")
        problems = validate_metadata(load(path))
        if problems:
            raise ValueError(f"threshold metadata invalid: {problems}")
        if not is_tracked(path):
            raise ValueError(f"threshold not committed: {path}")
        if not is_clean(path):
            raise ValueError(f"threshold has uncommitted modifications: {path}")
    lock = {
        "research_threshold_path": RESEARCH_THRESHOLD,
        "research_threshold_sha256": content_hash(RESEARCH_THRESHOLD),
        "starter_threshold_path": STARTER_THRESHOLD,
        "starter_threshold_sha256": content_hash(STARTER_THRESHOLD),
        "git_commit": head_commit(),
        "locked_at": "2026-07-22",
        "locked_before_analysis": True,
        "modified_after_lock": False,
    }
    with open(C.abs_repo(out_path), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(lock, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return lock


def load_lock(path=LOCK_PATH):
    return json.load(open(C.abs_repo(path), encoding="utf-8"))


def verify_lock(lock=None):
    """Return {threshold_precommit_valid, decision_status, ...}. Any drift invalidates."""
    lock = lock or load_lock()
    problems = []
    for pkey, hkey in (("research_threshold_path", "research_threshold_sha256"),
                       ("starter_threshold_path", "starter_threshold_sha256")):
        path = lock[pkey]
        if not os.path.exists(C.abs_repo(path)):
            problems.append(f"missing {path}")
            continue
        if content_hash(path) != lock[hkey]:
            problems.append(f"hash changed since lock: {path}")
        if not is_tracked(path):
            problems.append(f"no longer committed: {path}")
        if not is_clean(path):
            problems.append(f"working-tree modification after lock: {path}")
    valid = not problems
    return {
        "threshold_precommit_valid": valid,
        "modified_after_lock": not valid,
        "decision_status": "valid" if valid else "invalidated",
        "problems": problems,
        "research_threshold_sha256": lock["research_threshold_sha256"],
        "starter_threshold_sha256": lock["starter_threshold_sha256"],
        "git_commit": lock["git_commit"],
    }


def require_locked_before_analysis():
    """Gate every analysis/decision on a valid lock. Raises if invalid."""
    v = verify_lock()
    if not v["threshold_precommit_valid"]:
        raise RuntimeError(f"threshold lock invalid — analysis refused: {v['problems']}")
    return v
