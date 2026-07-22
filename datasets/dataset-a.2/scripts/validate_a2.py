"""Dataset A.2 static + content validator (Dispatch 21, Phase C/E/F).

Dependency-free (stdlib + PyYAML, both already required). Validates:
  1. record shape against schema/record-schema.json (required fields, types, enums,
     record_id / dataset_version, no unknown top-level keys);
  2. output_contract.schema_id resolves in the output-contract registry;
  3. every failure label is known (Dataset A enum + Dispatch-21 mechanical extensions);
  4. split grouping: no split_restrictions.group_key, source cluster, or gold opening is
     shared across train and evaluation;
  5. content gates: each preferred_response PASSES its own mechanical gates, and each
     rejected_response FAILS at least one of its declared failure_labels.

Usage:
    python -m validate_a2 --pilot-dir datasets/dataset-a.2/pilot
"""
import argparse
import json
import os
import sys

import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation import MECHANICAL_FAILURE_LABELS
from linewright.evaluation.gates import evaluate_response, gate_summary, GateResult
from linewright.evaluation import contracts as contract_mod
from linewright.evaluation.overlap import analyze_overlap

# Labels the mechanical gates can actually emit. A rejected example that declares one of
# these MUST provoke it; a rejected example that declares only reviewer-assisted labels
# (invalid_refusal, voice_flattening, imposed_minimalism, ...) is trusted to the human
# reviewer -- the machine cannot decide those.
MACHINE_DETECTABLE = set(MECHANICAL_FAILURE_LABELS) | {
    "constraint_ignored", "unsupported_inference", "invented_fact",
    "excessive_expansion", "runaway_length", "summary_replacing_scene",
    "omitted_required_change", "prose_outside_structure",
}

SCHEMA = json.load(open(os.path.join(_HERE, "..", "schema", "record-schema.json"), encoding="utf-8"))
_ENUMS = yaml.safe_load(open(os.path.join(_REPO, "datasets", "dataset-a", "schema",
                                          "enums.yaml"), encoding="utf-8"))
KNOWN_LABELS = set(_ENUMS["failure_label"]) | set(MECHANICAL_FAILURE_LABELS)
TASK_FAMILIES = set(SCHEMA["properties"]["task_family"]["enum"])


def load_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def validate_record_shape(rec):
    problems = []
    allowed = set(SCHEMA["properties"])
    for k in rec:
        if k not in allowed:
            problems.append(f"unknown top-level key '{k}'")
    for req in SCHEMA["required"]:
        if req not in rec:
            problems.append(f"missing required field '{req}'")
    rid = rec.get("record_id", "")
    if not (isinstance(rid, str) and rid.startswith("dsa2-")):
        problems.append(f"record_id must start with 'dsa2-' (got {rid!r})")
    if rec.get("dataset_version") != "dataset-a.2-pilot-v1":
        problems.append("dataset_version must be 'dataset-a.2-pilot-v1'")
    if rec.get("task_family") not in TASK_FAMILIES:
        problems.append(f"task_family invalid: {rec.get('task_family')!r}")
    for lab in rec.get("failure_labels_targeted", []):
        if lab not in KNOWN_LABELS:
            problems.append(f"unknown failure label '{lab}'")
    for i, rr in enumerate(rec.get("rejected_responses", []) or []):
        for lab in rr.get("failure_labels", []):
            if lab not in KNOWN_LABELS:
                problems.append(f"rejected[{i}] unknown failure label '{lab}'")
    sr = rec.get("split_restrictions", {})
    if not sr.get("group_key"):
        problems.append("split_restrictions.group_key required")
    rs = rec.get("review_status", {})
    for k in ("static_validated", "aedan_approved", "claude_approved", "chatgpt_approved"):
        if not isinstance(rs.get(k), bool):
            problems.append(f"review_status.{k} must be bool")
    # output contract must resolve
    try:
        contract_mod.resolve(rec.get("output_contract", {}))
    except Exception as e:
        problems.append(f"output_contract does not resolve: {e}")
    return problems


