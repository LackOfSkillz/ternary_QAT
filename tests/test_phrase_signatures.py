"""Tests for the Electro phrase-signature normalization + Gate 0 v3 scanner.

Uses the REAL phrase-families.yaml. Verifies deterministic normalization, dedup,
attribution, exclusions, family matching, tiering, density, clustering, em-dash
compound signatures, and no-substring/ordinary-phrase false positives.
"""
import os
import shutil
import sys

import pytest

_HERE = os.path.dirname(__file__)
_SCR = os.path.join(_HERE, "..", "datasets", "research",
                    "electro-phrase-signatures", "scripts")
_FAM = os.path.join(_HERE, "..", "datasets", "research",
                    "electro-phrase-signatures", "normalized", "phrase-families.yaml")
sys.path.insert(0, os.path.abspath(_SCR))

yaml = pytest.importorskip("yaml")
import scan_phrase_signatures as sig          # noqa: E402
import normalize_phrase_lists as norm          # noqa: E402

FAM = sig.load_families(os.path.abspath(_FAM))


# ---- classification / exclusions ----

def test_proper_name_excluded():
    assert sig.classify_artifact("elara stood") == "corpus_specific_proper_name"
    assert sig.classify_artifact("lord valerius") == "corpus_specific_proper_name"
    assert sig.classify_artifact("elias thorne") == "corpus_specific_proper_name"


def test_setting_and_numeric_excluded():
    assert sig.classify_artifact("sector gamma") == "corpus_specific_setting_identifier"
    assert sig.classify_artifact("unit 734") == "corpus_specific_setting_or_numeric"


def test_malformed_excluded():
    assert sig.classify_artifact("fa ade") == "malformed_or_truncated"
    assert sig.classify_artifact("constructed fa") == "malformed_or_truncated"


def test_ordinary_not_artifact():
    assert sig.classify_artifact("cold air") is None
    assert sig.classify_artifact("a cold knot") is None      # 'a' is a real word
    assert sig.classify_artifact("wooden table") is None


# ---- tiering ----

def test_tier_high_risk():
    for p in ("profound silence", "crushing weight", "utterly devoid",
              "voice dropping to", "a physical weight", "polished obsidian"):
        assert sig.tier_for(p, FAM) == "high_risk_signature", p


def test_tier_contextual():
    for p in ("metallic tang", "voice low", "leaned forward", "jaw tightened",
              "gaze fixed"):
        assert sig.tier_for(p, FAM) == "contextual_risk", p


def test_tier_ordinary():
    for p in ("cold air", "wooden table", "years ago"):
        assert sig.tier_for(p, FAM) == "ordinary_phrase", p


def test_proper_name_tier_is_corpus_artifact():
    # author/character allowlist behavior: names never become generic markers
    assert sig.tier_for("elara stood", FAM) == "corpus_artifact"
    assert sig.tier_for("king theron", FAM) == "corpus_artifact"


# ---- family matching / boundaries ----

def test_family_matching():
    assert "dialogue_delivery_template" in sig.families_for("voice low", FAM)
    assert "gaze_eye_choreography" in sig.families_for("gaze fixed", FAM)
    assert "pressure_metaphor" in sig.families_for("crushing weight", FAM)
    assert "comparative_template" in sig.families_for("the way", FAM)  # match_phrase


def test_word_boundary_no_substring_false_positive():
    # 'like' is a comparative token but must match only as a whole word
    assert "comparative_template" not in sig.families_for("unlike this", FAM)
    assert sig.families_for("background noise", FAM) == []   # 'ground' not a token


def test_case_insensitive_scan():
    m = sig.scan_text("Her VOICE was LOW and her GAZE was fixed.", FAM, {})
    assert m["family_hits"]["dialogue_delivery_template"] >= 1
    assert m["family_hits"]["gaze_eye_choreography"] >= 1


# ---- scanning metrics ----

def test_ordinary_text_no_high_risk():
    m = sig.scan_text("The cold air moved over the wooden table.", FAM, {})
    assert m["high_risk_count"] == 0


