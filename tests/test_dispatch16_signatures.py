"""Dispatch 16 tests: contextual-phrase restraint, author-voice preservation,
signature persistence under substitution, raw+density reporting, and determinism.
Scans the REAL Dataset A drafts and the REAL phrase families.
"""
import glob
import os
import re
import sys

import pytest

_HERE = os.path.dirname(__file__)
_DA = os.path.join(_HERE, "..", "datasets", "dataset-a")
_ART = os.path.join(_HERE, "..", "datasets", "research", "electro-phrase-signatures")
_SCR = os.path.join(_ART, "scripts")
sys.path.insert(0, os.path.abspath(_SCR))

yaml = pytest.importorskip("yaml")
import scan_phrase_signatures as sig          # noqa: E402

FAM = sig.load_families()
CAND = sig.load_candidates() if os.path.exists(sig.DEFAULT_CANDIDATES) else {}
DA_ROOT = os.path.abspath(_DA)


def _drafts():
    return sorted(glob.glob(os.path.join(DA_ROOT, "drafts", "**", "*.md"), recursive=True))


def _fm(path):
    t = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    return yaml.safe_load(m.group(1))


# 3. lexical synonym substitution remains in the same phrase family
def test_lexical_substitution_stays_in_family():
    a = set(sig.families_for("metallic tang", FAM))
    b = set(sig.families_for("coppery taste", FAM))
    assert "generic_sensory_shorthand" in a & b


# 4. pressure-metaphor substitution detected as structural persistence
def test_pressure_substitution_persists():
    assert "pressure_metaphor" in sig.families_for("crushing weight", FAM)
    assert "pressure_metaphor" in sig.families_for("immense weight", FAM)


# 5. multiple body-reaction cues trigger a cluster review
def test_body_cluster_triggers_window():
    txt = ("His breath hitched. Her jaw worked. He swallowed, knuckles white, hands "
           "trembling, heart hammering, a cold knot in his gut, another gasp, and "
           "still the shudder would not stop.")
    assert sig.scan_text(txt, FAM, CAND)["cluster_windows"] >= 1


# 6. one body-reaction cue does not trigger a blacklist failure
def test_single_body_cue_no_failure():
    m = sig.scan_text("Her jaw tightened once, and she said nothing.", FAM, CAND)
    assert m["high_risk_count"] == 0
    assert m["cluster_windows"] == 0
    assert sig.tier_for("jaw tightened", FAM) == "contextual_risk"


# 7. dialogue-delivery replacement with tone/cadence is equivalent risk
def test_tone_modifier_equivalent_delivery_risk():
    assert "dialogue_delivery_template" in sig.families_for("tone flat", FAM)
    assert "dialogue_delivery_template" in sig.families_for("voice low", FAM)
    assert "dialogue_delivery_template" in sig.families_for("cadence hardening", FAM)


# 8 + 9. comparative raw counts AND density are both reported (raw not hidden)
def test_segment_reports_raw_and_density():
    recs = sig.scan_dataset_a(DA_ROOT, FAM, CAND)
    s = sig._seg_section(recs, "gold")
    assert "comparative_raw" in s and "comparative_density" in s
    assert "high_risk_raw" in s and "words" in s


# 1 + 2 + 10 + 11. no-change / author-voice / the-way determinism on real data
def test_no_change_and_author_voice_preserved():
    recs = {r["id"]: r for r in sig.scan_dataset_a(DA_ROOT, FAM, CAND)}
    assert recs["dsa-revision-019"]["structured_no_change"] is True
    # author-voice override keeps its declared 'the way' anaphora in the gold
    assert recs["dsa-revision-020"]["the_way_gold"] == 3


def test_the_way_and_profile_counts_deterministic():
    a = sig.scan_dataset_a(DA_ROOT, FAM, CAND)
    b = sig.scan_dataset_a(DA_ROOT, FAM, CAND)
    aw = {r["id"]: (r["the_way_source"], r["the_way_gold"]) for r in a}
    bw = {r["id"]: (r["the_way_source"], r["the_way_gold"]) for r in b}
    assert aw == bw
    ap = sorted(r["style_profile"] for r in a)
    bp = sorted(r["style_profile"] for r in b)
    assert ap == bp


# 15. segmented report is deterministic
def test_segmented_report_deterministic():
    recs = sig.scan_dataset_a(DA_ROOT, FAM, CAND)
    new = {f"dsa-revision-{i:03d}" for i in range(11, 21)}
    assert sig.render_segmented_md(recs, FAM, new) == sig.render_segmented_md(recs, FAM, new)


# 12 + 13. after the Dispatch 17 experimental freeze, all records are approved for
# experimental use only (never production), split-assigned, with correct exclusion.
def test_all_records_experimentally_frozen():
    for f in _drafts():
        fm = _fm(f)
        assert fm["review_status"] == "approved", f
        assert fm["experimental_use_only"] is True, f
        assert fm["production_approved"] is False, f
        assert fm["teacher_terms_status"] == "pending_review", f
        assert fm["split"] in ("train", "evaluation"), f
        if fm["split"] == "evaluation":
            assert fm["excluded_from_training"] is True, f     # never gradient-trained
        else:
            assert fm["excluded_from_training"] is False, f


def test_new_records_present_and_excluded():
    ids = {_fm(f)["id"] for f in _drafts()}
    for i in range(11, 21):
        assert f"dsa-revision-{i:03d}" in ids


# 14. no raw Electro artifact entered compiled/training paths
def test_no_raw_electro_in_compiled_or_dataset():
    # compiled JSONL may now exist (the experimental freeze), but NO raw Electro
    # phrase-list file may appear under compiled, and the raw lists must not be
    # embedded in the compiled targets.
    # No raw Electro phrase-LIST file may appear under compiled. (Individual phrases
    # legitimately appear inside records — that is the material being taught — so the
    # guard is the raw list files, not phrase substrings; the compiler only ever
    # reads drafts/**/*.md, never the research raw lists.)
    for f in glob.glob(os.path.join(DA_ROOT, "compiled", "**", "*"), recursive=True):
        base = os.path.basename(f).lower()
        assert not (base.startswith("bigrams") or base.startswith("trigrams"))
    # raw lists exist ONLY under the research artifact
    raws = glob.glob(os.path.join(DA_ROOT, "..", "**", "raw", "*.txt"), recursive=True)
    for r in raws:
        assert "electro-phrase-signatures" in r.replace("\\", "/")
