#!/usr/bin/env python3
"""Gate 0 v2 — corpus-level signature scan across ALL Dataset A records.

Surfaces monoculture risk: recurring comparative frames ("the way ..."),
`not X, but Y` constructions, em-dash frequency by family/profile and by
source-vs-gold, poised-final-image endings, repeated sentence openings,
cross-record n-gram overlap, tricolon constructions, and cross-profile
similarity. It flags patterns for REVIEW; it does NOT adjudicate literary
quality and it does NOT approve or reject any record. Every metric is labeled
deterministic | heuristic.

Usage:
  python analyze_corpus_signatures.py --root datasets/dataset-a \
      --out-json <path.json> --out-md <path.md>
"""
import argparse
import difflib
import glob
import json
import os
import re
from collections import Counter, defaultdict

import yaml

# thresholds are REVIEW triggers, never FAIL — these scans expose monoculture
# risk, they do not decide correctness.
THRESH_THE_WAY = 3          # >= this many records using "the way ..." -> REVIEW
THRESH_NOT_BUT = 2
THRESH_FINAL_IMAGE = 4      # concentration of poised short-image endings
THRESH_TRICOLON = 3
THRESH_OPENING = 3          # same gold sentence-opening word across records
THRESH_NGRAM = 1            # any shared 4-gram between different records -> REVIEW
THRESH_PROFILE_SIM = 0.55   # cross-profile gold similarity


def parse(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    fm = yaml.safe_load(m.group(1))
    body = m.group(2)
    secs, cur, buf = {}, None, []
    for line in body.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            if cur:
                secs[cur] = "\n".join(buf).strip()
            cur, buf = h.group(1), []
        else:
            buf.append(line)
    if cur:
        secs[cur] = "\n".join(buf).strip()
    return fm, secs


def sentences(t):
    return [re.sub(r"\s+", " ", s.strip())
            for s in re.split(r"(?<=[.!?])\s+", (t or "").strip()) if s.strip()]


def words(t):
    return re.findall(r"[A-Za-z']+", t or "")


def status(count, thresh):
    return "REVIEW" if count >= thresh else "OK"


def strip_fences(t):
    """Remove fenced ```...``` code/JSON blocks so voice scans see prose only."""
    return re.sub(r"```.*?```", " ", t or "", flags=re.S)


def gold_prose(gold):
    """The narrative prose of a gold: the `text` field of a structured revision
    object if present, else the gold with fenced (JSON/contract) blocks removed."""
    m = re.search(r"```(?:json)?\s*(.*?)```", gold or "", re.S)
    if m:
        try:
            obj = json.loads(m.group(1))
            if isinstance(obj, dict) and "text" in obj:
                return obj["text"]
        except Exception:
            pass
    return strip_fences(gold)


def load_records(root):
    recs = []
    for f in sorted(glob.glob(os.path.join(root, "drafts", "**", "*.md"), recursive=True)):
        fm, secs = parse(f)
        src = secs.get("Context", "")
        gold = secs.get("Gold Response", "")
        recs.append({
            "id": fm.get("id"), "task_type": fm.get("task_type"),
            "style_profile": fm.get("style_profile") or "none",
            # prose views (fences/JSON removed) drive the voice-signature scans
            "source": strip_fences(src),
            "gold": gold_prose(gold),
        })
    return recs


def scan_phrase(recs, pattern, label):
    """Count records containing `pattern` in source and/or gold (deterministic)."""
    rx = re.compile(pattern, re.I)
    hits, locs = [], {}
    for r in recs:
        in_src = bool(rx.search(r["source"]))
        in_gold = bool(rx.search(r["gold"]))
        if in_src or in_gold:
            hits.append(r["id"])
            where = []
            if in_src:
                where.append("source")
            if in_gold:
                where.append("gold")
            locs[r["id"]] = "+".join(where)
    profiles = sorted({r["style_profile"] for r in recs if r["id"] in hits})
    return {"pattern": label, "count": len(hits), "records": hits,
            "locations": locs, "profiles": profiles, "kind": "deterministic"}


def em_dash_frequency(recs):
    by_family_src = Counter()
    by_family_gold = Counter()
    by_profile_gold = Counter()
    total_src = total_gold = 0
    for r in recs:
        s = r["source"].count("—")
        g = r["gold"].count("—")
        total_src += s
        total_gold += g
        by_family_src[r["task_type"]] += s
        by_family_gold[r["task_type"]] += g
        by_profile_gold[r["style_profile"]] += g
    return {"kind": "deterministic", "total_source": total_src, "total_gold": total_gold,
            "by_family_source": dict(by_family_src), "by_family_gold": dict(by_family_gold),
            "by_profile_gold": dict(by_profile_gold)}


def _short_image_ending(text):
    ss = sentences(text)
    if not ss:
        return None
    last = ss[-1]
    if '"' not in last and len(words(last)) <= 12 and not last.endswith("?"):
        return last
    return None


def final_image_endings(recs):
    """Heuristic proxy for the 'repeated poised final image' pattern: a passage
    whose LAST sentence carries no dialogue and is short (<= 12 words). Measured on
    BOTH source and gold prose; the source concentration is the primary signal
    (the pattern is largely inherited from the source passages)."""
    src_hits, gold_hits = [], []
    for r in recs:
        s = _short_image_ending(r["source"])
        g = _short_image_ending(r["gold"])
        if s:
            src_hits.append({"id": r["id"], "ending": s})
        if g:
            gold_hits.append({"id": r["id"], "ending": g})
    return {"kind": "heuristic",
            "source_count": len(src_hits), "gold_count": len(gold_hits),
            "source_examples": src_hits, "gold_examples": gold_hits,
            "source_records": [h["id"] for h in src_hits],
            "gold_records": [h["id"] for h in gold_hits]}


def repeated_openings(recs):
    """Most common first word across all gold sentences (anaphora/monoculture proxy)."""
    first_words = Counter()
    owners = defaultdict(set)
    for r in recs:
        for s in sentences(r["gold"]):
            w = words(s)
            if w:
                fw = w[0].lower()
                first_words[fw] += 1
                owners[fw].add(r["id"])
    top = [{"word": w, "count": c, "records": sorted(owners[w])}
           for w, c in first_words.most_common(6) if len(owners[w]) >= THRESH_OPENING]
    return {"kind": "heuristic", "top_openings": top}


def cross_record_ngrams(recs, n=4):
    """Shared n-grams appearing in DIFFERENT records' gold texts (deterministic)."""
    def grams(t):
        w = [x.lower() for x in words(t)]
        return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}
    owners = defaultdict(set)
    for r in recs:
        for g in grams(r["gold"]):
            owners[g].add(r["id"])
    shared = [{"ngram": g, "records": sorted(rs)}
              for g, rs in owners.items() if len(rs) >= 2]
    shared.sort(key=lambda x: (-len(x["records"]), x["ngram"]))
    return {"kind": "deterministic", "n": n, "count": len(shared), "shared": shared[:20]}


