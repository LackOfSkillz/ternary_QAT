"""Dispatch 30A-R1 — validate the candidate passage manifest. Confirms each row conforms to the
passage-manifest schema-ish shape, offsets lie within the frozen normalized source, the target text
recovers EXACTLY from (source, offsets) via target_sha256, and word counts are in range. Runs
locally on private data; prints statistics only (no prose).
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
NORM_DIR = os.path.join(EXP, "private-data", "normalized-sources")
NORM_MANIFEST = os.path.join(EXP, "private-data", "normalized-manifest.json")
CAND = os.path.join(EXP, "manifests", "candidate-passages.jsonl")
REQUIRED = ("passage_id", "source_filename", "source_sha256", "start_character_offset",
            "end_character_offset", "target_word_count", "target_sha256", "segmentation_method",
            "segmentation_confidence", "human_review_status")


def main():
    nm = {e["filename"]: e for e in json.load(open(NORM_MANIFEST, encoding="utf-8"))["files"]}
    cache = {}
    rows = [json.loads(l) for l in open(CAND, encoding="utf-8") if l.strip()]
    errors, per_source = [], {}
    ids = set()
    for r in rows:
        pid = r.get("passage_id", "?")
        for k in REQUIRED:
            if k not in r:
                errors.append(f"{pid}: missing {k}")
        if pid in ids:
            errors.append(f"{pid}: duplicate id")
        ids.add(pid)
        fn = r["source_filename"]
        per_source[fn] = per_source.get(fn, 0) + 1
        if fn not in nm:
            errors.append(f"{pid}: source not in normalized manifest"); continue
        if r["source_sha256"] != nm[fn]["normalized_sha256"]:
            errors.append(f"{pid}: source hash != normalized source")
        if fn not in cache:
            cache[fn] = open(os.path.join(NORM_DIR, fn), encoding="utf-8").read()
        text = cache[fn]
        s, e = r["start_character_offset"], r["end_character_offset"]
        if not (0 <= s < e <= len(text)):
            errors.append(f"{pid}: offsets out of range"); continue
        seg = text[s:e]
        if hashlib.sha256(seg.encode("utf-8")).hexdigest() != r["target_sha256"]:
            errors.append(f"{pid}: target_sha256 does not recover from source offsets")
        if len(seg.split()) != r["target_word_count"]:
            errors.append(f"{pid}: word_count mismatch")
        if not (1400 <= r["target_word_count"] <= 4500):
            errors.append(f"{pid}: word_count {r['target_word_count']} out of [1400,4500]")
    ok = not errors
    report = {"dispatch": "30A-R1", "candidates": len(rows), "sources": len(per_source),
              "per_source": per_source, "all_11_sources": len(per_source) == 11,
              "errors": errors[:50], "error_count": len(errors), "valid": ok}
    json.dump(report, open(os.path.join(EXP, "reports", "segmentation-validation.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"candidates": len(rows), "sources": len(per_source),
                      "offset_recovery_valid": ok, "errors": len(errors)}, indent=1))
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
