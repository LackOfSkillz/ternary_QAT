#!/usr/bin/env python3
"""Deterministic normalization of the Electro phrase lists.

Reads raw/*.txt, normalizes, removes exact duplicates (preserving source-file
attribution), classifies each phrase into a tier + phrase families, routes corpus
artifacts (proper names, malformed/truncated, setting/numeric identifiers) to an
audit file, and emits deterministic YAML plus a normalization report. NOTHING is
silently discarded.

Usage:
  python normalize_phrase_lists.py --root datasets/research/electro-phrase-signatures
"""
import argparse
import os
import sys

import yaml

# import shared classification/family logic from the sibling scanner module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan_phrase_signatures as sig  # noqa: E402

RAW_FILES = [
    ("bigrams-electro-a.txt", 2),
    ("bigrams-electro-b.txt", 2),
    ("trigrams-electro-a.txt", 3),
]


def normalize_line(line):
    return " ".join(line.strip().lower().split())


def run(root):
    families = sig.load_families(os.path.join(root, "normalized", "phrase-families.yaml"))
    raw_dir = os.path.join(root, "raw")

    raw_counts = {}
    phrase_sources = {}   # phrase -> set(source files)
    phrase_n = {}         # phrase -> n
    total_raw = 0
    for fn, _n in RAW_FILES:
        n_lines = 0
        for line in open(os.path.join(raw_dir, fn), encoding="utf-8"):
            p = normalize_line(line)
            if not p:
                continue
            n_lines += 1
            total_raw += 1
            phrase_sources.setdefault(p, set()).add(fn)
            phrase_n[p] = len(p.split())
        raw_counts[fn] = n_lines

    unique = sorted(phrase_sources)
    candidates, excluded = [], []
    tier_counts = {"high_risk_signature": 0, "contextual_risk": 0,
                   "ordinary_phrase": 0}
    excl_reasons = {}

    for p in unique:
        reason = sig.classify_artifact(p)
        if reason:
            excluded.append({"phrase": p, "reason": reason,
                             "source_files": sorted(phrase_sources[p])})
            excl_reasons[reason] = excl_reasons.get(reason, 0) + 1
            continue
        tier = sig.tier_for(p, families)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        candidates.append({
            "phrase": p, "n": phrase_n[p],
            "source_files": sorted(phrase_sources[p]),
            "family_ids": sig.families_for(p, families),
            "tier": tier, "status": "candidate",
        })

    overlap = sorted(p for p, s in phrase_sources.items() if len(s) > 1)

    norm_dir = os.path.join(root, "normalized")
    with open(os.path.join(norm_dir, "candidate-phrases.yaml"), "w", encoding="utf-8") as fh:
        yaml.safe_dump({"phrases": candidates}, fh, sort_keys=False,
                       allow_unicode=True, default_flow_style=False)
    with open(os.path.join(norm_dir, "excluded-artifacts.yaml"), "w", encoding="utf-8") as fh:
        yaml.safe_dump(excluded, fh, sort_keys=False, allow_unicode=True,
                       default_flow_style=False)

    report = [
        "# Normalization Report — Electro phrase lists", "",
        "Deterministic. Nothing is silently discarded; every excluded entry is in",
        "`normalized/excluded-artifacts.yaml` with a reason.", "",
        "## Raw entry counts (non-blank lines)", "",
    ]
    for fn, _n in RAW_FILES:
        report.append(f"- {fn}: {raw_counts[fn]}")
    report += [
        f"- **total raw entries:** {total_raw}", "",
        "## Deduplication", "",
        f"- unique entries: **{len(unique)}**",
        f"- exact duplicates removed: **{total_raw - len(unique)}**",
        f"- cross-file overlap (phrases in >1 file): **{len(overlap)}**", "",
        "## Exclusions (corpus artifacts)", "",
        f"- proper-name entries: **{excl_reasons.get('corpus_specific_proper_name', 0)}**",
        f"- setting/numeric identifiers: **"
        f"{excl_reasons.get('corpus_specific_setting_identifier', 0) + excl_reasons.get('corpus_specific_setting_or_numeric', 0)}**",
        f"- malformed/truncated entries: **{excl_reasons.get('malformed_or_truncated', 0)}**",
        f"- **total excluded:** {len(excluded)}", "",
        "## Retained candidates by tier", "",
        f"- high_risk_signature: **{tier_counts['high_risk_signature']}**",
        f"- contextual_risk: **{tier_counts['contextual_risk']}**",
        f"- ordinary_phrase: **{tier_counts['ordinary_phrase']}**",
        f"- **total retained candidates:** {len(candidates)}", "",
        "All thresholds downstream are REVIEW, never FAIL. No phrase is labeled "
        "\"AI-only\"; tiers are repetition-risk priors only.", "",
    ]
    with open(os.path.join(root, "reports", "normalization-report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(report))

    print(f"raw={total_raw} unique={len(unique)} dupes={total_raw - len(unique)} "
          f"overlap={len(overlap)} excluded={len(excluded)} candidates={len(candidates)}")
    print(f"tiers: {tier_counts}")
    print(f"excluded reasons: {excl_reasons}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    os.makedirs(os.path.join(args.root, "reports"), exist_ok=True)
    run(args.root)


if __name__ == "__main__":
    main()