def tricolon(recs):
    rx = re.compile(r"\b\w+,\s+\w+,\s+and\s+\w+\b")
    hits, locs = [], {}
    for r in recs:
        s = len(rx.findall(r["source"]))
        g = len(rx.findall(r["gold"]))
        if s or g:
            hits.append(r["id"])
            locs[r["id"]] = f"source={s} gold={g}"
    return {"pattern": "tricolon (X, Y, and Z)", "count": len(hits),
            "records": hits, "locations": locs, "kind": "deterministic"}


def cross_profile_similarity(recs):
    """Heuristic: gold-text similarity between records of DIFFERENT profiles."""
    warns = []
    for i in range(len(recs)):
        for j in range(i + 1, len(recs)):
            a, b = recs[i], recs[j]
            if a["style_profile"] == b["style_profile"] or a["style_profile"] == "none":
                continue
            ratio = difflib.SequenceMatcher(None, words(a["gold"]),
                                            words(b["gold"])).ratio()
            if ratio >= THRESH_PROFILE_SIM:
                warns.append({"a": a["id"], "b": b["id"],
                              "profiles": [a["style_profile"], b["style_profile"]],
                              "similarity": round(ratio, 3)})
    warns.sort(key=lambda x: -x["similarity"])
    return {"kind": "heuristic", "count": len(warns), "warnings": warns}


def build(root):
    recs = load_records(root)
    the_way = scan_phrase(recs, r"\bthe way\b", "the way ...")
    not_but = scan_phrase(recs, r"\bnot\b[^.,]{0,40},?\s+but\b", "not X, but Y")
    tri = tricolon(recs)
    return {
        "record_count": len(recs),
        "the_way": the_way,
        "not_but": not_but,
        "tricolon": tri,
        "em_dash": em_dash_frequency(recs),
        "final_image_endings": final_image_endings(recs),
        "repeated_openings": repeated_openings(recs),
        "cross_record_ngrams": cross_record_ngrams(recs),
        "cross_profile_similarity": cross_profile_similarity(recs),
    }


