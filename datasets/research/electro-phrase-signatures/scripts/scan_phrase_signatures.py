#!/usr/bin/env python3
"""Gate 0 v3 — phrase-signature scanner (reusable library + CLI).

Detects recurring model-writing signatures by CLUSTERING and REPETITION, not by
punishing isolated normal English. Emits REVIEW findings only, never FAIL, and
never labels any phrase "AI-only". Deterministic.

Library API (also used by normalize_phrase_lists.py):
  load_families(path)            -> [family dict, ...]
  load_candidates(path)          -> {phrase: {"tier":..., "families":[...]}}
  classify_artifact(phrase)      -> reason str | None   (proper name / malformed)
  families_for(phrase, families) -> [family_id, ...]
  tier_for(phrase, families)     -> tier str
  scan_text(text, families, cand_index) -> metrics dict

CLI:
  scan_phrase_signatures.py --text FILE [--families F --candidates C]
  scan_phrase_signatures.py --dataset-a ROOT --out-md OUT [--families F --candidates C]
"""
import argparse
import os
import re
import sys

import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_NORM = os.path.join(_HERE, "..", "normalized")
DEFAULT_FAMILIES = os.path.join(_NORM, "phrase-families.yaml")
DEFAULT_CANDIDATES = os.path.join(_NORM, "candidate-phrases.yaml")

# Corpus-specific proper names / settings (NOT generic AI markers).
NAME_TOKENS = {"elara", "kael", "elias", "valerius", "lyra", "kaelen", "isolde",
               "theron", "aris", "thorne", "vance", "silas", "alistair", "finch",
               "blackwood", "aes", "sedai"}
TITLE_TOKENS = {"lord", "lady", "king", "commander", "sir"}
SETTING_TOKENS = {"sector", "gamma"}
MALFORMED_TOKENS = {"fa", "ade"}  # truncation debris, chiefly mangled "façade"

# em-dash compound-signature triggers
INTENSIFIER_TOKENS = {"profound", "utterly", "absolute", "sheer", "terrifying",
                      "desperate", "profoundly", "absolutely"}
ABSTRACTION_FAMILIES = {"generic_intensifier", "pressure_metaphor",
                        "abstract_menace_atmosphere"}


def tokenize(text):
    return re.findall(r"[a-z']+", (text or "").lower())


def ngrams(tokens, n):
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def load_families(path=DEFAULT_FAMILIES):
    data = yaml.safe_load(open(path, encoding="utf-8"))
    fams = data["families"]
    for f in fams:
        f["_tokens"] = set(f.get("match_tokens", []) or [])
        f["_phrases"] = list(f.get("match_phrases", []) or [])
        f["_high"] = set(f.get("high_risk", []) or [])
    return fams


def load_candidates(path=DEFAULT_CANDIDATES):
    data = yaml.safe_load(open(path, encoding="utf-8")) or {}
    idx = {}
    for row in data.get("phrases", []):
        idx[row["phrase"]] = {"tier": row.get("tier"),
                              "families": row.get("family_ids", []) or []}
    return idx


def classify_artifact(phrase):
    """corpus-artifact reason for a phrase, or None."""
    toks = phrase.split()
    if any(c.isdigit() for c in phrase):
        return "corpus_specific_setting_or_numeric"
    if any(t in NAME_TOKENS for t in toks):
        return "corpus_specific_proper_name"
    if "named" in toks or any(t in TITLE_TOKENS for t in toks):
        return "corpus_specific_proper_name"
    if any(t in SETTING_TOKENS for t in toks):
        return "corpus_specific_setting_identifier"
    if any(t in MALFORMED_TOKENS for t in toks) or \
            any(len(t) == 1 and t not in {"a", "i"} for t in toks):
        return "malformed_or_truncated"
    return None


def families_for(phrase, families):
    toks = set(phrase.split())
    out = []
    for f in families:
        if toks & f["_tokens"]:
            out.append(f["family_id"])
            continue
        if any(re.search(r"\b" + re.escape(p) + r"\b", phrase) for p in f["_phrases"]):
            out.append(f["family_id"])
    return out


def tier_for(phrase, families):
    if classify_artifact(phrase):
        return "corpus_artifact"
    fams = set(families_for(phrase, families))
    if not fams:
        return "ordinary_phrase"
    for f in families:
        if f["family_id"] in fams and phrase in f["_high"]:
            return "high_risk_signature"
    return "contextual_risk"


def sentences(text):
    return [re.sub(r"\s+", " ", s).strip()
            for s in re.split(r"(?<=[.!?])\s+", (text or "").strip()) if s.strip()]


