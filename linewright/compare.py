"""Comparison report entry point (Part 2).

python -m linewright.compare --base <j> --lora <j> --ternary-qat <j> --out <md>

Produces a small, trackable Markdown comparison of base / LoRA / ternary-QAT
evaluation runs on the same held-out records. Diagnostic only; a smoke comparison
is never evidence of production quality.
"""
import argparse
import json
import os

from linewright import config as C
from linewright import runtime


def _load(p):
    return json.load(open(p, encoding="utf-8")) if p and os.path.exists(p) else None


def build_md(base, lora, qat):
    targets = [("base", base), ("lora", lora), ("ternary-qat", qat)]
    present = [(n, r) for n, r in targets if r]
    L = ["# Dataset A smoke comparison", "",
         "Base / LoRA / ternary-QAT on the same 7 held-out records. Diagnostic only;",
         "NOT evidence of production quality.", "",
         "| target | records | format_valid | backend |", "|---|---|---|---|"]
    for n, r in present:
        L.append(f"| {n} | {r.get('record_count')} | {r.get('format_valid_count')} | "
                 f"{r.get('backend')} |")
    L += ["", "## Per-record format validity", "",
          "| record | " + " | ".join(n for n, _ in present) + " |",
          "|---|" + "|".join("---" for _ in present) + "|"]
    ids = sorted({rec["record_id"] for _, r in present for rec in r["records"]})
    for rid in ids:
        row = [rid]
        for _, r in present:
            rec = next((x for x in r["records"] if x["record_id"] == rid), None)
            row.append("✓" if rec and rec["format_valid"] else "✗" if rec else "—")
        L.append("| " + " | ".join(row) + " |")
    L += ["", "_Behavioral rubric scoring is recorded per record in each eval JSON for "
          "Gate review; this table is the mechanical format-validity summary only._", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    ap.add_argument("--lora")
    ap.add_argument("--ternary-qat", dest="ternary_qat")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    md = build_md(_load(args.base), _load(args.lora), _load(args.ternary_qat))
    writer = runtime.AuthorizedWriter([os.path.join(C.REPO_ROOT, r) for r in C.AUTHORIZED_OUTPUT_ROOTS])
    with writer.open(C.abs_repo(args.out), "w") as fh:
        fh.write(md)
    print(f"comparison -> {args.out}")


if __name__ == "__main__":
    main()
