"""Dispatch 27A — enforce blind reviewer-kit invariants (isolation, parity, no identity leaks)."""
import hashlib
import json
import os
import re
import zipfile

import pytest
import yaml

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KITS = os.path.join(REPO, "benchmarks", "runs", "qwen-prose-confirmation-v1", "reviewer-kits")
PACKET = os.path.join(REPO, "benchmarks", "runs", "qwen-prose-confirmation-v1", "review",
                      "review", "anonymous", "reviewer-packet.json")
REVIEWERS = ["chatgpt", "claude"]
REQUIRED = ["README-FIRST.md", "SCORING-INSTRUCTIONS.md", "SCORING-RUBRIC.md",
            "ANONYMOUS-REVIEW-UNITS.md", "REVIEW-SCORES-TEMPLATE.yaml",
            "REVIEW-SCORES-TEMPLATE.json", "SUBMISSION-CHECKLIST.md"]
FORBIDDEN = ["qwen", "bf16", "fp16", "fp8", "q4", "gguf", "quantiz", "ministral", "bonsai",
             "ternary", "identity-key", "pairwise-key", "private-unblinding", "model_role"]

_missing = not os.path.isdir(KITS)
pytestmark = pytest.mark.skipif(_missing, reason="reviewer kits not built in this environment")


def zpath(rev):
    return os.path.join(KITS, f"prose-review-{rev}-v1.zip")


def read_zip(rev):
    z = zipfile.ZipFile(zpath(rev))
    return z, z.namelist()


def test_both_zips_exist_and_extract():
    for rev in REVIEWERS:
        assert os.path.exists(zpath(rev))
        z, names = read_zip(rev)
        assert z.testzip() is None
        assert len(names) == 7


def test_required_files_present_single_root():
    for rev in REVIEWERS:
        _, names = read_zip(rev)
        root = f"prose-review-{rev}-v1/"
        assert all(n.startswith(root) for n in names)
        base = {n.split("/", 1)[1] for n in names}
        assert base == set(REQUIRED)


def test_no_private_paths_traversal_or_junk():
    for rev in REVIEWERS:
        _, names = read_zip(rev)
        for n in names:
            assert ".." not in n and not n.startswith("/") and ":" not in n
            low = n.lower()
            for bad in ("private", "identity", "key", "__pycache__", ".git", "unblind",
                        "manifest", "deployment", "decision"):
                assert bad not in low, (rev, n)


def test_no_identity_forbidden_terms_in_contents():
    for rev in REVIEWERS:
        z, names = read_zip(rev)
        for n in names:
            low = z.read(n).decode("utf-8", "ignore").lower()
            for t in FORBIDDEN:
                assert t not in low, (rev, n, t)


def test_reviewer_ids_correct_and_not_crossed():
    for rev in REVIEWERS:
        z, _ = read_zip(rev)
        tj = json.loads(z.read(f"prose-review-{rev}-v1/REVIEW-SCORES-TEMPLATE.json"))
        ty = yaml.safe_load(z.read(f"prose-review-{rev}-v1/REVIEW-SCORES-TEMPLATE.yaml"))
        assert tj["review_metadata"]["reviewer_id"] == rev
        assert ty["review_metadata"]["reviewer_id"] == rev
        other = "claude" if rev == "chatgpt" else "chatgpt"
        assert other not in z.read(f"prose-review-{rev}-v1/REVIEW-SCORES-TEMPLATE.yaml").decode("utf-8")


def test_templates_agree_and_cover_all_units_no_prefill():
    packet = json.load(open(PACKET, encoding="utf-8"))
    ids = {u["unit_id"] for u in packet}
    for rev in REVIEWERS:
        z, _ = read_zip(rev)
        tj = json.loads(z.read(f"prose-review-{rev}-v1/REVIEW-SCORES-TEMPLATE.json"))
        ty = yaml.safe_load(z.read(f"prose-review-{rev}-v1/REVIEW-SCORES-TEMPLATE.yaml"))
        jids = [u["unit_id"] for u in tj["units"]]
        yids = [u["unit_id"] for u in ty["units"]]
        assert set(jids) == set(yids) == ids
        assert len(jids) == len(set(jids)) == len(ids)  # unique, no extra
        # no prefilled scores
        for u in tj["units"]:
            assert all(v is None for v in u["scores"].values())
            assert u["fatal_failure"] is False and u["fatal_failure_type"] is None


def test_all_frozen_units_present_and_output_preserved():
    packet = json.load(open(PACKET, encoding="utf-8"))
    for rev in REVIEWERS:
        z, _ = read_zip(rev)
        md = z.read(f"prose-review-{rev}-v1/ANONYMOUS-REVIEW-UNITS.md").decode("utf-8")
        found = re.findall(r"## Review Unit: (unit-[0-9a-f]+)", md)
        assert sorted(found) == sorted(u["unit_id"] for u in packet)
        assert len(found) == len(set(found))
        # each frozen output appears verbatim (non-empty ones)
        for u in packet:
            if u["text"].strip():
                assert u["text"].strip() in md, (rev, u["unit_id"])


def test_zip_sha_matches_manifest_and_source_commit_recorded():
    m = json.load(open(os.path.join(KITS, "reviewer-kit-manifest.json"), encoding="utf-8"))
    assert m["identity_key_included"] is False and m["private_data_included"] is False
    assert re.fullmatch(r"[0-9a-f]{40}", m["source_commit"])
    for rev in REVIEWERS:
        digest = hashlib.sha256(open(zpath(rev), "rb").read()).hexdigest()
        assert m[rev]["zip_sha256"] == digest
        assert m[rev]["reviewer_id"] == rev
    # orders differ between reviewers (randomized presentation)
    assert m["chatgpt"]["unit_order_sha256"] != m["claude"]["unit_order_sha256"]
