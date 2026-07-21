#!/usr/bin/env python3
"""Mechanical validator for Dataset A source records (Markdown + YAML front
matter). Lightweight on purpose: it checks structure/enums/uniqueness/placement,
it does NOT compile training data. Exit 0 only if every record passes.

Usage:
  python validate_dataset_a.py --root datasets/dataset-a
"""
import argparse
import glob
import os
import re
import sys

import yaml

APPROVED_STATUSES = {"substantively_approved", "author_approved", "frozen"}


def parse_record(path):
    """Return (front_matter_dict, set_of_section_headings, context_text,
    gold_text) or raise ValueError."""
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError("missing YAML front matter (--- ... ---)")
    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    sections = {}
    cur = None
    buf = []
    for line in body.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            if cur is not None:
                sections[cur] = "\n".join(buf).strip()
            cur = h.group(1)
            buf = []
        else:
            buf.append(line)
    if cur is not None:
        sections[cur] = "\n".join(buf).strip()
    return fm, sections


def load_yaml(path):
    return yaml.safe_load(open(path, encoding="utf-8"))


def validate(root):
    problems = []
    enums = load_yaml(os.path.join(root, "schema", "enums.yaml"))
    schema = load_yaml(os.path.join(root, "schema", "record-schema.yaml"))
    req_all = schema["required_all"]
    req_by_type = schema["required_by_task_type"]
    sec_all = schema["sections_required_all"]
    sec_by_type = schema["sections_required_by_task_type"]

    draft_files = sorted(glob.glob(os.path.join(root, "drafts", "**", "*.md"), recursive=True))
    approved_files = sorted(glob.glob(os.path.join(root, "approved", "**", "*.md"), recursive=True))
    all_files = [(f, "drafts") for f in draft_files] + [(f, "approved") for f in approved_files]

    seen_ids = {}
    fam_cluster = {}
    contexts = {}
    golds = {}
    fam_counts = {}

    def err(f, msg):
        problems.append(f"{os.path.relpath(f, root)}: {msg}")

    for f, area in all_files:
        try:
            fm, sections = parse_record(f)
        except ValueError as e:
            err(f, str(e))
            continue

        # required-all fields
        for field in req_all:
            if field not in fm or fm[field] in (None, ""):
                err(f, f"missing required field '{field}'")

        tt = fm.get("task_type")
        rid = fm.get("id", "<no-id>")

        # id uniqueness
        if rid in seen_ids:
            err(f, f"duplicate id '{rid}' (also {os.path.relpath(seen_ids[rid], root)})")
        else:
            seen_ids[rid] = f

        # enum checks
        def check_enum(field, enum_name):
            if field in fm and fm[field] is not None:
                if fm[field] not in enums[enum_name]:
                    err(f, f"{field}='{fm[field]}' not in enum {enum_name}")
        check_enum("split", "split")
        check_enum("review_status", "review_status")
        check_enum("task_type", "task_type")
        check_enum("operating_mode", "operating_mode")
        check_enum("difficulty", "difficulty")
        check_enum("source_type", "source_type")
        check_enum("license_status", "license_status")
        check_enum("teacher_terms_status", "teacher_terms_status")
        if "dataset" in fm and fm["dataset"] != "dataset-a":
            err(f, f"dataset must be 'dataset-a', got '{fm.get('dataset')}'")

        # style_profile reference
        if fm.get("style_profile") not in (None, "") and \
                fm.get("style_profile") not in enums["profiles"]:
            err(f, f"style_profile='{fm.get('style_profile')}' not a known profile")

        # failure_modes items
        for lab in (fm.get("failure_modes") or []):
            if lab not in enums["failure_label"]:
                err(f, f"failure_modes label '{lab}' not in enum failure_label")

        # excluded_from_training must be bool
        if not isinstance(fm.get("excluded_from_training"), bool):
            err(f, "excluded_from_training must be a boolean")

        # required fields by task type
        for field in req_by_type.get(tt, []):
            if field not in fm or fm[field] in (None, "", []):
                err(f, f"[{tt}] missing required field '{field}'")

        # required sections
        need = list(sec_all) + list(sec_by_type.get(tt, []))
        for s in need:
            if s not in sections or not sections[s]:
                err(f, f"[{tt}] missing required section '## {s}'")

        # placement: approved-status must not live under drafts/
        if area == "drafts" and fm.get("review_status") in APPROVED_STATUSES:
            err(f, f"approved-status '{fm.get('review_status')}' in drafts/ directory")

        # (template_family, semantic_cluster) uniqueness
        key = (fm.get("template_family"), fm.get("semantic_cluster"))
        if key in fam_cluster:
            err(f, f"duplicate (template_family, semantic_cluster) {key} "
                   f"(also {os.path.relpath(fam_cluster[key], root)})")
        else:
            fam_cluster[key] = f

        # duplicate source context / gold response (exact, normalized)
        ctx = re.sub(r"\s+", " ", sections.get("Context", "")).strip()
        gold = re.sub(r"\s+", " ", sections.get("Gold Response", "")).strip()
        if ctx:
            if ctx in contexts:
                err(f, f"duplicate Context text (also {os.path.relpath(contexts[ctx], root)})")
            else:
                contexts[ctx] = f
        if gold:
            if gold in golds:
                err(f, f"duplicate Gold Response text (also {os.path.relpath(golds[gold], root)})")
            else:
                golds[gold] = f

        fam_counts[tt] = fam_counts.get(tt, 0) + 1

    return problems, {"records": len(all_files), "by_task_type": fam_counts,
                      "ids": len(seen_ids)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    problems, stats = validate(args.root)
    print("=== DATASET A VALIDATION ===")
    print("records:", stats["records"], "| by task_type:", stats["by_task_type"])
    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for p in problems:
            print("  !!", p)
        sys.exit(1)
    print("\nALL DATASET A RECORDS VALID")


if __name__ == "__main__":
    main()
