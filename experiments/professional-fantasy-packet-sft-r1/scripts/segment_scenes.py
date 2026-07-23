"""Dispatch 30A-R1 — Phase 2 hierarchical scene segmentation.

Structure leads, word count is a preference not a cutting rule:
  1. detect chapter / part / prologue headings and ornament breaks;
  2. split into scenes at headings, ornaments, and >=2-blank-line gaps;
  3. snap every boundary to complete paragraphs (never mid-paragraph);
  4. split oversized scenes only at paragraph boundaries; merge tiny ones forward;
  5. prefer 600-1400 words, permit 400-1800, reject the rest as candidates.

Emits ~12-16 candidates/source with metadata to the git-ignored candidate manifest, and per-candidate
text (+ surrounding context) to git-ignored private-data/targets/ for the local review app.
No prose is printed or committed.
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
NORM_DIR = os.path.join(EXP, "private-data", "normalized-sources")
NORM_MANIFEST = os.path.join(EXP, "private-data", "normalized-manifest.json")
TARGETS = os.path.join(EXP, "private-data", "targets")
CAND = os.path.join(EXP, "manifests", "candidate-passages.jsonl")
SEG_VERSION = "seg-v1"

CHAP = re.compile(r"^(chapter\b|prologue\b|epilogue\b|part\s+[ivxlcm\d]|book\s+[ivxlcm\d]|"
                  r"[ivxlcdm]{1,6}$|\d{1,3}$)", re.I)
ACTION = re.compile(r"\b(ran|drew|struck|leapt|swung|threw|grabbed|slashed|charged|dodged|kicked|"
                    r"lunged|sprinted|hurled|ducked|parried|gripped|shoved|dove|rolled|snatched|"
                    r"seized|clawed|smashed|fired|drove|crashed)\b", re.I)
STOP_NAMES = {"The", "He", "She", "They", "It", "His", "Her", "A", "An", "And", "But", "When",
              "Then", "There", "That", "This", "As", "At", "In", "On", "So", "If", "For", "Now",
              "I", "You", "We", "No", "Yes", "What", "Why", "How", "Who"}


def is_ornament(t):
    s = t.strip()
    return 0 < len(s) <= 12 and all(c in "*#~•·—-⁂※.✦ " for c in s) and any(c not in " ." for c in s)


def is_chapter(t):
    s = t.strip()
    return len(s) <= 40 and CHAP.match(s) is not None and "\n" not in t


def paragraphs(text):
    """Return paragraph blocks with char offsets. Handles both blank-line-separated prose and
    single-newline (one-line-per-paragraph) formatting; in the latter each non-blank line is a
    paragraph so oversized scenes still have boundaries to snap to."""
    lines = text.split("\n")
    blank = sum(1 for l in lines if not l.strip())
    single_line_mode = blank / max(1, len(lines)) < 0.02
    paras, offset = [], 0
    if single_line_mode:
        blanks = 0
        for ln in lines:
            if ln.strip():
                paras.append({"start": offset, "end": offset + len(ln), "text": ln, "gap_before": blanks})
                blanks = 0
            else:
                blanks += 1
            offset += len(ln) + 1
        return paras
    cur, cur_start, blanks, gap = [], 0, 0, 0
    for ln in lines:
        if ln.strip() == "":
            if cur:
                paras.append({"start": cur_start, "end": cur_start + sum(len(x) + 1 for x in cur) - 1,
                              "text": "\n".join(cur), "gap_before": gap})
                cur = []
            blanks += 1
        else:
            if not cur:
                gap = blanks; cur_start = offset
            blanks = 0
            cur.append(ln)
        offset += len(ln) + 1
    if cur:
        paras.append({"start": cur_start, "end": cur_start + sum(len(x) + 1 for x in cur) - 1,
                      "text": "\n".join(cur), "gap_before": gap})
    return paras


def classify(paras):
    for p in paras:
        p["role"] = "chapter" if is_chapter(p["text"]) else "ornament" if is_ornament(p["text"]) else "prose"
    return paras


def build_scenes(paras):
    scenes, cur, cur_break, prev_role = [], [], "soft", None
    for p in paras:
        if p["role"] in ("chapter", "ornament"):
            if cur:
                scenes.append({"start_break": cur_break, "paras": cur}); cur = []
            prev_role = p["role"]; continue
        newbreak = prev_role if prev_role in ("chapter", "ornament") else \
            ("scene_gap" if p["gap_before"] >= 2 else None)
        if newbreak and cur:
            scenes.append({"start_break": cur_break, "paras": cur}); cur = []
        if not cur:
            cur_break = newbreak if newbreak else "soft"
        cur.append(p); prev_role = "prose"
    if cur:
        scenes.append({"start_break": cur_break, "paras": cur})
    return scenes


def wc(text):
    return len(text.split())


def split_oversized(paras, maxw=1800, target=1200, minw=600):
    if wc("\n\n".join(p["text"] for p in paras)) <= maxw:
        return [(paras, "single")]
    chunks, cur, cw = [], [], 0
    for p in paras:
        w = wc(p["text"])
        if cur and cw + w > target and cw >= minw:
            chunks.append((cur, "length")); cur, cw = [], 0
        cur.append(p); cw += w
    if cur:
        chunks.append((cur, "length"))
    return chunks


def dominant_name(text):
    toks = re.findall(r"\b[A-Z][a-z]{2,}\b", text)
    freq = {}
    for t in toks:
        if t not in STOP_NAMES:
            freq[t] = freq.get(t, 0) + 1
    if not freq:
        return None, 0
    top = sorted(freq.items(), key=lambda x: -x[1])
    return top[0][0], top[0][1]


def analyze(text, start_break, end_break, paras):
    words = wc(text)
    dq = sum(1 for p in paras if '"' in p["text"] or "“" in p["text"])
    dialogue_ratio = round(dq / max(1, len(paras)), 2)
    action = round(100 * len(ACTION.findall(text)) / max(1, words), 2)
    if dialogue_ratio >= 0.5:
        fn = "dialogue_heavy"
    elif action >= 1.2 and dialogue_ratio < 0.35:
        fn = "action_heavy"
    else:
        fn = "exposition_or_discovery"
    hard = {"chapter", "ornament", "scene_gap"}
    bc = "high" if start_break in hard and end_break in hard else \
         "medium" if start_break in hard or end_break in hard else "low"
    first = text.split(".")[0].split()
    if start_break in hard:
        dep = "low"
    elif first and first[0] in {"He", "She", "They", "It", "His", "Her"} and not any(
            re.match(r"[A-Z][a-z]{2,}", w) and w not in STOP_NAMES for w in first[:15]):
        dep = "high"
    else:
        dep = "medium"
    last = text.rstrip()[-1:] if text.strip() else ""
    complete = last in ".!?\"'”’)" and (text.count('"') % 2 == 0)
    name, cnt = dominant_name(text)
    vp = "stable" if cnt >= 3 else "unknown"
    coh = "high" if bc == "high" and complete and dep == "low" else \
          "low" if (not complete) or dep == "high" else "medium"
    return {"word_count": words, "estimated_token_count": round(words / 0.75),
            "dialogue_ratio": dialogue_ratio, "action_score": action,
            "suggested_scene_function": fn, "boundary_confidence": bc,
            "opening_context_dependency": dep,
            "closing_completeness": "complete" if complete else "partial",
            "viewpoint_stability": vp, "scene_coherence": coh}


def select(cands, lo=12, hi=16):
    ok = [c for c in cands if 400 <= c["word_count"] <= 1800]
    if len(ok) <= hi:
        return ok
    ok.sort(key=lambda c: c["start_offset"])
    idx = [round(i * (len(ok) - 1) / (hi - 1)) for i in range(hi)]
    seen, out = set(), []
    for i in idx:
        if i not in seen:
            seen.add(i); out.append(ok[i])
    return out


def process_source(fn, norm_sha):
    text = open(os.path.join(NORM_DIR, fn), encoding="utf-8").read()
    paras = classify(paragraphs(text))
    scenes = build_scenes(paras)
    units = []
    for sc in scenes:
        chunks = split_oversized(sc["paras"])
        for ci, (chunk, how) in enumerate(chunks):
            units.append({"paras": chunk, "start": chunk[0]["start"], "end": chunk[-1]["end"],
                          "start_break": sc["start_break"] if ci == 0 else "length",
                          "end_break": None})
    # merge tiny units forward
    merged, i = [], 0
    while i < len(units):
        u = units[i]
        uw = wc(text[u["start"]:u["end"]])
        if uw < 400 and i + 1 < len(units) and uw + wc(text[units[i + 1]["start"]:units[i + 1]["end"]]) <= 1800:
            nxt = units[i + 1]
            merged.append({"start": u["start"], "end": nxt["end"], "start_break": u["start_break"],
                           "end_break": None, "paras": u["paras"] + nxt["paras"]})
            i += 2
        else:
            merged.append(u); i += 1
    # end_break: from the next unit's start_break
    for j, u in enumerate(merged):
        nxt = merged[j + 1] if j + 1 < len(merged) else None
        u["end_break"] = (nxt["start_break"] if nxt and nxt["start_break"] in ("chapter", "ornament", "scene_gap")
                          else "eof" if not nxt else "soft")
    cands = []
    for u in merged:
        seg = text[u["start"]:u["end"]]
        if not (400 <= wc(seg) <= 1800):
            continue
        meta = analyze(seg, u["start_break"], u["end_break"], u["paras"])
        cands.append({"source_filename": fn, "start_offset": u["start"], "end_offset": u["end"],
                      "start_break": u["start_break"], "end_break": u["end_break"], "paras": u["paras"],
                      **meta})
    chosen = select(cands)
    return text, paras, chosen


def context(paras, cand_start, cand_end, n=2):
    before = [p["text"] for p in paras if p["role"] == "prose" and p["end"] <= cand_start][-n:]
    after = [p["text"] for p in paras if p["role"] == "prose" and p["start"] >= cand_end][:n]
    return before, after


def main():
    nm = {e["filename"]: e for e in json.load(open(NORM_MANIFEST, encoding="utf-8"))["files"]}
    os.makedirs(TARGETS, exist_ok=True)
    all_rows, stats = [], {}
    for fn, e in nm.items():
        stem = os.path.splitext(fn)[0]
        text, paras, chosen = process_source(fn, e["normalized_sha256"])
        fn_stats = {"candidates": 0, "functions": {}}
        for i, c in enumerate(chosen, 1):
            pid = f"{stem}-p{i:02d}"
            seg = text[c["start_offset"]:c["end_offset"]]
            row = {"passage_id": pid, "source_filename": fn, "source_sha256": e["normalized_sha256"],
                   "start_character_offset": c["start_offset"], "end_character_offset": c["end_offset"],
                   "start_line_if_available": None, "end_line_if_available": None,
                   "target_word_count": c["word_count"], "target_token_count": c["estimated_token_count"],
                   "target_sha256": hashlib.sha256(seg.encode("utf-8")).hexdigest(),
                   "segmentation_method": f"{c['start_break']}+{c['end_break']}",
                   "segmentation_confidence": c["boundary_confidence"],
                   "human_review_status": "pending",
                   "scene_function": c["suggested_scene_function"],
                   "passage_properties": {"dialogue_ratio": c["dialogue_ratio"],
                       "action_density": c["action_score"], "closure_type": c["closing_completeness"],
                       "viewpoint_distance": c["viewpoint_stability"]},
                   "diagnostics": {"opening_context_dependency": c["opening_context_dependency"],
                       "closing_completeness": c["closing_completeness"],
                       "viewpoint_stability": c["viewpoint_stability"], "scene_coherence": c["scene_coherence"]},
                   "segmentation_version": SEG_VERSION}
            all_rows.append(row)
            before, after = context(paras, c["start_offset"], c["end_offset"])
            # per-candidate PRIVATE payload for the review app (prose stays here, git-ignored)
            json.dump({"passage_id": pid, "source_filename": fn, "word_count": c["word_count"],
                       "scene_function": c["suggested_scene_function"], "text": seg,
                       "paragraphs": [{"offset": p["start"], "text": p["text"]} for p in c["paras"]],
                       "context_before": before, "context_after": after,
                       "start_offset": c["start_offset"], "end_offset": c["end_offset"]},
                      open(os.path.join(TARGETS, pid + ".json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            fn_stats["candidates"] += 1
            fn_stats["functions"][c["suggested_scene_function"]] = \
                fn_stats["functions"].get(c["suggested_scene_function"], 0) + 1
        stats[fn] = fn_stats
    with open(CAND, "w", encoding="utf-8", newline="\n") as fh:
        for r in all_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"sources": len(stats), "total_candidates": len(all_rows),
                      "per_source": {k: v["candidates"] for k, v in stats.items()},
                      "functions_overall": _agg(stats)}, indent=1))


def _agg(stats):
    out = {}
    for v in stats.values():
        for f, c in v["functions"].items():
            out[f] = out.get(f, 0) + c
    return out


if __name__ == "__main__":
    main()