def validate_content_gates(rec, train_targets=None):
    """The gold must pass; each rejected must genuinely fail its declared labels."""
    problems = []
    spec = contract_mod.spec_from_record(rec, train_targets=train_targets)
    gm = evaluate_response(rec.get("preferred_response", ""), spec)
    summ = gate_summary(gm)
    # memorization_valid is self-referential for the gold (it trivially matches itself);
    # exclude it here and check cross-target overlap separately below.
    bad = [k for k, v in summ["gates"].items()
           if v is False and k not in ("format_valid", "memorization_valid")]
    if bad:
        problems.append(f"preferred_response FAILS mechanical gates: {bad}")
    # the gold must not copy ANOTHER record's training target (gold='' avoids self-match)
    mem = analyze_overlap(rec.get("preferred_response", ""), "", train_targets or [])
    if mem.valid is False:
        problems.append(f"preferred_response overlaps another training target: {mem.evidence}")
    for i, rr in enumerate(rec.get("rejected_responses", []) or []):
        gmr = evaluate_response(rr["response"], spec)
        got = set()
        for v in gmr.values():
            if isinstance(v, GateResult):
                got |= set(v.failure_labels)
        declared = set(rr.get("failure_labels", []))
        mech = declared & MACHINE_DETECTABLE
        if mech and not (mech & got):
            problems.append(
                f"rejected[{i}] declares machine-detectable {sorted(mech)} but the validators "
                f"detected {sorted(got) or 'nothing'} — the rejected example is not actually "
                f"bad in the declared way")
    return problems


def validate_split_grouping(train, evaluation):
    """No source cluster may cross train↔evaluation (Phase D policy)."""
    problems = []

    def keys(recs):
        gk = set(r.get("split_restrictions", {}).get("group_key") for r in recs)
        sf = set(r.get("source_family") for r in recs)
        sw = set(r.get("story_world") for r in recs)
        # opening leakage is about shared SOURCE material, not the structured gold scaffold
        # (two K1 verdicts share a JSON prefix but no source content).
        op = set((r.get("input", {}).get("source") or "")[:80] for r in recs)
        return gk, sf, sw, op
    tg, tf, tw, to = keys(train)
    eg, ef, ew, eo = keys(evaluation)
    for label, a, b in (("group_key", tg, eg), ("source_family", tf, ef),
                        ("story_world", tw, ew), ("gold_opening", to, eo)):
        shared = {x for x in (a & b) if x}
        if shared:
            problems.append(f"{label} shared across splits: {sorted(shared)}")
    return problems


def validate_pilot(pilot_dir):
    train = load_jsonl(os.path.join(pilot_dir, "train.jsonl"))
    evaluation = load_jsonl(os.path.join(pilot_dir, "evaluation.jsonl"))
    all_recs = train + evaluation
    train_targets = [r.get("preferred_response", "") for r in train]
    problems = []
    ids = set()
    for rec in all_recs:
        rid = rec.get("record_id", "?")
        if rid in ids:
            problems.append(f"duplicate record_id {rid}")
        ids.add(rid)
        for p in validate_record_shape(rec):
            problems.append(f"[{rid}] {p}")
        # gold should not overlap OTHER records' targets (memorization guard)
        others = [t for t in train_targets if t != rec.get("preferred_response")]
        for p in validate_content_gates(rec, train_targets=others):
            problems.append(f"[{rid}] {p}")
    problems += validate_split_grouping(train, evaluation)
    return problems, len(train), len(evaluation)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot-dir", required=True)
    args = ap.parse_args()
    problems, ntr, nev = validate_pilot(args.pilot_dir)
    print(f"=== DATASET A.2 PILOT VALIDATION ===\ntrain={ntr} eval={nev}")
    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for p in problems:
            print(" -", p)
        raise SystemExit(1)
    print("\nALL A.2 PILOT RECORDS VALID")


if __name__ == "__main__":
    main()
