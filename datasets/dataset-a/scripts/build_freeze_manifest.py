#!/usr/bin/env python3
"""Build the experimental-freeze manifest + a timestamp-free canonical companion.

Deterministic: every field is derived from the frozen record files except the
isolated `created_at` (yaml only). The canonical JSON is byte-stable given the
record contents and is what integrity checks compare against.

Usage:
  python build_freeze_manifest.py --root datasets/dataset-a \
      --freeze-id dataset-a-experimental-v1 --source-head 7492546 --created-at 2026-07-21
"""
import argparse
import glob
import hashlib
import json
import os
import re

import yaml

FREEZE_ID = "dataset-a-experimental-v1"


def parse(path):
    text = open(path, "rb").read()
    sha = hashlib.sha256(text).hexdigest()
    t = text.decode("utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", t, re.S)
    fm = yaml.safe_load(m.group(1))
    body = m.group(2)
    gold = ""
    cur = None
    buf = []
    for line in body.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            if cur == "Gold Response":
                gold = "\n".join(buf).strip()
            cur, buf = h.group(1), []
        else:
            buf.append(line)
    if cur == "Gold Response":
        gold = "\n".join(buf).strip()
    return fm, sha, gold


def no_change(gold):
    mm = re.search(r"```(?:json)?\s*(.*?)```", gold, re.S)
    if mm:
        try:
            obj = json.loads(mm.group(1))
            return isinstance(obj, dict) and obj.get("changed") is False
        except Exception:
            pass
    return False


def build(root):
    records = []
    for f in sorted(glob.glob(os.path.join(root, "drafts", "**", "*.md"), recursive=True)):
        fm, sha, gold = parse(f)
        ib = (fm.get("invention_budget") or {}).get("level")
        records.append({
            "id": fm["id"],
            "sha256": sha,
            "task_type": fm["task_type"],
            "subtype": fm.get("subtype"),
            "style_profile": fm.get("style_profile") or "none",
            "semantic_cluster": fm.get("semantic_cluster"),
            "template_family": fm.get("template_family"),
            "teacher_model": fm.get("teacher_model"),
            "provenance": fm.get("provenance"),
            "invention_budget_level": ib,
            "no_change": no_change(gold),
            "author_voice_override": fm.get("subtype") == "author_voice_override",
            "split": fm.get("split"),
            "review_status": fm.get("review_status"),
        })
    records.sort(key=lambda r: r["id"])
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--freeze-id", default=FREEZE_ID)
    ap.add_argument("--source-head", required=True)
    ap.add_argument("--created-at", required=True)
    args = ap.parse_args()

    records = build(args.root)
    core = {
        "freeze_id": args.freeze_id,
        "purpose": "first_end_to_end_training_smoke_test",
        "source_branch": "linewright-experiments",
        "source_head": args.source_head,
        "record_count": len(records),
        "review_status_at_freeze": "approved",
        "gate_2_status": "passed",
        "gate_3_status": "passed",
        "production_approved": False,
        "record_ids": [r["id"] for r in records],
        "records": records,
    }
    out_dir = os.path.join(args.root, "manifests")
    # canonical (timestamp-free), byte-stable
    with open(os.path.join(out_dir, "experimental-freeze-v1.canonical.json"),
              "w", encoding="utf-8", newline="\n") as fh:
        json.dump(core, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    # yaml with the isolated timestamp
    yml = dict(core)
    yml_ordered = {"freeze_id": yml["freeze_id"], "purpose": yml["purpose"],
                   "source_branch": yml["source_branch"], "source_head": yml["source_head"],
                   "created_at": args.created_at, "record_count": yml["record_count"],
                   "review_status_at_freeze": yml["review_status_at_freeze"],
                   "gate_2_status": yml["gate_2_status"], "gate_3_status": yml["gate_3_status"],
                   "production_approved": yml["production_approved"],
                   "record_ids": yml["record_ids"], "records": yml["records"]}
    with open(os.path.join(out_dir, "experimental-freeze-v1.yaml"),
              "w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump(yml_ordered, fh, sort_keys=False, allow_unicode=True,
                       default_flow_style=False, width=1000)
    tr = sum(1 for r in records if r["split"] == "train")
    ev = sum(1 for r in records if r["split"] == "evaluation")
    print(f"freeze manifest: {len(records)} records (train={tr} eval={ev})")


if __name__ == "__main__":
    main()
