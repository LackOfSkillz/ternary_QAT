"""Dispatch 30A-R1 — freeze the 65-passage accepted set.

Merges the 11 accepted c01 + 54 accepted round-2 candidates, applies the 3 coherent round-two start
edits, preserves the corrected got-c01, and ignores TWO accidental near-end adjust_start values
(got-c01=1057247, sanderson-c02=30428 -> 17 words) as stale. Recomputes word count + target SHA-256
for edited passages, verifies integrity, and runs same-source overlap detection. Private outputs
(offsets/targets git-ignored); prints metadata only.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from segment_scenes import paragraphs  # noqa: E402

NORM = os.path.join(EXP, "private-data", "normalized-sources")
ACCEPTED = os.path.join(EXP, "manifests", "accepted-passages.jsonl")
CAND = os.path.join(EXP, "manifests", "candidate-passages.jsonl")
TARGETS = os.path.join(EXP, "private-data", "targets")
AUDIT = os.path.join(EXP, "private-data", "recovery-audit.json")

VALID_EDITS = {"mouser-c06": 154223, "pawn-c06": 123703, "got-c06": 570140}
IGNORED_ADJUSTMENTS = {"got-c01": 1057247, "sanderson-c02": 30428}  # accidental near-end clicks


def src(fn, cache):
    if fn not in cache:
        cache[fn] = open(os.path.join(NORM, fn), encoding="utf-8").read()
    return cache[fn]


def main():
    c01 = {json.loads(l)["passage_id"]: json.loads(l) for l in open(ACCEPTED, encoding="utf-8") if l.strip()}
    cand = {json.loads(l)["passage_id"]: json.loads(l) for l in open(CAND, encoding="utf-8") if l.strip()}
    allrec = {**c01, **cand}
    cache, audit_edits = {}, []
    accepted = []
    for pid, r in allrec.items():
        r = dict(r)
        fn = r["source_filename"]
        text = src(fn, cache)
        if pid in VALID_EDITS:
            old = (r["start_character_offset"], r["end_character_offset"], r["target_word_count"], r["target_sha256"])
            ns = VALID_EDITS[pid]
            para_ok = ns in {p["start"] for p in paragraphs(text)}
            seg = text[ns:r["end_character_offset"]]
            assert para_ok and ns < r["end_character_offset"] and len(seg.split()) >= 200, f"edit {pid} invalid/incoherent"
            r["start_character_offset"] = ns
            r["target_word_count"] = len(seg.split())
            r["target_token_count"] = round(len(seg.split()) / 0.75)
            r["target_sha256"] = hashlib.sha256(seg.encode()).hexdigest()
            r["boundary_adjusted"] = "round2 start edit"
            # rewrite private target payload for the edited passage
            _rewrite_target(pid, fn, ns, r["end_character_offset"], text)
            audit_edits.append({"passage_id": pid, "old_start": old[0], "new_start": ns,
                                "old_words": old[2], "new_words": r["target_word_count"],
                                "old_hash": old[3][:12], "new_hash": r["target_sha256"][:12]})
        elif pid in IGNORED_ADJUSTMENTS:
            # keep original accepted boundary; do NOT apply the accidental adjustment
            r["ignored_accidental_adjust_start"] = IGNORED_ADJUSTMENTS[pid]
        r["human_review_status"] = "accepted"
        accepted.append(r)

    # integrity + overlap
    cache2, errors = {}, []
    by_source, hashes = {}, {}
    for r in accepted:
        fn = r["source_filename"]
        seg = src(fn, cache2)[r["start_character_offset"]:r["end_character_offset"]]
        if hashlib.sha256(seg.encode()).hexdigest() != r["target_sha256"]:
            errors.append(f"{r['passage_id']}: target hash mismatch")
        if len(seg.split()) != r["target_word_count"]:
            errors.append(f"{r['passage_id']}: word count mismatch")
        by_source.setdefault(fn, []).append(r)
        hashes.setdefault(r["target_sha256"], []).append(r["passage_id"])
    dup_hashes = {h: ids for h, ids in hashes.items() if len(ids) > 1}
    overlaps, material = [], []
    for fn, rs in by_source.items():
        rs.sort(key=lambda x: x["start_character_offset"])
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                a, b = rs[i], rs[j]
                lo = max(a["start_character_offset"], b["start_character_offset"])
                hi = min(a["end_character_offset"], b["end_character_offset"])
                if hi > lo:
                    shared = hi - lo
                    pair = {"a": a["passage_id"], "b": b["passage_id"], "shared_chars": shared}
                    overlaps.append(pair)
                    shorter = min(a["end_character_offset"] - a["start_character_offset"],
                                  b["end_character_offset"] - b["start_character_offset"])
                    if shared > 0.10 * shorter:
                        material.append(pair)

    with open(ACCEPTED, "w", encoding="utf-8", newline="\n") as fh:
        for r in accepted:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # private audit append
    audit = json.load(open(AUDIT, encoding="utf-8")) if os.path.exists(AUDIT) else {"dispatch": "30A-R1", "corrections": []}
    audit.setdefault("round2_freeze", {})
    audit["round2_freeze"] = {
        "valid_edits_applied": audit_edits,
        "ignored_accidental_adjust_starts": [
            {"passage_id": "got-c01", "ignored_start": 1057247, "kept": "2386w @ 1045159-1057980"},
            {"passage_id": "sanderson-c02", "ignored_start": 30428, "would_yield_words": 17,
             "kept_original": "3107w @ 11766-30521", "status": "PENDING Gary confirmation (parallels got-c01)"}]}
    json.dump(audit, open(AUDIT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    from collections import Counter
    words = [r["target_word_count"] for r in accepted]
    by_src_counts = dict(Counter(r["source_filename"] for r in accepted))
    print(json.dumps({"accepted_total": len(accepted), "by_source": by_src_counts,
                      "valid_edits_applied": len(audit_edits), "ignored_accidental": 2,
                      "integrity_errors": errors, "duplicate_hashes": dup_hashes,
                      "overlapping_pairs": len(overlaps), "material_overlaps": material,
                      "word_count_range": [min(words), max(words)]}, indent=1))


def _rewrite_target(pid, fn, s, e, text):
    p = os.path.join(TARGETS, pid + ".json")
    if not os.path.exists(p):
        return
    d = json.load(open(p, encoding="utf-8"))
    d["text"] = text[s:e]
    d["start_offset"] = s
    d["end_offset"] = e
    d["word_count"] = len(text[s:e].split())
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
