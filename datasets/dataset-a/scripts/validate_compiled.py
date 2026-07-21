#!/usr/bin/env python3
"""Compiled-artifact + split-leakage validator for the experimental freeze.

Checks the 18 compilation guarantees against the split manifest, freeze manifest,
and compiled JSONL. Exit 0 only if every check passes.

Usage:
  python validate_compiled.py --root datasets/dataset-a --out-subdir experimental-v1
"""
import argparse
import glob
import hashlib
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compile_dataset_a as C  # noqa: E402


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out-subdir", default="experimental-v1")
    args = ap.parse_args()
    root, sub = args.root, args.out_subdir
    problems = []

    def check(cond, msg):
        if not cond:
            problems.append(msg)

    split = yaml.safe_load(open(os.path.join(root, "manifests",
                                             "experimental-split-v1.yaml"), encoding="utf-8"))
    train_ids, eval_ids = set(split["train"]), set(split["evaluation"])
    freeze = json.load(open(os.path.join(root, "manifests",
                                         "experimental-freeze-v1.canonical.json"), encoding="utf-8"))
    freeze_hash = {r["id"]: r["sha256"] for r in freeze["records"]}

    out = os.path.join(root, "compiled", sub)
    train = load_jsonl(os.path.join(out, "train.jsonl"))
    ev = load_jsonl(os.path.join(out, "evaluation.jsonl"))
    manifest = json.load(open(os.path.join(out, "manifest.json"), encoding="utf-8"))

    # gather source records
    src = {}
    for f in sorted(glob.glob(os.path.join(root, "drafts", "**", "*.md"), recursive=True)):
        fm, secs, sha = C.parse_record(f)
        src[fm["id"]] = (fm, secs, sha)

    tr_ids = [r["id"] for r in train]
    ev_ids = [r["id"] for r in ev]

    # 1 + 3: every frozen record in exactly one split; counts match manifest
    check(set(tr_ids) == train_ids, "train.jsonl ids != split manifest train")
    check(set(ev_ids) == eval_ids, "evaluation.jsonl ids != split manifest evaluation")
    check(len(tr_ids) == len(train_ids) == 28, "train count != 28")
    check(len(ev_ids) == len(eval_ids) == 7, "eval count != 7")
    # 2 + 9: no eval id in train
    check(not (set(tr_ids) & set(ev_ids)), "train/eval leakage: shared ids")
    # 5 + 26: unique ids
    check(len(tr_ids) == len(set(tr_ids)), "duplicate id in train.jsonl")
    check(len(ev_ids) == len(set(ev_ids)), "duplicate id in evaluation.jsonl")
    check(len(set(tr_ids) | set(ev_ids)) == 35, "compiled ids != 35 frozen records")

    # per-row checks
    for r in train + ev:
        fm, secs, sha = src[r["id"]]
        # 4: parses (already parsed); 6: training row has assistant target
        asst = r["messages"][2]
        check(asst["role"] == "assistant" and asst["content"].strip() != "",
              f"{r['id']}: empty/missing assistant target")
        # 8 + 12 + 11: target is EXACTLY the gold (no leak, no rejected)
        expected = C.assistant_target(secs.get("Gold Response", ""))
        check(asst["content"] == expected, f"{r['id']}: assistant target != gold")
        rej = C.assistant_target(secs.get("Rejected Response", ""))
        if rej:
            check(asst["content"] != rej, f"{r['id']}: assistant target equals rejected response")
        # user prompt exactly instruction+context (no notes/eval leak)
        check(r["messages"][1]["content"] == C.user_prompt(secs),
              f"{r['id']}: user prompt altered")
        # no reviewer notes / rejection reasons text in target
        for leak in ("Reviewer Notes", "Rejection Reasons", "Rejected Response",
                     "Protected Elements", "## Evaluation"):
            check(leak not in asst["content"], f"{r['id']}: '{leak}' leaked into target")
        # 13: source hash matches freeze manifest AND row metadata
        check(sha == freeze_hash.get(r["id"]), f"{r['id']}: source hash != freeze manifest")
        check(r["metadata"]["source_hash"] == sha, f"{r['id']}: row source_hash mismatch")
        # 7: structured no-change assistant is valid JSON
        gold = secs.get("Gold Response", "")
        inner = C.fence_inner(gold)
        if inner and '"changed"' in (inner or ""):
            try:
                obj = json.loads(asst["content"])
                check(isinstance(obj, dict) and "changed" in obj,
                      f"{r['id']}: structured no-change target invalid")
            except Exception:
                problems.append(f"{r['id']}: structured target is not valid JSON")

    # 9: evaluation records excluded_from_training on-record
    for rid in eval_ids:
        fm = src[rid][0]
        check(fm.get("excluded_from_training") is True,
              f"{rid}: evaluation record not excluded_from_training")
    # train records included
    for rid in train_ids:
        fm = src[rid][0]
        check(fm.get("excluded_from_training") is False,
              f"{rid}: train record must be excluded_from_training: false")

    # 18: no draft/unreviewed record compiled
    for rid in set(tr_ids) | set(ev_ids):
        check(src[rid][0].get("review_status") == "approved",
              f"{rid}: compiled but not approved")

    # 10: no raw Electro list in compiled output
    for f in glob.glob(os.path.join(out, "**", "*"), recursive=True):
        base = os.path.basename(f).lower()
        check(not (base.startswith("bigrams") or base.startswith("trigrams")),
              f"raw Electro list in compiled output: {f}")

    # 16: system prompt hash matches manifest
    sp = os.path.join(root, manifest["system_prompt"]["path"])
    sp_hash = hashlib.sha256(open(sp, "rb").read()).hexdigest()
    check(sp_hash == manifest["system_prompt"]["sha256"], "system-prompt hash != manifest")

    # 13: manifest file hashes match compiled files
    for key, meta in manifest["files"].items():
        p = os.path.join(out, meta["path"])
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        check(h == meta["sha256"], f"manifest file hash mismatch for {key}")

    print("=== COMPILED ARTIFACT VALIDATION ===")
    print(f"train={len(train)} eval={len(ev)} frozen={len(src)}")
    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for p in problems:
            print("  !!", p)
        sys.exit(1)
    print("\nALL COMPILED ARTIFACTS VALID")


if __name__ == "__main__":
    main()