def md(report):
    L = ["# Gate 0 v2 — Corpus Signature Report", "",
         f"Scanned **{report['record_count']}** records (source + gold). These scans",
         "expose **monoculture risk** across the corpus. Thresholds emit **REVIEW**,",
         "never FAIL — they do not adjudicate literary quality. Metrics are labeled",
         "deterministic | heuristic.", ""]

    def phrase_block(rep, thresh):
        st = status(rep["count"], thresh)
        locs = "; ".join(f"{rid} ({rep['locations'][rid]})" for rid in rep["records"])
        return [f"### Pattern: `{rep['pattern']}`  ({rep['kind']})",
                f"- Count (records): **{rep['count']}**  | Threshold: {thresh}  | Status: **{st}**",
                f"- Profiles affected: {', '.join(rep['profiles']) or 'n/a'}",
                f"- Records: {locs or 'none'}", ""]

    L += phrase_block(report["the_way"], THRESH_THE_WAY)
    L += phrase_block(report["not_but"], THRESH_NOT_BUT)

    tri = report["tricolon"]
    st = status(tri["count"], THRESH_TRICOLON)
    L += [f"### Pattern: `{tri['pattern']}`  ({tri['kind']})",
          f"- Count (records): **{tri['count']}**  | Threshold: {THRESH_TRICOLON}  | Status: **{st}**",
          f"- Records: {'; '.join(f'{k} ({v})' for k, v in tri['locations'].items()) or 'none'}", ""]

    ed = report["em_dash"]
    L += ["### Em-dash frequency  (deterministic)",
          f"- Total em dashes — source: **{ed['total_source']}**, gold: **{ed['total_gold']}**",
          f"- By family (gold): {ed['by_family_gold']}",
          f"- By family (source): {ed['by_family_source']}",
          f"- By profile (gold): {ed['by_profile_gold']}",
          "- Status: **REVIEW** — confirm em dashes are earned per profile, not a "
          "teacher tic imported into golds.", ""]

    fi = report["final_image_endings"]
    st = status(fi["source_count"], THRESH_FINAL_IMAGE)
    L += ["### Poised final-image endings  (heuristic proxy)",
          f"- **Source** passages ending on a short (<=12-word) non-dialogue image: "
          f"**{fi['source_count']}**  | Threshold: {THRESH_FINAL_IMAGE}  | Status: **{st}**",
          f"- Source records: {', '.join(fi['source_records']) or 'none'}"]
    for ex in fi["source_examples"]:
        L.append(f"    - {ex['id']}: “{ex['ending']}”")
    L += [f"- **Gold** responses with the same pattern: **{fi['gold_count']}** "
          f"({', '.join(fi['gold_records']) or 'none'})",
          "- Explanation: the poised-closing-image habit is concentrated in the "
          "**source** passages and largely carries into the golds; a high source "
          "concentration is a monoculture signal for Gary's Gate review.", ""]

    ro = report["repeated_openings"]
    L += ["### Repeated sentence openings  (heuristic)"]
    if ro["top_openings"]:
        for o in ro["top_openings"]:
            L.append(f"- “{o['word']}…” opens {o['count']} gold sentences "
                     f"across {len(o['records'])} records: {', '.join(o['records'])}")
    else:
        L.append("- No opening word shared across the REVIEW threshold of records.")
    L.append("")

    ng = report["cross_record_ngrams"]
    st = status(ng["count"], THRESH_NGRAM)
    L += [f"### Cross-record shared {ng['n']}-grams (gold)  (deterministic)",
          f"- Distinct shared {ng['n']}-grams across different records: **{ng['count']}**"
          f"  | Status: **{st}**"]
    for s in ng["shared"][:12]:
        L.append(f"    - “{s['ngram']}” — {', '.join(s['records'])}")
    L.append("")

    cps = report["cross_profile_similarity"]
    st = status(cps["count"], 1)
    L += ["### Cross-profile gold similarity  (heuristic)",
          f"- Pairs of DIFFERENT-profile golds above {THRESH_PROFILE_SIM} similarity: "
          f"**{cps['count']}**  | Status: **{st}**"]
    for w in cps["warnings"][:12]:
        L.append(f"    - {w['a']} vs {w['b']} ({'/'.join(w['profiles'])}): {w['similarity']}")
    L += ["- Explanation: high similarity between golds meant to differ by profile "
          "signals the same repair leaking across voices (SIREP-collapse risk).", ""]

    L += ["---", "",
          "**Discipline:** REVIEW flags are prompts for the Gate 1/2/3 human and",
          "model reviewers. They surface repetition to be judged, not defects to be",
          "auto-fixed. Deterministic counts are exact; heuristic proxies approximate",
          "patterns a tool cannot fully understand.", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()
    report = build(args.root)
    with open(args.out_json, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    with open(args.out_md, "w", encoding="utf-8") as fh:
        fh.write(md(report))
    tw = report["the_way"]
    print(f"corpus scan -> {args.out_md}")
    print(f"  'the way ...': {tw['count']} records {tw['records']}")
    print(f"  final-image endings (source/gold): "
          f"{report['final_image_endings']['source_count']}/"
          f"{report['final_image_endings']['gold_count']}")
    print(f"  em dashes source/gold: {report['em_dash']['total_source']}/"
          f"{report['em_dash']['total_gold']}")


if __name__ == "__main__":
    main()
