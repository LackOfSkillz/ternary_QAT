"""Validate the fast battery before generation (Dispatch 24, Workstream E).

Checks: JSONL parses; unique item IDs; pair references resolve; every non-standalone item is
paired; every item resolves a behavior contract + provenance; every item is benchmark_only +
excluded_from_training; output_contract schema_id resolves; required modules + pair families
covered; no benchmark source overlaps Dataset A/A.2 beyond short boilerplate; no numeric
threshold embedded as a gate. Emits a pre-run validation report.
"""
import difflib
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation import contracts as contract_mod

REQUIRED_MODULES = set("ABCDEFGHI")   # J is embedded (slop analysis on prose outputs)
REQUIRED_FAMILY_TYPES = {"surface_pair", "restraint_pair", "canon_pair", "voice_pair",
                         "length_pair", "constraint_pair", "turn_pair"}


def load(name):
    p = os.path.join(_HERE, name)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def _dataset_sources():
    src = []
    for rel in ("datasets/dataset-a/compiled/experimental-v1/train.jsonl",
                "datasets/dataset-a/compiled/experimental-v1/evaluation.jsonl",
                "datasets/dataset-a.2/pilot/train.jsonl",
                "datasets/dataset-a.2/pilot/evaluation.jsonl"):
        p = os.path.join(_REPO, rel)
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            if "messages" in r:
                src.append(" ".join(m.get("content", "") for m in r["messages"]))
            else:
                src.append(r.get("input", {}).get("source", "") + " " + r.get("preferred_response", ""))
    return src


def validate():
    items = load("items.jsonl")
    contracts = {c["contract_id"]: c for c in load("contracts.jsonl")}
    families = {f["family_id"]: f for f in load("families.jsonl")}
    prov = {p["provenance_id"]: p for p in load("provenance.jsonl")}
    ids = [i["item_id"] for i in items]
    problems = []

    if len(ids) != len(set(ids)):
        problems.append("duplicate item_ids")
    for i in items:
        iid = i["item_id"]
        if i.get("benchmark_only") is not True:
            problems.append(f"[{iid}] benchmark_only must be true")
        if i.get("excluded_from_training") is not True:
            problems.append(f"[{iid}] excluded_from_training must be true")
        if i["behavior_contract_id"] not in contracts:
            problems.append(f"[{iid}] behavior contract does not resolve")
        if i["provenance_id"] not in prov:
            problems.append(f"[{iid}] provenance missing")
        if i.get("source_material_class") not in ("synthetic", "licensed", "public_domain",
                                                  "otherwise_distributable"):
            problems.append(f"[{iid}] invalid source_material_class")
        try:
            contract_mod.resolve(i["output_contract"])
        except Exception as e:
            problems.append(f"[{iid}] output_contract does not resolve: {e}")
        if i.get("is_standalone"):
            if not i.get("standalone_reason"):
                problems.append(f"[{iid}] standalone requires a reason")
        else:
            for pid in i.get("paired_item_ids", []):
                if pid not in ids:
                    problems.append(f"[{iid}] paired item {pid} missing")
            if not i.get("controlled_variable"):
                problems.append(f"[{iid}] paired item needs a controlled_variable")

    # family arms resolve
    for fid, f in families.items():
        for arm, iid in f["arms"].items():
            if iid not in ids:
                problems.append(f"[family {fid}] arm {arm} -> missing item {iid}")

    # module + family coverage
    modules = {i["module"][0] for i in items}
    missing_mod = REQUIRED_MODULES - modules
    if missing_mod:
        problems.append(f"missing required modules: {sorted(missing_mod)}")
    ftypes = {f["family_type"] for f in families.values()}
    missing_fam = REQUIRED_FAMILY_TYPES - ftypes
    if missing_fam:
        problems.append(f"missing required pair families: {sorted(missing_fam)}")

    # no numeric threshold embedded as a gate (contracts carry behaviors, not score floors)
    for cid, c in contracts.items():
        for k in ("required_behaviors", "forbidden_failures"):
            for v in c.get(k, []):
                if isinstance(v, (int, float)):
                    problems.append(f"[contract {cid}] numeric threshold embedded in {k}")

    # dataset overlap (no long verbatim overlap with Dataset A/A.2)
    ds = _dataset_sources()
    worst = 0.0
    for i in items:
        # check SOURCE/scenario content, not the shared task-instruction boilerplate (a
        # scene-contract/canon instruction template is legitimately shared across the family).
        s = i["input"].get("source", "") + " " + i["input"].get("context", "")
        if len(s.strip()) < 40:
            continue
        for d in ds:
            m = difflib.SequenceMatcher(None, s, d, autojunk=False).find_longest_match(
                0, len(s), 0, len(d))
            worst = max(worst, m.size)
            if m.size >= 120:   # a 120+ char verbatim span with a dataset record is leakage
                problems.append(f"[{i['item_id']}] {m.size}-char overlap with a dataset record")
                break
    return problems, {"items": len(items), "contracts": len(contracts),
                      "families": len(families), "modules": sorted(modules),
                      "family_types": sorted(ftypes),
                      "max_dataset_overlap_chars": worst}


def main():
    problems, stats = validate()
    report = {"dispatch": 24, "phase": "pre-run validation", "battery": "fast-v1",
              "stats": stats, "problems": problems, "valid": not problems}
    out = os.path.join(_HERE, "pre-run-validation-report.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"=== FAST BATTERY PRE-RUN VALIDATION ===\nstats={stats}")
    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for p in problems:
            print(" -", p)
        raise SystemExit(1)
    print("\nFAST BATTERY VALID — safe to freeze and generate")


if __name__ == "__main__":
    main()