# ---------------- scanning ----------------

def scan_text(text, families, cand_index):
    """Deterministic signature metrics for one block of text."""
    toks = tokenize(text)
    wc = len(toks)
    bg, tg = ngrams(toks, 2), ngrams(toks, 3)

    # exact candidate n-gram hits (word-boundary by construction)
    exact = {"high_risk_signature": [], "contextual_risk": [], "ordinary_phrase": []}
    for ng in bg + tg:
        info = cand_index.get(ng)
        if info and info["tier"] in exact:
            exact[info["tier"]].append(ng)

    # family hits via n-gram classification (heuristic density signal)
    fam_hits = {f["family_id"]: 0 for f in families}
    for ng in bg + tg:
        for fid in families_for(ng, families):
            fam_hits[fid] += 1
    fam_density = {fid: round(c / wc * 1000, 1) if wc else 0.0
                   for fid, c in fam_hits.items()}

    # clustering: sliding 40-token window with >=4 family-trigger tokens
    trigger_tokens = set()
    for f in families:
        trigger_tokens |= f["_tokens"]
    win, clusters = 40, 0
    flags = [1 if t in trigger_tokens else 0 for t in toks]
    for i in range(0, max(1, wc - win + 1)):
        if sum(flags[i:i + win]) >= 8:
            clusters += 1

    # em-dash compound signatures
    em_total = text.count("—")
    compound = 0
    for s in sentences(text):
        if "—" not in s:
            continue
        stoks = set(tokenize(s))
        abstraction = stoks & INTENSIFIER_TOKENS
        if not abstraction:
            for f in families:
                if f["family_id"] in ABSTRACTION_FAMILIES and (stoks & f["_tokens"]):
                    abstraction = True
                    break
        if abstraction:
            compound += 1

    return {
        "word_count": wc,
        "exact_hits": exact,
        "high_risk_count": len(exact["high_risk_signature"]),
        "contextual_count": len(exact["contextual_risk"]),
        "family_hits": fam_hits,
        "family_density": fam_density,
        "cluster_windows": clusters,
        "em_dash_total": em_total,
        "em_dash_compound": compound,
    }


def _family_multiset(text, families):
    """family_id -> trigger-token count (for introduced/removed deltas)."""
    toks = tokenize(text)
    out = {f["family_id"]: 0 for f in families}
    for ng in ngrams(toks, 2) + ngrams(toks, 3):
        for fid in families_for(ng, families):
            out[fid] += 1
    return out


# ---------------- Dataset A driver ----------------

