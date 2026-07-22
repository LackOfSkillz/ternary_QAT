"""Corpus-level slop analysis (Dispatch 23, Workstream E).

Detects sameness that appears only ACROSS outputs of one model role: repeated openings/
endings, shared template structure, image-family reuse. Deterministic (n-gram / opening
overlap; no embeddings). Every cluster cites the evidence outputs that support it. Cross-role
comparison happens only after blind per-output scoring is locked (enforced by the caller).
"""
import re
from collections import defaultdict

VERSION = "slop-corpus-v1"


def _opening(text, n_words):
    return " ".join(re.findall(r"\w+", (text or "").lower())[:n_words])


def _ending(text, n_words):
    ws = re.findall(r"\w+", (text or "").lower())
    return " ".join(ws[-n_words:]) if ws else ""


def _shingles(text, n=5):
    ws = re.findall(r"\w+", (text or "").lower())
    return {tuple(ws[i:i + n]) for i in range(max(0, len(ws) - n + 1))}


def _jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def corpus_slop_summary(outputs, model_role, run_id="unset", opening_words=6,
                        ending_words=6, similarity_threshold=0.4):
    """``outputs`` = [{output_id, text}]. ``similarity_threshold`` is a REPORTING cluster
    cutoff (documented as unvalidated), not a quality verdict."""
    ids = [o["output_id"] for o in outputs]

    def cluster_by(keyfn, words):
        buckets = defaultdict(list)
        for o in outputs:
            buckets[keyfn(o["text"], words)].append(o["output_id"])
        return [{"pattern": k, "output_ids": v} for k, v in buckets.items()
                if k and len(v) >= 2]

    opening_clusters = cluster_by(_opening, opening_words)
    ending_clusters = cluster_by(_ending, ending_words)

    # pairwise shingle similarity clusters (template reuse)
    shs = {o["output_id"]: _shingles(o["text"]) for o in outputs}
    pairs = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            sim = _jaccard(shs[ids[i]], shs[ids[j]])
            if sim >= similarity_threshold:
                pairs.append({"a": ids[i], "b": ids[j], "similarity": round(sim, 4)})

    evidence_ids = sorted({x for c in opening_clusters + ending_clusters for x in c["output_ids"]}
                          | {p["a"] for p in pairs} | {p["b"] for p in pairs})
    return {
        "schema": "slop-corpus-summary", "schema_version": 1, "version": VERSION,
        "run_id": run_id, "model_role": model_role, "output_ids": ids,
        "cross_output_similarity": {"pairs": pairs, "threshold": similarity_threshold,
                                    "threshold_status": "unvalidated"},
        "opening_pattern_clusters": opening_clusters,
        "ending_pattern_clusters": ending_clusters,
        "image_family_clusters": [],           # requires semantic detectors (interface-only)
        "scene_solution_clusters": [],
        "voice_convergence": {"note": "requires pinned embeddings; interface-only"},
        "genre_separation": {},
        "dominant_templates": [{"pattern": c["pattern"], "output_ids": c["output_ids"]}
                               for c in opening_clusters],
        "evidence_output_ids": evidence_ids,
        "confidence": "moderate" if (opening_clusters or pairs) else "inconclusive",
        "limitations": ["deterministic overlap only; semantic image/voice convergence is "
                        "interface-only", "similarity threshold is unvalidated"],
    }
