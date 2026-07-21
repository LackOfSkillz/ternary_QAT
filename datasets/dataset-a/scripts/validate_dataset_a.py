#!/usr/bin/env python3
"""Mechanical validator for Dataset A source records (Markdown + YAML front
matter). Lightweight on purpose: it checks structure/enums/uniqueness/placement,
it does NOT compile training data. Exit 0 only if every record passes.

Usage:
  python validate_dataset_a.py --root datasets/dataset-a
"""
import argparse
import glob
import json
import os
import re
import sys

import yaml

APPROVED_STATUSES = {"substantively_approved", "author_approved", "frozen"}

# a declared constraint line in a ## Context block, e.g. "- C1 (established fact): ..."
_CONSTRAINT_DECL_RE = re.compile(r"^\s*-\s*([A-Z][A-Za-z]*\d+)\b")

PUBLIC_DOMAIN_FIELDS = ["title", "author", "publication_year",
                        "edition_or_archive", "source_url_or_identifier",
                        "verification_note"]


def declared_constraint_ids(context_text):
    """IDs declared in a constraint_check ## Context (C1, K1, D2, O3, S1, ...)."""
    return [m.group(1) for m in
            (_CONSTRAINT_DECL_RE.match(ln) for ln in context_text.splitlines())
            if m]


def extract_gold_json(gold_text):
    """Return the parsed JSON object in a gold response (from a fenced ```json
    block if present, else the whole section), or None if it is not JSON."""
    m = re.search(r"```(?:json)?\s*(.*?)```", gold_text, re.S)
    candidate = (m.group(1) if m else gold_text).strip()
    try:
        return json.loads(candidate)
    except Exception:
        return None


