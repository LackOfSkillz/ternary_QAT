#!/usr/bin/env python3
"""Deterministic compiler: frozen Dataset A Markdown -> SFT JSONL.

Compiles ONLY records with review_status 'approved' and a train/evaluation split
(draft/unreviewed records are skipped). Byte-stable output: records sorted by id,
JSON with sort_keys, LF newlines. Rejected responses NEVER become the SFT target;
an optional separate preference file is written for train records that carry one.

Outputs (under compiled/experimental-v1/):
  train.jsonl, evaluation.jsonl, preference-train.jsonl, manifest.json, compile-report.md

Usage:
  python compile_dataset_a.py --root datasets/dataset-a --out-subdir experimental-v1 \
      --freeze-id dataset-a-experimental-v1 \
      --system-prompt datasets/dataset-a/prompts/linewright-training-system-v1.txt
"""
import argparse
import glob
import hashlib
import json
import os
import re
import statistics


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    return sha256_bytes(open(path, "rb").read())


def parse_record(path):
    raw = open(path, "rb").read()
    sha = sha256_bytes(raw)
    text = raw.decode("utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    import yaml
    fm = yaml.safe_load(m.group(1))
    body = m.group(2)
    secs, cur, buf = {}, None, []
    for line in body.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            if cur is not None:
                secs[cur] = "\n".join(buf).strip()
            cur, buf = h.group(1), []
        else:
            buf.append(line)
    if cur is not None:
        secs[cur] = "\n".join(buf).strip()
    return fm, secs, sha


def fence_inner(text):
    """Inner content of the first fenced ```lang\n...``` block, else None."""
    m = re.search(r"```[a-zA-Z0-9]*\r?\n(.*?)```", text or "", re.S)
    return m.group(1).strip() if m else None


def assistant_target(gold):
    """The gold training target: the fenced code (JSON/YAML contract, or structured
    no-change object) if present — which drops any trailing annotation prose — else
    the full gold prose."""
    inner = fence_inner(gold)
    return inner if inner is not None else (gold or "").strip()


def user_prompt(secs):
    return (secs.get("Instruction", "").strip() + "\n\n" +
            secs.get("Context", "").strip()).strip()


def approx_tokens(s):
    # deterministic char/4 heuristic; labeled approximate in the report
    return (len(s) + 3) // 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out-subdir", default="experimental-v1")
    ap.add_argument("--freeze-id", default="dataset-a-experimental-v1")
    ap.add_argument("--system-prompt", required=True)
    args = ap.parse_args()

    system = open(args.system_prompt, encoding="utf-8").read().strip()
    system_hash = sha256_file(args.system_prompt)

    rows = {"train": [], "evaluation": []}
    pref_rows = []
    manifest_records = []
    lengths = []

    for f in sorted(glob.glob(os.path.join(args.root, "drafts", "**", "*.md"), recursive=True)):
        fm, secs, sha = parse_record(f)
        # compile ONLY approved, train/evaluation records; skip draft/unreviewed
        if fm.get("review_status") != "approved":
            continue
        split = fm.get("split")
        if split not in ("train", "evaluation"):
            continue
        target = assistant_target(secs.get("Gold Response", ""))
        row = {
            "id": fm["id"],
            "task_type": fm["task_type"],
            "style_profile": fm.get("style_profile") or "none",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt(secs)},
                {"role": "assistant", "content": target},
            ],
            "metadata": {
                "split": split,
                "freeze_id": args.freeze_id,
                "source_hash": sha,
                "teacher_model": fm.get("teacher_model"),
                "invention_budget": (fm.get("invention_budget") or {}).get("level"),
            },
        }
        rows[split].append(row)
        manifest_records.append({"id": fm["id"], "split": split, "source_hash": sha,
                                 "task_type": fm["task_type"]})
        total_chars = sum(len(m["content"]) for m in row["messages"])
        lengths.append((fm["id"], approx_tokens("".join(m["content"] for m in row["messages"])),
                        total_chars))
        # optional preference pair (train only, if a rejected response exists)
        rej = secs.get("Rejected Response", "").strip()
        if split == "train" and rej:
            pref_rows.append({
                "id": fm["id"],
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt(secs)},
                ],
                "chosen": target,
                "rejected": assistant_target(rej),
                "metadata": {"freeze_id": args.freeze_id, "source_hash": sha},
            })

    for k in rows:
        rows[k].sort(key=lambda r: r["id"])
    pref_rows.sort(key=lambda r: r["id"])
    manifest_records.sort(key=lambda r: r["id"])

    out_dir = os.path.join(args.root, "compiled", args.out_subdir)
    os.makedirs(out_dir, exist_ok=True)

    def write_jsonl(name, data):
        p = os.path.join(out_dir, name)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            for r in data:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
        return p, sha256_file(p)

    train_p, train_h = write_jsonl("train.jsonl", rows["train"])
    eval_p, eval_h = write_jsonl("evaluation.jsonl", rows["evaluation"])
    pref_p, pref_h = write_jsonl("preference-train.jsonl", pref_rows)

    manifest = {
        "freeze_id": args.freeze_id,
        "compiled_from": "drafts",
        "format": "sft_messages",
        "system_prompt": {"path": os.path.relpath(args.system_prompt, args.root).replace("\\", "/"),
                          "sha256": system_hash},
        "row_counts": {"train": len(rows["train"]), "evaluation": len(rows["evaluation"]),
                       "preference_train": len(pref_rows)},
        "files": {
            "train": {"path": "train.jsonl", "sha256": train_h},
            "evaluation": {"path": "evaluation.jsonl", "sha256": eval_h},
            "preference_train": {"path": "preference-train.jsonl", "sha256": pref_h},
        },
        "records": manifest_records,
    }
    man_p = os.path.join(out_dir, "manifest.json")
    with open(man_p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    man_h = sha256_file(man_p)

    # report
    toks = sorted(t for _, t, _ in lengths)
    from collections import Counter
    tr_tasks = Counter(r["task_type"] for r in rows["train"])
    ev_tasks = Counter(r["task_type"] for r in rows["evaluation"])
    rep = [
        "# Dataset A compile report — experimental-v1", "",
        f"- freeze_id: `{args.freeze_id}`",
        f"- system prompt: `{manifest['system_prompt']['path']}`  sha256 `{system_hash[:16]}…`",
        f"- train rows: **{len(rows['train'])}**  (train.jsonl sha256 `{train_h[:16]}…`)",
        f"- evaluation rows: **{len(rows['evaluation'])}**  (evaluation.jsonl sha256 `{eval_h[:16]}…`)",
        f"- preference-train rows: **{len(pref_rows)}**  (preference-train.jsonl sha256 `{pref_h[:16]}…`)",
        f"- manifest.json sha256 `{man_h[:16]}…`", "",
        "## Approx token lengths (char/4 heuristic, whole example incl. system)", "",
        f"- system-prompt tokens (approx): {approx_tokens(system)}",
        f"- min / median / max example: {toks[0]} / {int(statistics.median(toks))} / {toks[-1]}",
        f"- total approx tokens (train): {sum(t for i,t,c in lengths if any(r['id']==i for r in rows['train']))}",
        "", "## Task distribution by split", "",
        f"- train: {dict(tr_tasks)}",
        f"- evaluation: {dict(ev_tasks)}", "",
        "## Discipline", "",
        "- Only `approved` train/evaluation records compiled; draft/unreviewed skipped.",
        "- Rejected responses are NOT SFT targets (separate preference-train.jsonl only).",
        "- Evaluation rows are held out (excluded_from_training: true on-record).",
        "- No reviewer notes / rejection reasons / evaluation text leak into targets.",
        "- Deterministic: sorted by id, sort_keys JSON, LF newlines.", "",
    ]
    with open(os.path.join(out_dir, "compile-report.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(rep))

    print(f"compiled train={len(rows['train'])} eval={len(rows['evaluation'])} "
          f"pref={len(pref_rows)} -> {out_dir}")
    print(f"train.jsonl {train_h[:16]} | evaluation.jsonl {eval_h[:16]} | manifest {man_h[:16]}")


if __name__ == "__main__":
    main()