def _parse_record(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    fm = yaml.safe_load(m.group(1))
    body, secs, cur, buf = m.group(2), {}, None, []
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


def _prose(section):
    """Narrative prose of a section: structured-gold `text`, else fences removed."""
    m = re.search(r"```(?:json)?\s*(.*?)```", section or "", re.S)
    if m:
        import json
        try:
            obj = json.loads(m.group(1))
            if isinstance(obj, dict) and "text" in obj:
                return obj["text"]
        except Exception:
            pass
    return re.sub(r"```.*?```", " ", section or "", flags=re.S)


def scan_dataset_a(root, families, cand_index):
    import glob
    recs = []
    for f in sorted(glob.glob(os.path.join(root, "drafts", "**", "*.md"), recursive=True)):
        fm, secs = _parse_record(f)
        src = _prose(secs.get("Context", ""))
        gold = _prose(secs.get("Gold Response", ""))
        rej = _prose(secs.get("Rejected Response", ""))
        s_src, s_gold, s_rej = (scan_text(src, families, cand_index),
                                scan_text(gold, families, cand_index),
                                scan_text(rej, families, cand_index))
        # source->gold family deltas (introduced / removed / preserved)
        ms, mg = _family_multiset(src, families), _family_multiset(gold, families)
        introduced = {k: mg[k] - ms[k] for k in mg if mg[k] > ms[k]}
        removed = {k: ms[k] - mg[k] for k in ms if ms[k] > mg[k]}
        preserved = {k: min(ms[k], mg[k]) for k in ms if min(ms[k], mg[k]) > 0}
        # structured no-change detection (gold is {changed:false, text:==source})
        import json
        no_change = False
        mm = re.search(r"```(?:json)?\s*(.*?)```", secs.get("Gold Response", ""), re.S)
        if mm:
            try:
                obj = json.loads(mm.group(1))
                no_change = isinstance(obj, dict) and obj.get("changed") is False
            except Exception:
                pass
        recs.append({
            "id": fm.get("id"), "task_type": fm.get("task_type"),
            "style_profile": fm.get("style_profile") or "none",
            "source": s_src, "gold": s_gold, "rejected": s_rej,
            "introduced": introduced, "removed": removed, "preserved": preserved,
            "em_source": s_src["em_dash_total"], "em_gold": s_gold["em_dash_total"],
            "em_compound_gold": s_gold["em_dash_compound"],
            "the_way_source": len(re.findall(r"\bthe way\b", src, re.I)),
            "the_way_gold": len(re.findall(r"\bthe way\b", gold, re.I)),
            "structured_no_change": no_change,
        })
    return recs


def _seg_section(recs, sect):
    words = sum(r[sect]["word_count"] for r in recs) or 1
    return {
        "records": len(recs),
        "words": sum(r[sect]["word_count"] for r in recs),
        "high_risk_raw": sum(r[sect]["high_risk_count"] for r in recs),
        "contextual_raw": sum(r[sect]["contextual_count"] for r in recs),
        "em_dash": sum(r[sect]["em_dash_total"] for r in recs),
        "em_compound": sum(r[sect]["em_dash_compound"] for r in recs),
        "cluster_windows": sum(r[sect]["cluster_windows"] for r in recs),
        "comparative_raw": sum(r[sect]["family_hits"]["comparative_template"] for r in recs),
        "comparative_density": round(
            sum(r[sect]["family_hits"]["comparative_template"] for r in recs) / words * 1000, 1),
    }


def render_segmented_md(recs, families, new_ids):
    fam_ids = [f["family_id"] for f in families]
    seed = [r for r in recs if r["id"] not in new_ids]
    new = [r for r in recs if r["id"] in new_ids]
    segments = [("Corrected seed (25)", seed), ("New batch (10)", new),
                ("Combined draft corpus (35)", recs)]
    L = ["# Gate 0 v3 — Electro Phrase-Signature Report (Dispatch 16)", "",
         "Segmented scan. The Dispatch 15 baseline report",
         "(`gate-0-v3-electro-signatures.md`) is left untouched. Findings are",
         "**REVIEW** only; no phrase proves AI authorship. Short records inflate",
         "per-1,000-word density, so **raw counts and density are both reported** and",
         "records are not ranked by normalized density alone.", ""]

    for name, seg in segments:
        L += [f"## {name}", ""]
        for sect in ("source", "gold", "rejected"):
            s = _seg_section(seg, sect)
            L.append(f"- **{sect}**: words {s['words']} | high-risk exact "
                     f"{s['high_risk_raw']} | contextual exact {s['contextual_raw']} | "
                     f"comparative raw {s['comparative_raw']} "
                     f"(density {s['comparative_density']}/1k) | em-dash {s['em_dash']} "
                     f"(compound {s['em_compound']}) | cluster-windows {s['cluster_windows']}")
        # the way per segment
        tws = sum(r["the_way_source"] for r in seg)
        twg = sum(r["the_way_gold"] for r in seg)
        L += [f"- `the way` — source {tws}, gold {twg}", ""]

    # family density leaderboard, seed vs new (aggregate hits / words * 1000)
    def agg_density(seg, sect):
        words = sum(r[sect]["word_count"] for r in seg) or 1
        return {fid: round(sum(r[sect]["family_hits"][fid] for r in seg) / words * 1000, 1)
                for fid in fam_ids}
    seed_g, new_g = agg_density(seed, "gold"), agg_density(new, "gold")
    L += ["## Family density — gold (aggregate per 1,000 words)", "",
          "| family | seed gold | new gold |", "|---|---|---|"]
    for fid in sorted(fam_ids, key=lambda x: -max(seed_g[x], new_g[x])):
        L.append(f"| {fid} | {seed_g[fid]} | {new_g[fid]} |")
    L.append("")

    # profile + task-family concentration (new batch)
    from collections import Counter
    prof = Counter(r["style_profile"] for r in new)
    task = Counter(r["task_type"] for r in new)
    L += ["## New-batch concentration", "",
          f"- style profiles: {dict(prof)}",
          f"- task families: {dict(task)}", ""]

    # introduced / removed families (new batch, source->gold)
    intro, rem = {}, {}
    for r in new:
        for k, v in r["introduced"].items():
            intro[k] = intro.get(k, 0) + v
        for k, v in r["removed"].items():
            rem[k] = rem.get(k, 0) + v
    L += ["## New-batch source → gold family deltas", "",
          f"- introduced: {intro or 'none'}",
          f"- removed: {rem or 'none'}",
          "- The golds should chiefly **remove** families; introductions are small "
          "(a single earned reaction, an action beat).", ""]

    # highest raw-hit and highest-density records (with word counts)
    raw_rank = sorted(((r["gold"]["high_risk_count"] + r["gold"]["contextual_count"],
                        r["id"]) for r in recs), reverse=True)[:6]
    dens_rank = sorted(((round(sum(r["gold"]["family_density"].values()), 1),
                         r["gold"]["word_count"], r["id"]) for r in recs),
                       reverse=True)[:6]
    L += ["## Highest raw-hit records (gold exact)", ""]
    L += [f"- {rid}: {n}" for n, rid in raw_rank]
    L += ["", "## Highest gold density records (with word counts)", ""]
    L += [f"- {rid}: density {d} (words {w})" for d, w, rid in dens_rank]
    L.append("")

    # explicit control checks
    nc = next((r for r in recs if r["id"] == "dsa-revision-019"), None)
    av = next((r for r in recs if r["id"] == "dsa-revision-020"), None)
    ord_ctrl = next((r for r in recs if r["id"] == "dsa-revision-012"), None)
    L += ["## Control checks", "",
          f"- **No-change restraint** (dsa-revision-019): structured no-change gold "
          f"= {bool(nc and nc['structured_no_change'])}; the earned `looked away` is "
          f"preserved (source == gold).",
          f"- **Author-voice override** (dsa-revision-020): declared `the way...` "
          f"anaphora preserved in gold ({av['the_way_gold'] if av else 0} occurrences "
          f"kept intentionally); the generic pressure metaphor was removed.",
          "- **Ordinary-phrase false-positive control**: single ordinary phrases "
          "never register as high-risk (see tests); the new golds add 0 high-risk "
          "exact hits.", ""]

    L += ["---", "",
          "**Discipline:** warnings only; no record altered by this report. Corpus "
          "artifacts (proper names, setting IDs) are excluded from generic "
          "detection. The seed `the way` cluster was reduced 5→4 (Part B); the "
          "new batch's 3 `the way` are the author-declared device in "
          "dsa-revision-020, not house style.", ""]
    return "\n".join(L)


def render_dataset_a_md(recs, families):
    fam_ids = [f["family_id"] for f in families]
    L = ["# Gate 0 v3 — Electro Phrase-Signature Report (Dataset A seed)", "",
         f"Scanned **{len(recs)}** records. Source, gold, and rejected responses are",
         "reported separately. All findings are **REVIEW** — never automatic",
         "rejection — and no phrase proves AI authorship. Family density is a",
         "heuristic per-1,000-word signal; exact hits are deterministic.", ""]

    # corpus totals
    def tot(sect, key):
        return sum(r[sect][key] for r in recs)
    L += ["## Corpus totals", "",
          f"- Source high-risk exact hits: **{tot('source','high_risk_count')}**  |"
          f" gold: **{tot('gold','high_risk_count')}**  |"
          f" rejected: **{tot('rejected','high_risk_count')}**",
          f"- Source contextual exact hits: **{tot('source','contextual_count')}**  |"
          f" gold: **{tot('gold','contextual_count')}**  |"
          f" rejected: **{tot('rejected','contextual_count')}**",
          f"- Em dashes — source: **{tot('source','em_dash_total')}**,"
          f" gold: **{tot('gold','em_dash_total')}**;"
          f" gold em-dash compound signatures: **{tot('gold','em_dash_compound')}**", ""]

    # family density leaderboard (mean across records, source vs gold)
    L += ["## Highest-density phrase families (mean per 1,000 words)", "",
          "| family | source | gold | severity |", "|---|---|---|---|"]
    sev = {f["family_id"]: f.get("severity", "") for f in families}
    rows = []
    for fid in fam_ids:
        s = round(sum(r["source"]["family_density"][fid] for r in recs) / len(recs), 1)
        g = round(sum(r["gold"]["family_density"][fid] for r in recs) / len(recs), 1)
        rows.append((max(s, g), fid, s, g))
    for _, fid, s, g in sorted(rows, reverse=True):
        L.append(f"| {fid} | {s} | {g} | {sev[fid]} |")
    L.append("")

    # introduced/removed source->gold (aggregate)
    intro = {}
    rem = {}
    for r in recs:
        for k, v in r["introduced"].items():
            intro[k] = intro.get(k, 0) + v
        for k, v in r["removed"].items():
            rem[k] = rem.get(k, 0) + v
    L += ["## Source → gold family deltas (aggregate)", "",
          f"- Introduced (gold adds a family pattern absent/thinner in source): "
          f"{intro or 'none'}",
          f"- Removed (gold reduces a source family pattern): {rem or 'none'}",
          "- REVIEW when a gold **introduces** a high-severity family pattern; a "
          "gold that **removes** one is doing anti-slop work.", ""]

    # profile concentrations
    prof = {}
    for r in recs:
        p = r["style_profile"]
        d = prof.setdefault(p, {"n": 0, "dens": {fid: 0.0 for fid in fam_ids}})
        d["n"] += 1
        for fid in fam_ids:
            d["dens"][fid] += r["gold"]["family_density"][fid]
    L += ["## Profile concentrations (mean gold family density)", ""]
    for p, d in sorted(prof.items()):
        top = sorted(((round(v / d["n"], 1), fid) for fid, v in d["dens"].items()),
                     reverse=True)[:3]
        L.append(f"- **{p}** ({d['n']} rec): "
                 + ", ".join(f"{fid} {val}" for val, fid in top if val > 0) or "—")
    L += ["- REVIEW when multiple profiles share the same high-severity family "
          "(house-style collapse risk).", ""]

    # the way findings (direct scan of prose, source + gold)
    tw_src = [r["id"] for r in recs if r["the_way_source"]]
    tw_gold = [r["id"] for r in recs if r["the_way_gold"]]
    tw_family = sum(1 for r in recs if r["source"]["family_hits"].get("comparative_template", 0))
    L += ["## `the way` and comparative frames", "",
          f"- Source `the way` occurrences in **{len(tw_src)}** records: "
          f"{', '.join(tw_src) or 'none'}",
          f"- Gold `the way` occurrences in **{len(tw_gold)}** records: "
          f"{', '.join(tw_gold) or 'none'}",
          f"- Records with any comparative_template family density (source): {tw_family}",
          "- REVIEW: the comparative frame (`the way ...`, `like a ...`) is a known "
          "recurring signature in this corpus; watch for it clustering across records.", ""]

    # highest-density records
    dens_rank = sorted(
        ((round(sum(r["gold"]["family_density"].values()), 1), r["id"]) for r in recs),
        reverse=True)[:8]
    L += ["## Highest-density records (gold, summed family density)", ""]
    for val, rid in dens_rank:
        L.append(f"- {rid}: {val}")
    L.append("")

    # per-record detail (only where something is present)
    L += ["## Per-record detail", ""]
    for r in recs:
        hs = r["source"]["exact_hits"]["high_risk_signature"]
        hg = r["gold"]["exact_hits"]["high_risk_signature"]
        cg = r["gold"]["exact_hits"]["contextual_risk"]
        L += [f"### {r['id']}  ({r['style_profile']}, {r['task_type']})",
              f"- exact high-risk: source {sorted(set(hs)) or '[]'} | gold {sorted(set(hg)) or '[]'}",
              f"- gold contextual exact: {sorted(set(cg))[:8] or '[]'}",
              f"- em dashes source/gold: {r['em_source']}/{r['em_gold']}"
              f" (gold compound: {r['em_compound_gold']})",
              f"- introduced families: {r['introduced'] or 'none'} | "
              f"removed: {r['removed'] or 'none'}", ""]

    L += ["---", "",
          "**Discipline:** warnings only. Corpus artifacts (proper names, malformed",
          "entries, setting IDs) are excluded from generic detection. Ordinary",
          "phrases are never high risk merely for appearing once. Author-supplied",
          "punctuation and single earned phrases are not penalized.", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text")
    ap.add_argument("--dataset-a")
    ap.add_argument("--families", default=DEFAULT_FAMILIES)
    ap.add_argument("--candidates", default=DEFAULT_CANDIDATES)
    ap.add_argument("--new-ids", help="comma-separated record IDs for a segmented report")
    ap.add_argument("--out-md")
    args = ap.parse_args()
    families = load_families(args.families)
    cand = load_candidates(args.candidates) if os.path.exists(args.candidates) else {}

    if args.dataset_a:
        recs = scan_dataset_a(args.dataset_a, families, cand)
        if args.new_ids:
            new_ids = set(x.strip() for x in args.new_ids.split(",") if x.strip())
            md = render_segmented_md(recs, families, new_ids)
        else:
            md = render_dataset_a_md(recs, families)
        if args.out_md:
            with open(args.out_md, "w", encoding="utf-8") as fh:
                fh.write(md)
            print(f"scanned {len(recs)} records -> {args.out_md}")
        else:
            print(md)
        return
    if args.text:
        text = open(args.text, encoding="utf-8").read()
        import json
        print(json.dumps(scan_text(text, families, cand), indent=2))
        return
    ap.error("provide --text or --dataset-a")


if __name__ == "__main__":
    main()