def _norm_ws(t):
    return re.sub(r"\s+", " ", t or "").strip()


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
    allowed_fields = set(schema["fields"].keys())
    allow_unknown = schema.get("allow_unknown_fields", True)

    draft_files = sorted(glob.glob(os.path.join(root, "drafts", "**", "*.md"), recursive=True))
    approved_files = sorted(glob.glob(os.path.join(root, "approved", "**", "*.md"), recursive=True))
    all_files = [(f, "drafts") for f in draft_files] + [(f, "approved") for f in approved_files]

    seen_ids = {}
    fam_cluster = {}
    contexts = {}
    golds = {}
    fam_counts = {}
    matched = {}     # id -> matched_pair_with
    id_task = {}     # id -> task_type

    def err(f, msg):
        problems.append(f"{os.path.relpath(f, root)}: {msg}")

    for f, area in all_files:
        try:
            fm, sections = parse_record(f)
        except ValueError as e:
            err(f, str(e))
            continue

        # unknown front-matter keys (schema keys only; free-form sections are fine)
        if not allow_unknown:
            for key in fm:
                if key not in allowed_fields:
                    err(f, f"unknown front-matter field '{key}' (not declared in schema)")

        # required-all fields
        for field in req_all:
            if field not in fm or fm[field] in (None, ""):
                err(f, f"missing required field '{field}'")

        tt = fm.get("task_type")
        rid = fm.get("id", "<no-id>")
        id_task[rid] = tt
        if fm.get("matched_pair_with"):
            matched[rid] = fm["matched_pair_with"]

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
        check_enum("origin", "origin")
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

        # required fields by task type. causal_constraint_ids may legitimately be
        # an empty list (a non-violation), so only its presence is required here;
        # its contents are checked by the causal-set grading below.
        for field in req_by_type.get(tt, []):
            empty = fm.get(field) in (None, "", []) and field != "causal_constraint_ids"
            if field not in fm or empty:
                err(f, f"[{tt}] missing required field '{field}'")

        # required sections
        need = list(sec_all) + list(sec_by_type.get(tt, []))
        for s in need:
            if s not in sections or not sections[s]:
                err(f, f"[{tt}] missing required section '## {s}'")

        # ---- constraint_check causal-set grading ----
        if tt == "constraint_check":
            declared = set(declared_constraint_ids(sections.get("Context", "")))
            causal = fm.get("causal_constraint_ids")
            if not isinstance(causal, list):
                err(f, "causal_constraint_ids must be a list")
                causal = []
            if len(causal) != len(set(causal)):
                err(f, f"causal_constraint_ids has duplicate IDs: {causal}")
            for cid in causal:
                if cid not in declared:
                    err(f, f"causal_constraint_ids references undeclared "
                           f"constraint '{cid}' (declared: {sorted(declared)})")
            gold = extract_gold_json(sections.get("Gold Response", ""))
            if gold is None or "constraint_ids" not in gold:
                err(f, "[constraint_check] gold response must be JSON with a "
                       "'constraint_ids' array")
            else:
                gold_ids = gold.get("constraint_ids")
                if not isinstance(gold_ids, list):
                    err(f, "gold constraint_ids must be an array")
                    gold_ids = []
                if len(gold_ids) != len(set(gold_ids)):
                    err(f, f"gold constraint_ids has duplicate IDs: {gold_ids}")
                for cid in gold_ids:
                    if cid not in declared:
                        err(f, f"gold constraint_ids references undeclared "
                               f"constraint '{cid}'")
                if set(gold_ids) != set(causal):
                    missing = sorted(set(causal) - set(gold_ids))
                    extra = sorted(set(gold_ids) - set(causal))
                    err(f, f"gold constraint_ids {sorted(gold_ids)} != causal set "
                           f"{sorted(causal)} (missing {missing}, extra {extra})")
                if gold.get("violation") is False and (gold_ids or causal):
                    err(f, "non-violation must have empty constraint_ids AND "
                           "causal_constraint_ids")

        # ---- invention_budget (focused_revision) ----
        if tt == "focused_revision":
            ib = fm.get("invention_budget")
            if not isinstance(ib, dict):
                err(f, "invention_budget must be a mapping {level, allowed, prohibited}")
            else:
                level = ib.get("level")
                allowed = ib.get("allowed")
                prohibited = ib.get("prohibited")
                if level not in ("none", "bounded", "open"):
                    err(f, f"invention_budget.level '{level}' not in none|bounded|open")
                if not isinstance(allowed, list):
                    err(f, "invention_budget.allowed must be a list")
                    allowed = []
                if not isinstance(prohibited, list):
                    err(f, "invention_budget.prohibited must be a list")
                    prohibited = []
                if level == "none" and allowed:
                    err(f, "invention_budget.level 'none' must not declare "
                           "affirmative allowances")
                if level == "bounded" and not allowed:
                    err(f, "invention_budget.level 'bounded' must list at least "
                           "one allowance")
                if level == "open" and not prohibited:
                    err(f, "invention_budget.level 'open' must still state prohibitions")

            # no-change protocol: structured gold with changed==false must echo source
            gold = extract_gold_json(sections.get("Gold Response", ""))
            if isinstance(gold, dict) and gold.get("changed") is False:
                src = _norm_ws(re.sub(r"^(Sentence|Passage):\s*", "",
                                      sections.get("Context", "")))
                if _norm_ws(gold.get("text", "")) != src:
                    err(f, "no-change gold (changed:false) 'text' must exactly "
                           "match the ## Context source")

        # ---- public-domain provenance ----
        if fm.get("source_type") == "public_domain":
            pds = fm.get("public_domain_source")
            if not isinstance(pds, dict):
                err(f, "source_type 'public_domain' requires a public_domain_source block")
            else:
                for pf in PUBLIC_DOMAIN_FIELDS:
                    if pf not in pds or pds[pf] in (None, ""):
                        err(f, f"public_domain_source missing '{pf}'")

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

    # matched_pair_with: existence, reciprocity, compatible task types
    for rid, partner in matched.items():
        loc = seen_ids.get(rid, "<?>")
        if partner not in seen_ids:
            problems.append(f"{os.path.relpath(loc, root)}: matched_pair_with "
                            f"'{partner}' does not exist")
            continue
        back = matched.get(partner)
        if back != rid:
            problems.append(f"{os.path.relpath(loc, root)}: matched pair with "
                            f"'{partner}' is not reciprocal (partner points to '{back}')")
        if id_task.get(rid) != id_task.get(partner):
            problems.append(f"{os.path.relpath(loc, root)}: matched pair task_type "
                            f"mismatch ({id_task.get(rid)} vs {id_task.get(partner)})")

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
