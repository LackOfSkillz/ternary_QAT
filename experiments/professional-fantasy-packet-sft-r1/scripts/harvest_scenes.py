"""Dispatch 30A-R1 — Phase 2 (corrected): curated representative scene harvesting.

Works only inside each source's narrative body (front/back matter excluded). Builds larger,
scene-aligned candidate chunks (1800-3000 preferred, 1400-4000 acceptable, >4500 flagged for manual),
sampled across early/middle/late regions. Produces an ELEVEN-SOURCE calibration batch: one
representative candidate per file, diversified by region and scene emphasis. Private outputs
(offsets/text git-ignored); prints metadata only, no prose.
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from segment_scenes import paragraphs, classify, build_scenes, wc, dominant_name, ACTION, STOP_NAMES  # noqa: E402

NORM_DIR = os.path.join(EXP, "private-data", "normalized-sources")
BODY_MAP = os.path.join(EXP, "private-data", "narrative-body-map.json")
TARGETS = os.path.join(EXP, "private-data", "targets")
CAND = os.path.join(EXP, "manifests", "candidate-passages.jsonl")
HARVEST_VERSION = "harvest-v1"

REGIONS = {"early": (20, 40), "middle": (40, 65), "late": (65, 90)}
# per-source assignment (order follows the body map); region rotation + emphasis rotation for diversity
REGION_ROT = ["early", "middle", "late", "middle", "late", "early", "middle", "late", "early", "middle", "late"]
EMPHASIS_ROT = ["dialogue", "action", "discovery", "worldbuilding", "character", "aftermath",
                "tension", "travel", "political", "dialogue", "action"]


def _uw(u):
    return wc("\n".join(p["text"] for p in u["paras"]))


def chunks_for(text, body_start, body_end):
    paras = classify(paragraphs(text))
    body = [p for p in paras if p["start"] >= body_start and p["end"] <= body_end]
    scenes = build_scenes(body)
    # expand oversized scenes into paragraph-boundary sub-units (~2400w) so no source is dropped;
    # a length-split boundary is marked so the reviewer can flag it.
    units, manual = [], 0
    for sc in scenes:
        if wc("\n".join(p["text"] for p in sc["paras"])) <= 4000:
            units.append({"paras": sc["paras"], "start_break": sc["start_break"]})
            continue
        manual += 1
        cur, cw, first = [], 0, True
        for p in sc["paras"]:
            pw = wc(p["text"])
            if cur and cw + pw > 2400 and cw >= 1400:
                units.append({"paras": cur, "start_break": sc["start_break"] if first else "length"})
                first, cur, cw = False, [], 0
            cur.append(p); cw += pw
        if cur:
            units.append({"paras": cur, "start_break": sc["start_break"] if first else "length"})
    # merge small units up to 1800-3000
    out, cur, cw = [], [], 0
    for u in units:
        cur.append(u); cw += _uw(u)
        if cw >= 1800:
            paras_all = [p for uu in cur for p in uu["paras"]]
            out.append({"start": paras_all[0]["start"], "end": paras_all[-1]["end"],
                        "start_break": cur[0]["start_break"], "paras": paras_all})
            cur, cw = [], 0
    if cur and cw >= 1400:
        paras_all = [p for uu in cur for p in uu["paras"]]
        out.append({"start": paras_all[0]["start"], "end": paras_all[-1]["end"],
                    "start_break": cur[0]["start_break"], "paras": paras_all})
    return paras, out, manual


def analyze(text, start_break, paras_slice):
    words = wc(text)
    dq = sum(1 for p in paras_slice if '"' in p["text"] or "“" in p["text"])
    dr = round(dq / max(1, len(paras_slice)), 2)
    act = round(100 * len(ACTION.findall(text)) / max(1, words), 2)
    fn = "dialogue_heavy" if dr >= 0.30 else "action_heavy" if act >= 0.5 and dr < 0.30 else "exposition_or_discovery"
    hard = {"chapter", "ornament", "scene_gap"}
    first = text.split(".")[0].split()
    dep = "low" if start_break in hard else (
        "high" if first and first[0] in {"He", "She", "They", "It", "His", "Her"} and not any(
            re.match(r"[A-Z][a-z]{2,}", w) and w not in STOP_NAMES for w in first[:15]) else "medium")
    last = text.rstrip()[-1:] if text.strip() else ""
    complete = last in ".!?\"'”’)" and text.count('"') % 2 == 0
    name, cnt = dominant_name(text)
    return {"word_count": words, "dialogue_ratio": dr, "action_density": act, "scene_function": fn,
            "opening_context_dependency": dep, "closing_completeness": "complete" if complete else "partial",
            "viewpoint_summary": name if cnt >= 3 else "unclear"}


def pick(chunks, text, body_start, body_end, region, emphasis):
    lo, hi = REGIONS[region]
    span = max(1, body_end - body_start)
    def pct(c): return 100 * ((c["start"] + c["end"]) / 2 - body_start) / span
    scored = []
    for c in chunks:
        seg = text[c["start"]:c["end"]]
        a = analyze(seg, c["start_break"], c["paras"])
        p = pct(c)
        in_region = lo <= p <= hi
        emphasis_val = a["dialogue_ratio"] if emphasis in ("dialogue", "character") else \
            a["action_density"] / 5 if emphasis in ("action", "tension", "travel") else \
            (1 - a["dialogue_ratio"])  # discovery/worldbuilding/aftermath/political -> calmer
        quality = (1 if a["closing_completeness"] == "complete" else 0) + \
                  (1 if a["opening_context_dependency"] == "low" else 0) + \
                  (1 if 1800 <= a["word_count"] <= 3000 else 0)
        region_pen = 0 if in_region else -abs(p - (lo + hi) / 2) / 100
        scored.append((in_region, emphasis_val + quality + region_pen, c, a, round(p, 1)))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return scored[0] if scored else None


def context(paras, s, e, n=2):
    before = [p["text"] for p in paras if p["role"] == "prose" and p["end"] <= s][-n:]
    after = [p["text"] for p in paras if p["role"] == "prose" and p["start"] >= e][:n]
    return before, after


def main():
    bm = json.load(open(BODY_MAP, encoding="utf-8"))["sources"]
    os.makedirs(TARGETS, exist_ok=True)
    rows, report = [], []
    for i, (fn, m) in enumerate(bm.items()):
        text = open(os.path.join(NORM_DIR, fn), encoding="utf-8").read()
        paras, chunks, manual = chunks_for(text, m["narrative_start_offset"], m["narrative_end_offset"])
        if not chunks:
            report.append({"source_filename": fn, "error": "no chunks"}); continue
        region, emphasis = REGION_ROT[i % 11], EMPHASIS_ROT[i % 11]
        best = pick(chunks, text, m["narrative_start_offset"], m["narrative_end_offset"], region, emphasis)
        _, _, c, a, pctv = best
        stem = os.path.splitext(fn)[0]
        pid = f"{stem}-c01"
        seg = text[c["start"]:c["end"]]
        # chapter ordinal preceding this offset (count chapter-heading paras before start)
        chap_ord = sum(1 for p in paras if p["role"] == "chapter" and p["end"] <= c["start"]
                       and p["start"] >= m["narrative_start_offset"])
        narrative_region = "early" if pctv < 40 else "middle" if pctv < 65 else "late"
        row = {"passage_id": pid, "source_filename": fn, "source_sha256": m["source_sha256"],
               "start_character_offset": c["start"], "end_character_offset": c["end"],
               "start_line_if_available": None, "end_line_if_available": None,
               "target_word_count": a["word_count"], "target_token_count": round(a["word_count"] / 0.75),
               "target_sha256": hashlib.sha256(seg.encode("utf-8")).hexdigest(),
               "narrative_region": narrative_region, "approximate_source_percent": pctv,
               "chapter_or_section": f"body-ch{chap_ord}",
               "segmentation_method": f"{c['start_break']}+scene_merge",
               "segmentation_confidence": "high" if a["opening_context_dependency"] == "low" and a["closing_completeness"] == "complete" else "medium",
               "human_review_status": "pending", "scene_function": a["scene_function"],
               "assigned_region": region, "assigned_emphasis": emphasis,
               "viewpoint_summary": a["viewpoint_summary"],
               "passage_properties": {"dialogue_ratio": a["dialogue_ratio"], "action_density": a["action_density"]},
               "diagnostics": {"opening_context_dependency": a["opening_context_dependency"],
                               "closing_completeness": a["closing_completeness"],
                               "manual_flag_oversized_scenes": manual},
               "harvest_version": HARVEST_VERSION}
        rows.append(row)
        before, after = context(paras, c["start"], c["end"])
        json.dump({"passage_id": pid, "source_filename": fn, "word_count": a["word_count"],
                   "scene_function": a["scene_function"], "narrative_region": narrative_region,
                   "approximate_source_percent": pctv, "viewpoint_summary": a["viewpoint_summary"],
                   "text": seg, "paragraphs": [{"offset": p["start"], "text": p["text"]} for p in c["paras"]],
                   "context_before": before, "context_after": after,
                   "start_offset": c["start"], "end_offset": c["end"]},
                  open(os.path.join(TARGETS, pid + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        report.append({"source_filename": fn, "passage_id": pid, "word_count": a["word_count"],
                       "narrative_region": narrative_region, "approximate_source_percent": pctv,
                       "chapter_or_section": f"body-ch{chap_ord}", "scene_function": a["scene_function"],
                       "boundary_method": row["segmentation_method"], "confidence": row["segmentation_confidence"],
                       "assigned": f"{region}/{emphasis}"})
    with open(CAND, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    json.dump({"dispatch": "30A-R1", "harvest_version": HARVEST_VERSION, "calibration_batch": report,
               "count": len(rows)},
              open(os.path.join(EXP, "reports", "calibration-batch.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"calibration_candidates": len(rows),
                      "sources": [r["source_filename"] for r in report if "passage_id" in r]}, indent=1))


if __name__ == "__main__":
    main()
