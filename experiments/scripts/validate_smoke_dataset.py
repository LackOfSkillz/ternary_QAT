#!/usr/bin/env python3
"""Validate the Run 1 smoke dataset (train + eval JSONL).

Checks structure, counts, per-task counts, uniqueness, split/exclusion flags,
and prints SHA-256 checksums. Exit code 0 only if every check passes.
"""
import argparse
import hashlib
import json
import sys

REQUIRED_FIELDS = {
    "id", "task_type", "system", "instruction", "context", "response",
    "source_type", "license_status", "provenance", "split",
    "excluded_from_training", "notes",
}
VALID_TASKS = {"canon_extraction", "constraint_check",
               "focused_revision", "fiction_compliance"}
TRAIN_PER_TASK = 20
EVAL_PER_TASK = 6
TRAIN_TOTAL = 80
EVAL_TOTAL = 24


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path, problems):
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                problems.append(f"{path}:{n}: invalid JSON: {e}")
    return rows


def check(cond, msg, problems):
    if not cond:
        problems.append(msg)


def validate(train_path, eval_path):
    problems = []
    train = load_jsonl(train_path, problems)
    eval_ = load_jsonl(eval_path, problems)

    # counts
    check(len(train) == TRAIN_TOTAL,
          f"train count {len(train)} != {TRAIN_TOTAL}", problems)
    check(len(eval_) == EVAL_TOTAL,
          f"eval count {len(eval_)} != {EVAL_TOTAL}", problems)

    train_task_counts = {t: 0 for t in VALID_TASKS}
    eval_task_counts = {t: 0 for t in VALID_TASKS}
    all_ids = []
    train_ids, eval_ids = set(), set()
    triples = {}

    def scan(rows, split_name, is_eval):
        for r in rows:
            rid = r.get("id", "<no-id>")
            all_ids.append(rid)
            missing = REQUIRED_FIELDS - set(r)
            check(not missing, f"{rid}: missing fields {missing}", problems)
            tt = r.get("task_type")
            check(tt in VALID_TASKS, f"{rid}: bad task_type {tt}", problems)
            if tt in VALID_TASKS:
                (eval_task_counts if is_eval else train_task_counts)[tt] += 1
            # non-empty instruction/response
            check(bool(str(r.get("instruction", "")).strip()),
                  f"{rid}: empty instruction", problems)
            check(bool(str(r.get("response", "")).strip()),
                  f"{rid}: empty response", problems)
            # split + exclusion flags
            if is_eval:
                eval_ids.add(rid)
                check(r.get("split") == "held_out",
                      f"{rid}: eval split != held_out ({r.get('split')})", problems)
                check(r.get("excluded_from_training") is True,
                      f"{rid}: eval excluded_from_training != true", problems)
            else:
                train_ids.add(rid)
                check(r.get("excluded_from_training") is False,
                      f"{rid}: train excluded_from_training != false", problems)
            # duplicate triple detection
            key = (r.get("instruction"), r.get("context"), r.get("response"))
            if key in triples:
                problems.append(f"{rid}: duplicate instruction/context/response "
                                f"triple (also {triples[key]})")
            else:
                triples[key] = rid

    scan(train, "train", False)
    scan(eval_, "eval", True)

    # unique IDs across both
    if len(all_ids) != len(set(all_ids)):
        dupes = {i for i in all_ids if all_ids.count(i) > 1}
        problems.append(f"duplicate IDs across files: {sorted(dupes)}")
    # no train ID in eval
    overlap = train_ids & eval_ids
    check(not overlap, f"train IDs appear in eval: {sorted(overlap)}", problems)

    # per-task counts
    for t in VALID_TASKS:
        check(train_task_counts[t] == TRAIN_PER_TASK,
              f"train {t}: {train_task_counts[t]} != {TRAIN_PER_TASK}", problems)
        check(eval_task_counts[t] == EVAL_PER_TASK,
              f"eval {t}: {eval_task_counts[t]} != {EVAL_PER_TASK}", problems)

    return problems, train_task_counts, eval_task_counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--eval", required=True)
    args = ap.parse_args()

    problems, tcounts, ecounts = validate(args.train, args.eval)

    print("=== CHECKSUMS (SHA-256) ===")
    print(f"train: {sha256(args.train)}  {args.train}")
    print(f"eval:  {sha256(args.eval)}  {args.eval}")
    print("=== PER-TASK COUNTS ===")
    print("train:", {k: tcounts[k] for k in sorted(tcounts)})
    print("eval: ", {k: ecounts[k] for k in sorted(ecounts)})

    if problems:
        print(f"\n=== {len(problems)} PROBLEM(S) ===")
        for p in problems:
            print("  !!", p)
        sys.exit(1)
    print("\nALL DATASET CHECKS PASSED")


if __name__ == "__main__":
    main()