def test_density_per_1000_and_word_count():
    m = sig.scan_text("voice voice voice", FAM, {})
    assert m["word_count"] == 3
    fid = "dialogue_delivery_template"
    assert m["family_density"][fid] == round(m["family_hits"][fid] / 3 * 1000, 1)
    assert m["family_density"][fid] > 0


def test_clustering_window():
    dense = " ".join(["voice"] * 10 + ["neutral"] * 30)
    sparse = " ".join(["morning"] * 40)
    assert sig.scan_text(dense, FAM, {})["cluster_windows"] >= 1
    assert sig.scan_text(sparse, FAM, {})["cluster_windows"] == 0


def test_em_dash_compound_signature():
    hit = sig.scan_text("The room was still — a profound silence.", FAM, {})
    miss = sig.scan_text("The door opened — she stepped through it.", FAM, {})
    assert hit["em_dash_compound"] == 1
    assert miss["em_dash_compound"] == 0


def test_introduced_vs_preserved_family_multiset():
    src = sig._family_multiset("the room was quiet and empty", FAM)
    gold = sig._family_multiset("her voice dropped, her voice barely audible", FAM)
    fid = "dialogue_delivery_template"
    assert src[fid] == 0 and gold[fid] > 0     # introduced by gold


def test_exact_candidate_hits_use_index():
    cand = {"profound silence": {"tier": "high_risk_signature",
                                 "families": ["generic_intensifier"]}}
    m = sig.scan_text("It fell into a profound silence at last.", FAM, cand)
    assert "profound silence" in m["exact_hits"]["high_risk_signature"]


# ---- deterministic normalization on a temp root ----

def _tmp_artifact(tmp_path):
    root = tmp_path / "art"
    (root / "raw").mkdir(parents=True)
    (root / "normalized").mkdir()
    (root / "reports").mkdir()
    shutil.copy(os.path.abspath(_FAM), root / "normalized" / "phrase-families.yaml")
    (root / "raw" / "bigrams-electro-a.txt").write_text(
        "voice low\nprofound silence\nelara stood\nvoice low\n", encoding="utf-8")
    (root / "raw" / "bigrams-electro-b.txt").write_text(
        "voice low\nfa ade\n", encoding="utf-8")
    (root / "raw" / "trigrams-electro-a.txt").write_text(
        "a physical weight\n", encoding="utf-8")
    return root


def test_normalization_dedup_attribution_exclusion(tmp_path):
    root = _tmp_artifact(tmp_path)
    norm.run(str(root))
    cand = yaml.safe_load(open(root / "normalized" / "candidate-phrases.yaml",
                               encoding="utf-8"))["phrases"]
    excl = yaml.safe_load(open(root / "normalized" / "excluded-artifacts.yaml",
                               encoding="utf-8"))
    by = {c["phrase"]: c for c in cand}
    # dedup + cross-file attribution
    assert by["voice low"]["source_files"] == ["bigrams-electro-a.txt",
                                               "bigrams-electro-b.txt"]
    assert by["voice low"]["tier"] == "contextual_risk"
    assert by["profound silence"]["tier"] == "high_risk_signature"
    assert by["a physical weight"]["n"] == 3
    # exclusions preserved with reasons
    reasons = {e["phrase"]: e["reason"] for e in excl}
    assert reasons["elara stood"] == "corpus_specific_proper_name"
    assert reasons["fa ade"] == "malformed_or_truncated"


def test_normalization_deterministic(tmp_path):
    root = _tmp_artifact(tmp_path)
    norm.run(str(root))
    first = (root / "normalized" / "candidate-phrases.yaml").read_bytes()
    norm.run(str(root))
    second = (root / "normalized" / "candidate-phrases.yaml").read_bytes()
    assert first == second


def test_scan_text_deterministic():
    t = "Her voice low, the crushing weight of a profound silence — and the way she moved."
    assert sig.scan_text(t, FAM, {}) == sig.scan_text(t, FAM, {})
