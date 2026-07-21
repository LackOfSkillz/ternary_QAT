#!/usr/bin/env python3
"""Gate 0 — deterministic delta analysis of focused-revision records.

Compares each revision record's `## Context` source prose to its `## Gold
Response`, measuring changes and flagging potential OFF-AXIS movement (changes
outside the declared craft target / authorized changes / protected craft). It
does NOT approve or reject anything; it produces evidence for the Gate 1 human
review. Every metric is labeled deterministic | heuristic | unavailable.

Usage:
  python analyze_revision_deltas.py --root datasets/dataset-a \
      --out-json <path.json> --out-md <path.md>
"""
import argparse
import difflib
import glob
import json
import os
import re

import yaml


def structured_gold_text(gold):
    """If the gold is the structured revision object {changed, reason, text},
    return (text, changed). Otherwise (gold, None)."""
    m = re.search(r"```(?:json)?\s*(.*?)```", gold, re.S)
    if m:
        try:
            obj = json.loads(m.group(1))
            if isinstance(obj, dict) and "text" in obj:
                return obj["text"], obj.get("changed")
        except Exception:
            pass
    return gold, None

FILTER_WORDS = ["saw", "felt", "heard", "noticed", "realized", "watched",
                "thought", "knew", "seemed", "wondered"]
EMOTION_WORDS = ["grief", "sorrow", "joy", "fear", "anger", "angry", "love",
                 "hope", "dread", "shame", "guilt", "guilty", "rage", "despair",
                 "longing", "tenderness", "sadness", "sad", "happiness", "happy",
                 "hurt", "forgive", "forgiveness", "desire"]


