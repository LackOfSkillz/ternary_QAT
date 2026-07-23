"""Dispatch 30A-R1 — Phase: harvest the additional 55 candidates (5 per source), round-robin, to
reach 6/source (the accepted c01 + 5 new). Reuses the curated body-scoped harvester, excludes the
already-accepted c01 span, and spreads the 5 across the six-function target mix and early/middle/late
regions. Writes the new candidates to candidate-passages.jsonl (private) + per-candidate targets
(private) and a metadata-only report. No prose printed.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from harvest_scenes import chunks_for, analyze, context, REGIONS  # noqa: E402

NORM_DIR = os.path.join(EXP, "private-data", "normalized-sources")
BODY_MAP = os.path.join(EXP, "private-data", "narrative-body-map.json")
ACCEPTED = os.path.join(EXP, "manifests", "accepted-passages.jsonl")
TARGETS = os.path.join(EXP, "private-data", "targets")
CAND = os.path.join(EXP, "manifests", "candidate-passages.jsonl")
HARVEST_VERSION = "harvest-v1-round2"

# 5 remaining function slots (the 6th was filled by c01); region spread across the body
SLOTS = [("dialogue", "early"), ("action", "late"), ("discovery", "middle"),
         ("worldbuilding", "late"), ("quiet_aftermath", "early")]


def emphasis_val(a, emphasis):
    dr, ac = a["dialogue_ratio"], a["action_density"]
    if emphasis == "dialogue":
        return dr
    if emphasis == "action":
        return ac / 5
    if emphasis == "discovery":
        return 0.5 - abs(dr - 0.25)          # mid dialogue
    return 1 - dr - ac / 10                    # worldbuilding / quiet_aftermath = calmer


def overlaps(a, b0, b1):
    return not (a["end"] <= b0 or a["start"] >= b1)


def pick_for_slot(chunks, text, bs, be, emphasis, region, used):
    lo, hi = REGIONS[region]
    span = max(1, be - bs)
    scored = []
    for c in chunks:
        if id(c) in used:
            continue
        seg = text[c["start"]:c["end"]]
        a = analyze(seg, c["start_break"], c["paras"])
        pct = 100 * ((c["start"] + c["end"]) / 2 - bs) / span
        in_region = lo <= pct <= hi
        quality = (1 if a["closing_completeness"] == "complete" else 0) + \
                  (1 if a["opening_context_dependency"] == "low" else 0) + \
                  (1 if 1800 <= a["word_count"] <= 3000 else 0)
        region_pen = 0 if in_region else -abs(pct - (lo + hi) / 2) / 100
        scored.append((in_region, emphasis_val(a, emphasis) + quality + region_pen, c, a, round(pct, 1)))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return scored[0] if scored else None


def main():
    bm = json.load(open(BODY_MAP, encoding="utf-8"))["sources"]
    acc = {r["passage_id"]: r for r in (json.loads(l) for l in open(ACCEPTED, encoding="utf-8") if l.strip())}
    os.makedirs(TARGETS, exist_ok=True)
    rows, report, rejected = [], [], 0
    for fn, m in bm.items():
        stem = os.path.splitext(fn)[0]
        c01 = acc.get(f"{stem}-c01", {})
        c0s, c0e = c01.get("start_character_offset", -1), c01.get("end_character_offset", -1)
        text = open(os.path.join(NORM_DIR, fn), encoding="utf-8").read()
        _, chunks, _ = chunks_for(text, m["narrative_start_offset"], m["narrative_end_offset"])
        chunks = [c for c in chunks if not overlaps(c, c0s, c0e)]
        used = set()
        for i, (emphasis, region) in enumerate(SLOTS, start=2):
            best = pick_for_slot(chunks, text, m["narrative_start_offset"], m["narrative_end_offset"],
                                 emphasis, region, used)
            if not best:
                rejected += 1
                continue
            _, _, c, a, pct = best
            used.add(id(c))
            pid = f"{stem}-c{i:02d}"
            seg = text[c["start"]:c["end"]]
            chap = sum(1 for p in _all_paras(text) if False)  # (cheap; chapter ordinal omitted for round2)
            nr = "early" if pct < 40 else "middle" if pct < 65 else "late"
            rows.append({"passage_id": pid, "source_filename": fn, "source_sha256": m["source_sha256"],
                         "start_character_offset": c["start"], "end_character_offset": c["end"],
                         "target_word_count": a["word_count"], "target_token_count": round(a["word_count"] / 0.75),
                         "target_sha256": hashlib.sha256(seg.encode()).hexdigest(),
                         "narrative_region": nr, "approximate_source_percent": pct,
                         "chapter_or_section": "body", "segmentation_method": f"{c['start_break']}+scene_merge",
                         "segmentation_confidence": "high" if a["opening_context_dependency"] == "low" and a["closing_completeness"] == "complete" else "medium",
                         "human_review_status": "pending", "scene_function": a["scene_function"],
                         "assigned_region": region, "assigned_emphasis": emphasis,
                         "viewpoint_summary": a["viewpoint_summary"],
                         "passage_properties": {"dialogue_ratio": a["dialogue_ratio"], "action_density": a["action_density"]},
                         "diagnostics": {"opening_context_dependency": a["opening_context_dependency"],
                                         "closing_completeness": a["closing_completeness"]},
                         "harvest_version": HARVEST_VERSION})
            before, after = context(_all_paras(text), c["start"], c["end"])
            json.dump({"passage_id": pid, "source_filename": fn, "word_count": a["word_count"],
                       "scene_function": a["scene_function"], "narrative_region": nr,
                       "approximate_source_percent": pct, "viewpoint_summary": a["viewpoint_summary"],
                       "text": seg, "paragraphs": [{"offset": p["start"], "text": p["text"]} for p in c["paras"]],
                       "context_before": before, "context_after": after,
                       "start_offset": c["start"], "end_offset": c["end"]},
                      open(os.path.join(TARGETS, pid + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            report.append({"passage_id": pid, "source_filename": fn, "word_count": a["word_count"],
                           "narrative_region": nr, "assigned_emphasis": emphasis, "scene_function": a["scene_function"]})
    # write ONLY the 55 new candidates to the (git-ignored) candidate manifest for the review queue
    with open(CAND, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    words = [r["word_count"] for r in report]
    toks = [round(w / 0.75) for w in words]
    summary = {"dispatch": "30A-R1", "harvest_version": HARVEST_VERSION,
               "new_candidates": len(rows), "rejected_during_harvest": rejected,
               "candidates_by_source": dict(Counter(r["source_filename"] for r in report)),
               "candidates_by_assigned_emphasis": dict(Counter(r["assigned_emphasis"] for r in report)),
               "candidates_by_scene_function": dict(Counter(r["scene_function"] for r in report)),
               "word_count_range": [min(words), max(words)] if words else None,
               "estimated_token_range": [min(toks), max(toks)] if toks else None,
               "narrative_region_distribution": dict(Counter(r["narrative_region"] for r in report))}
    json.dump(summary, open(os.path.join(EXP, "reports", "harvest-round2.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(summary, indent=1))


def _all_paras(text):
    from harvest_scenes import paragraphs, classify
    if not hasattr(_all_paras, "_c"):
        _all_paras._c = {}
    if text not in _all_paras._c:
        _all_paras._c[text] = classify(paragraphs(text))
    return _all_paras._c[text]


if __name__ == "__main__":
    main()
