"""Dispatch 28B — normalize raw generation outputs (read raw-results/, write normalized-results/).

Allowed normalization ONLY: normalize line endings, trim outer whitespace, drop an empty assistant
prefix, and strip an EMPTY <think></think> wrapper. Never rewrites content, repairs JSON, corrects
spelling, truncates, or removes non-empty reasoning. Raw is preserved untouched.
"""
import json
import os
import re
import sys

RUN = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "runs", "linewright-prompt-execution-v1")
RUN = os.path.abspath(RUN)
ARMS = ["p0-realistic", "p0-maximal", "p1-contract", "p3-ideal"]


def normalize_text(t):
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    # strip an empty <think></think> wrapper only (never non-empty reasoning)
    m = re.match(r"\s*<think>\s*</think>\s*", t)
    if m:
        t = t[m.end():]
    return t.strip()


def process(src_dir, dst_dir):
    n = 0
    if not os.path.isdir(src_dir):
        return 0
    os.makedirs(dst_dir, exist_ok=True)
    for fn in sorted(os.listdir(src_dir)):
        if not fn.endswith(".json"):
            continue
        r = json.load(open(os.path.join(src_dir, fn), encoding="utf-8"))
        if r.get("generation_status") == "technical_failure":
            json.dump(r, open(os.path.join(dst_dir, fn), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            continue
        raw = r.get("output_text", "")
        r["normalized_text"] = normalize_text(raw)
        r["normalization_changed"] = (r["normalized_text"] != raw)
        json.dump(r, open(os.path.join(dst_dir, fn), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        n += 1
    return n


def main():
    total = 0
    for arm in ARMS:
        total += process(os.path.join(RUN, "raw-results", arm), os.path.join(RUN, "normalized-results", arm))
    comp = process(os.path.join(RUN, "comprehension-results"),
                   os.path.join(RUN, "comprehension-normalized"))
    print(json.dumps({"normalized_primary": total, "normalized_comprehension": comp}, indent=1))


if __name__ == "__main__":
    main()