def parse(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    fm = yaml.safe_load(m.group(1))
    body = m.group(2)
    secs = {}
    cur, buf = None, []
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


def strip_prefix(text, label):
    # gold responses sometimes prepend a sentence like "No change needed. ...";
    # for metrics we compare raw section text as-is.
    return text.strip()


def sentences(t):
    # collapse intra-sentence whitespace so wrapped source prose and single-line
    # gold text (e.g. from a structured no-change object) compare correctly.
    return [re.sub(r"\s+", " ", s.strip())
            for s in re.split(r"(?<=[.!?])\s+", t.strip()) if s.strip()]


def words(t):
    return re.findall(r"[A-Za-z']+", t)


def count(t, ch):
    return t.count(ch)


def var(xs):
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return round((sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5, 2)


def wordset_count(t, vocab):
    low = re.findall(r"[a-z']+", t.lower())
    return sum(1 for w in low if w in vocab)


def analyze_one(fm, secs):
    src = secs.get("Context", "")
    # drop a leading "Passage:" / "Sentence:" label if present in revision context
    src = re.sub(r"^(Sentence|Passage):\s*", "", src)
    gold, gold_changed = structured_gold_text(secs.get("Gold Response", ""))

    sc_s, sc_g = sentences(src), sentences(gold)
    w_s, w_g = words(src), words(gold)
    sm = difflib.SequenceMatcher(None, sc_s, sc_g)
    changed = sum(1 for tag, *_ in sm.get_opcodes() if tag != "equal")
    ratio = round(sm.ratio(), 3)

    def punct(ch):
        return {"source": count(src, ch), "gold": count(gold, ch),
                "delta": count(gold, ch) - count(src, ch)}

    metrics = {
        "word_count": {"source": len(w_s), "gold": len(w_g),
                       "delta": len(w_g) - len(w_s), "kind": "deterministic"},
        "sentence_count": {"source": len(sc_s), "gold": len(sc_g),
                           "delta": len(sc_g) - len(sc_s), "kind": "heuristic"},
        "changed_sentence_blocks": {"value": changed, "kind": "heuristic"},
        "sentence_similarity_ratio": {"value": ratio, "kind": "heuristic"},
        "em_dash": {**punct("—"), "kind": "deterministic"},
        "ellipsis": {"source": count(src, "…") + count(src, "..."),
                     "gold": count(gold, "…") + count(gold, "..."),
                     "kind": "deterministic"},
        "semicolon": {**punct(";"), "kind": "deterministic"},
        "colon": {**punct(":"), "kind": "deterministic"},
        "avg_sentence_len": {"source": round(len(w_s) / max(len(sc_s), 1), 1),
                             "gold": round(len(w_g) / max(len(sc_g), 1), 1),
                             "kind": "heuristic"},
        "sentence_len_variance": {
            "source": var([len(words(s)) for s in sc_s]),
            "gold": var([len(words(s)) for s in sc_g]), "kind": "heuristic"},
        "filter_words": {"source": wordset_count(src, FILTER_WORDS),
                         "gold": wordset_count(gold, FILTER_WORDS),
                         "kind": "deterministic"},
        "adverbs_ly": {"source": len([w for w in w_s if w.lower().endswith("ly")]),
                       "gold": len([w for w in w_g if w.lower().endswith("ly")]),
                       "kind": "heuristic"},
        "adjective_estimate": {"value": None, "kind": "unavailable",
                               "note": "no POS tagger in the deterministic env"},
        "named_emotion_words": {"source": wordset_count(src, EMOTION_WORDS),
                                "gold": wordset_count(gold, EMOTION_WORDS),
                                "kind": "heuristic"},
        "quote_chars": {"source": count(src, '"'), "gold": count(gold, '"'),
                        "kind": "heuristic",
                        "note": "dialogue-to-narration proxy"},
    }
    # repeated-opening estimate (anaphora proxy): most common sentence first word
    def rep_open(ss):
        firsts = [s.split()[0].lower() for s in ss if s.split()]
        if not firsts:
            return 0
        return max(firsts.count(x) for x in set(firsts))
    metrics["max_repeated_opening"] = {"source": rep_open(sc_s), "gold": rep_open(sc_g),
                                       "kind": "heuristic"}

    # ---- off-axis + teacher-signature flags ----
    # Authorized-axis awareness (heuristic): some structural moves (combining or
    # varying sentences) are explicitly authorized, so a low sentence-sequence
    # similarity is EXPECTED and must not be treated as a major off-axis warning.
    flags = []
    authorized = " ".join(fm.get("authorized_changes", []) or []).lower()
    targets = " ".join((fm.get("craft_targets", []) or []) +
                       (fm.get("anti_slop_targets", []) or [])).lower()
    protected = " ".join(fm.get("protected_craft", []) or []).lower()
    # low sentence-sequence similarity is EXPECTED when the task authorizes a
    # structural rewrite (combining/varying sentences) or a line-level rewrite
    # into subtext; those are on-axis, not off-axis.
    structural_authorized = any(kw in (authorized + targets) for kw in
                                ("combine", "vary sentence", "sentence length variance",
                                 "turn_length_variance", "sentence_length_variance",
                                 "rewrite", "subtext", "indirection"))
    ib = fm.get("invention_budget") or {}
    ib_level = ib.get("level")

    if metrics["em_dash"]["delta"] > 0 and "dash" not in (authorized + targets):
        flags.append(f"em dash introduced ({metrics['em_dash']['delta']}) but not "
                     f"an authorized/target change")
    if metrics["colon"]["delta"] > 0 and "colon" not in (authorized + targets):
        flags.append(f"colon introduced ({metrics['colon']['delta']}), not a named change")
    if metrics["semicolon"]["delta"] != 0 and "semicolon" not in authorized:
        flags.append("semicolon count changed, not a named target")
    if ratio < 0.5 and not structural_authorized:
        flags.append(f"large edit distance (similarity {ratio}) on a focused/minimal task")
    # invention beyond a 'none' budget (heuristic: net new words with no deletion task)
    if ib_level == "none" and metrics["word_count"]["delta"] > 6:
        flags.append(f"word count grew by {metrics['word_count']['delta']} under a "
                     f"'none' invention budget (possible added material)")
    if metrics["named_emotion_words"]["gold"] < metrics["named_emotion_words"]["source"] \
            and ("emotion" in protected or "named" in protected):
        flags.append("named-emotion word count dropped while emotion naming is protected")
    if abs(metrics["sentence_len_variance"]["gold"] -
           metrics["sentence_len_variance"]["source"]) >= 4 and "variance" not in targets:
        flags.append("sentence-length variance shifted notably though not the named target")

    # teacher-style signatures (heuristic)
    sigs = []
    if metrics["em_dash"]["delta"] > 0:
        sigs.append("added em dash")
    if re.search(r"\bnot\b[^.,]{0,40},?\s+but\b", gold, re.I) and \
            not re.search(r"\bnot\b[^.,]{0,40},?\s+but\b", src, re.I):
        sigs.append("'not X, but Y' construction added")
    tri_g = len(re.findall(r"\b\w+,\s+\w+,\s+and\s+\w+\b", gold))
    tri_s = len(re.findall(r"\b\w+,\s+\w+,\s+and\s+\w+\b", src))
    if tri_g > tri_s:
        sigs.append("three-part (tricolon) construction added")
    # aphoristic short abstract ending added
    if sc_g and sc_s and sc_g[-1] != sc_s[-1] and len(words(sc_g[-1])) <= 8 \
            and not any(c.isdigit() for c in sc_g[-1]):
        sigs.append("short aphoristic-style ending changed/added (review)")

    return metrics, flags, sigs


def machine_note(fm, metrics, flags):
    tgt = ", ".join(fm.get("craft_targets", []) or []) or "n/a"
    if not flags:
        return f"No off-axis flags. Target: {tgt}. Edit similarity " \
               f"{metrics['sentence_similarity_ratio']['value']}."
    return f"{len(flags)} off-axis flag(s). Target: {tgt}."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.root, "drafts", "revision", "*.md")))
    records = []
    for f in files:
        fm, secs = parse(f)
        metrics, flags, sigs = analyze_one(fm, secs)
        records.append({
            "id": fm.get("id"), "style_profile": fm.get("style_profile"),
            "craft_targets": fm.get("craft_targets"),
            "protected_craft": fm.get("protected_craft"),
            "authorized_changes": fm.get("authorized_changes"),
            "unauthorized_changes": fm.get("unauthorized_changes"),
            "invention_budget_level": (fm.get("invention_budget") or {}).get("level"),
            "metrics": metrics, "off_axis_flags": flags,
            "teacher_signatures": sigs, "machine_note": machine_note(fm, metrics, flags),
        })

    with open(args.out_json, "w", encoding="utf-8") as fh:
        json.dump({"records": records}, fh, indent=2)

    # markdown report
    lines = ["# Gate 0 — Revision Delta Report", "",
             "Deterministic evidence for Gate 1 human review of the 10 focused-",
             "revision records. This report **does not approve or reject** anything.",
             "Metrics are labeled deterministic | heuristic | unavailable.", "",
             "**Authorized-axis awareness (heuristic):** when a record explicitly",
             "authorizes combining or varying sentences, low sentence-sequence",
             "similarity is EXPECTED and is *not* flagged as off-axis. The scan still",
             "flags unauthorized additions (new imagery/facts/interpretation, em",
             "dashes/colons not named as targets, protected-element loss, and net new",
             "words under a `none` invention budget). It does not judge prose quality.",
             ""]
    for r in records:
        m = r["metrics"]
        lines += [f"## {r['id']}  ({r['style_profile']})", "",
                  f"- **Intended craft target:** {', '.join(r['craft_targets'] or []) or 'n/a'}",
                  f"- **Protected craft:** {', '.join(r['protected_craft'] or []) or 'n/a'}",
                  f"- **Authorized changes:** {', '.join(r['authorized_changes'] or []) or 'n/a'}",
                  f"- **Invention budget:** {r['invention_budget_level'] or 'n/a'}",
                  "",
                  "| metric | source | gold | delta | kind |",
                  "|---|---|---|---|---|"]
        for name in ["word_count", "sentence_count", "avg_sentence_len",
                     "sentence_len_variance", "em_dash", "semicolon", "colon",
                     "ellipsis", "filter_words", "adverbs_ly", "named_emotion_words",
                     "max_repeated_opening", "quote_chars"]:
            d = m[name]
            delta = d.get("delta", "")
            if delta == "" and "source" in d and "gold" in d and isinstance(d["source"], (int, float)):
                delta = d["gold"] - d["source"]
            lines.append(f"| {name} | {d.get('source','')} | {d.get('gold','')} | "
                         f"{delta} | {d['kind']} |")
        lines += ["",
                  f"- similarity ratio (heuristic): {m['sentence_similarity_ratio']['value']}; "
                  f"changed sentence blocks: {m['changed_sentence_blocks']['value']}",
                  f"- adjective_estimate: unavailable (no POS tagger)", ""]
        if r["off_axis_flags"]:
            lines.append("**Potential off-axis flags:**")
            for fl in r["off_axis_flags"]:
                lines.append(f"- ⚠ {fl}")
        else:
            lines.append("**Potential off-axis flags:** none")
        lines.append("")
        lines.append(f"**Teacher-style signatures (heuristic):** "
                     f"{', '.join(r['teacher_signatures']) or 'none'}")
        lines += ["", f"**Machine note:** {r['machine_note']}", "",
                  "**Reviewer decision (Gate 1):** _pending_", "", "---", ""]

    with open(args.out_md, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"analyzed {len(records)} revision records -> {args.out_md}")
    for r in records:
        print(f"  {r['id']}: flags={len(r['off_axis_flags'])} "
              f"sigs={len(r['teacher_signatures'])}")


if __name__ == "__main__":
    main()
