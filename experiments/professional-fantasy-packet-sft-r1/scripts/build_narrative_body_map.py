"""Dispatch 30A-R1 — Phase 2 (corrected): build a private narrative-body map per source.

Identifies the story body and excludes front matter (title/copyright/contents/foreword/introduction/
framing prologue/dramatis personae/maps) and back matter (appendix/glossary/index/about-the-author).
Uses explicit section markers + a forward dialogue-density signal (story prose carries dialogue;
framing/expository matter does not). Output is PRIVATE (offsets are retrieval keys); prints only
percentages/counts, no prose.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from segment_scenes import paragraphs, classify  # noqa: E402

NORM_DIR = os.path.join(EXP, "private-data", "normalized-sources")
NORM_MANIFEST = os.path.join(EXP, "private-data", "normalized-manifest.json")
OUT = os.path.join(EXP, "private-data", "narrative-body-map.json")

FRONT = re.compile(r"^(contents|table of contents|foreword|preface|introduction|note on the text|"
                   r"dramatis personae|dedication|acknowledg|copyright|maps?|illustrations?|"
                   r"a note (on|about)|by the same author|also by)\b", re.I)
BACK = re.compile(r"^(appendix|appendices|glossary|index|about the author|acknowledg|also by|"
                  r"an excerpt|excerpt from|preview of|coming soon|dramatis personae)\b", re.I)
WORD = re.compile(r"\S+")


def has_dialogue(t):
    return '"' in t or "“" in t


def main():
    nm = json.load(open(NORM_MANIFEST, encoding="utf-8"))["files"]
    maps, stats = {}, {}
    for e in nm:
        fn = e["filename"]
        text = open(os.path.join(NORM_DIR, fn), encoding="utf-8").read()
        total = len(text)
        paras = classify(paragraphs(text))
        pw = [len(WORD.findall(p["text"])) for p in paras]
        n = len(paras)
        # forward dialogue ratio over ~4000-word window per paragraph
        fwd = [0.0] * n
        for i in range(n):
            w, dq, tot, j = 0, 0, 0, i
            while j < n and w < 4000:
                w += pw[j]; tot += 1; dq += 1 if has_dialogue(paras[j]["text"]) else 0; j += 1
            fwd[i] = dq / max(1, tot)
        # last front-matter marker within first 22% of file
        front_cut = 0
        for i, p in enumerate(paras):
            if p["start"] > 0.22 * total:
                break
            if FRONT.match(p["text"].strip()) or (p["role"] == "chapter" and FRONT.match(p["text"].strip() or "")):
                front_cut = i + 1
        # narrative_start = first para at/after front_cut whose forward window carries dialogue
        start_i = front_cut
        for i in range(front_cut, n):
            if fwd[i] >= 0.12:
                start_i = i; break
        # narrative_end = earliest back-matter marker after 65% of file
        end_i = n
        for i, p in enumerate(paras):
            if p["start"] > 0.65 * total and BACK.match(p["text"].strip()):
                end_i = i; break
        else:
            for i in range(n - 1, -1, -1):
                if fwd[i] >= 0.08:
                    end_i = min(n, i + 1); break
        ns = paras[start_i]["start"] if start_i < n else 0
        ne = paras[end_i]["start"] if end_i < n else total
        body_words = sum(pw[start_i:end_i])
        excluded = []
        if ns > 0:
            excluded.append({"start_offset": 0, "end_offset": ns, "reason": "front_matter"})
        if ne < total:
            excluded.append({"start_offset": ne, "end_offset": total, "reason": "back_matter"})
        conf = "high" if (front_cut > 0 or fwd[start_i] >= 0.15) else "medium"
        maps[fn] = {"source_filename": fn, "source_sha256": e["normalized_sha256"],
                    "narrative_start_offset": ns, "narrative_end_offset": ne,
                    "body_word_count": body_words, "excluded_ranges": excluded, "confidence": conf}
        stats[fn] = {"start_pct": round(100 * ns / total, 1), "end_pct": round(100 * ne / total, 1),
                     "body_words": body_words, "confidence": conf}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"dispatch": "30A-R1", "note": "PRIVATE (offsets); percentages/counts only elsewhere",
               "sources": maps}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"body_maps": len(maps), "per_source": stats}, indent=1))


if __name__ == "__main__":
    main()
