"""Baseline reproducibility gate (Part 9).

python -m linewright.reproducibility --run1 <eval1.json> --run2 <eval2.json> --out <repro.json>

Compares two base-model evaluation runs and yields a disposition:
  exact_match | normalized_match | materially_equivalent | failed
Progression to real training must abort on `failed`.
"""
import argparse
import hashlib
import json
import re


def _norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def _sha(s):
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def compare_runs(r1, r2):
    recs1 = {r["record_id"]: r for r in r1["records"]}
    recs2 = {r["record_id"]: r for r in r2["records"]}
    ids = sorted(set(recs1) | set(recs2))
    per_record = []
    exact = normalized = 0
    material = failed = 0
    disagreements = []

    if set(recs1) != set(recs2):
        return {"disposition": "failed", "reason": "record sets differ",
                "run1_ids": sorted(recs1), "run2_ids": sorted(recs2)}

    for rid in ids:
        a, b = recs1[rid], recs2[rid]
        raw_eq = a["raw_output"] == b["raw_output"]
        norm_eq = _norm(a["raw_output"]) == _norm(b["raw_output"])
        checks_eq = a["deterministic_checks"] == b["deterministic_checks"]
        parsed_eq = a["parsed_output"] == b["parsed_output"]
        valid_eq = a["format_valid"] == b["format_valid"]
        entry = {"record_id": rid, "raw_equal": raw_eq, "normalized_equal": norm_eq,
                 "deterministic_checks_equal": checks_eq, "parsed_equal": parsed_eq,
                 "format_valid_equal": valid_eq,
                 "len1": len(a["raw_output"] or ""), "len2": len(b["raw_output"] or "")}
        per_record.append(entry)
        # a material disagreement is one that would affect the benchmark
        if not (checks_eq and parsed_eq and valid_eq):
            failed += 1
            disagreements.append(rid)
        elif raw_eq:
            exact += 1
        elif norm_eq:
            normalized += 1
        else:
            material += 1

    if failed:
        disposition = "failed"
    elif material == 0 and normalized == 0:
        disposition = "exact_match"
    elif material == 0:
        disposition = "normalized_match"
    else:
        disposition = "materially_equivalent"

    return {
        "disposition": disposition,
        "record_count": len(ids),
        "exact_match": exact,
        "normalized_match": normalized,
        "materially_equivalent": material,
        "failed": failed,
        "material_disagreements": disagreements,
        "run1_raw_hash": _sha(json.dumps([recs1[i]["raw_output"] for i in ids])),
        "run2_raw_hash": _sha(json.dumps([recs2[i]["raw_output"] for i in ids])),
        "materially_equivalent_requires_reason": material > 0,
        "per_record": per_record,
        "accepted": disposition in ("exact_match", "normalized_match"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run1", required=True)
    ap.add_argument("--run2", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    r1 = json.load(open(args.run1, encoding="utf-8"))
    r2 = json.load(open(args.run2, encoding="utf-8"))
    result = compare_runs(r1, r2)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print(f"reproducibility: {result['disposition']} "
          f"(exact={result['exact_match']} norm={result['normalized_match']} "
          f"mat={result['materially_equivalent']} failed={result['failed']})")


if __name__ == "__main__":
    main()
