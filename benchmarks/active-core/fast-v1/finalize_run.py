"""Finalize the live dual-GX10 fast-battery run (Dispatch 24 continuation, Phases 4-8).

Consumes the frozen plan + the collected normalized results (from both nodes), ingests them
into a durable SQLite ledger, verifies output integrity, runs the mechanical gates (with
deterministic replay validation) + Module-J slop analysis + per-role corpus summaries, builds
blind reviewer packets (absolute-first, 4 hidden calibration seeds, identity-stripped), and
writes the completed run report. Model identity never reaches a reviewer packet.

Run (locally, after collecting outputs into normalized-results/):
  python finalize_run.py
"""
import glob
import hashlib
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.battery.score import score_run, load_battery
from linewright.evaluation.battery import packets as pk
from linewright.evaluation.execution.ledger import Ledger
from linewright.evaluation.execution.plan import job_tuples, verify_plan_hash
from linewright.evaluation.calibration.records import load_calibration_set
from linewright.evaluation.calibration.replay import replay, replay_passed
from linewright.evaluation.gates import evaluate_response
from linewright.evaluation.battery.score import spec_for

RUN_ID = "lwdb-fast-v1-20260722"
RUN_DIR = os.path.join(_REPO, "benchmarks", "runs", RUN_ID)
NORM = os.path.join(RUN_DIR, "normalized-results")


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_plan():
    return json.load(open(os.path.join(RUN_DIR, "generation-plan.json"), encoding="utf-8"))


def load_norm():
    return [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(NORM, "*.json")))]


def verify_integrity(plan, results):
    problems, seen = [], set()
    for r in results:
        iid, role = r["benchmark_item_id"], r["model_role"]
        jid = r["job_id"]
        if jid in seen:
            problems.append(f"duplicate job {jid}")
        seen.add(jid)
        if r["output_hash"] != _sha(r["output_text"]):
            problems.append(f"{jid}: output hash mismatch")
        if r["prompt_hash"] != plan["item_hashes"].get(iid):
            problems.append(f"{jid}: prompt hash != plan")
        if r["behavior_contract_hash"] != plan["behavior_contract_hashes"].get(iid):
            problems.append(f"{jid}: contract hash != plan")
        if r["generation_settings_hash"] != plan["generation_settings_hash"]:
            problems.append(f"{jid}: gen-settings hash != plan")
        if role not in ("target_base", "new_candidate"):
            problems.append(f"{jid}: bad role {role}")
    expected = {f"{RUN_ID}::{i}::{ro}" for i, ro in job_tuples(plan)}
    got = {r["job_id"] for r in results}
    missing = expected - got
    if missing:
        problems.append(f"missing jobs: {sorted(missing)}")
    return problems, {"expected": len(expected), "got": len(got), "missing": len(missing)}


def ingest_ledger(plan, results):
    db = os.path.join(RUN_DIR, "run-ledger.sqlite")
    if os.path.exists(db):
        os.remove(db)
    lg = Ledger(db)
    lg.create_run(RUN_ID, plan["plan_id"], plan["plan_hash"], plan["execution_mode"],
                  "persistent_remote", now=0)
    lg.add_jobs(RUN_ID, job_tuples(plan), input_hashes=plan["item_hashes"])
    for i, r in enumerate(results):
        p = os.path.join(NORM, r["job_id"].replace(":", "_") + ".json")
        lg.complete_job(r["job_id"], p, r["output_hash"], now=i + 1)
    counts = lg.counts(RUN_ID)
    if not any(c for s, c in counts.items() if s != "completed"):
        lg.set_run_state(RUN_ID, "completed", now=999, completed_at=999)
    lg.close()
    return counts


def replay_mechanical(results):
    """Deterministic replay: score each output twice; hashes must match."""
    items, contracts = load_battery()
    replays = []
    for r in results:
        it = items[r["benchmark_item_id"]]
        c = contracts[it["behavior_contract_id"]]
        spec = spec_for(it, c)
        rep = replay("battery-mechanical", "v1",
                     lambda out: evaluate_response(out, spec, hit_token_cap=r.get("hit_token_cap", False)),
                     r["output_text"])
        replays.append(rep)
    return replays


def main():
    plan = load_plan()
    assert verify_plan_hash(plan), "plan hash does not verify"
    results = load_norm()
    print(f"collected {len(results)} normalized results")

    integ_problems, integ_stats = verify_integrity(plan, results)
    counts = ingest_ledger(plan, results)
    replays = replay_mechanical(results)
    replay_ok = replay_passed(replays)

    scored = score_run(results)
    items_by_id, _ = load_battery()
    items_by_id = {k: v for k, v in items_by_id.items()}
    cal = load_calibration_set(os.path.join(_REPO, "benchmarks", "calibration",
                                            "grader-calibration-set-v1.jsonl"))[:4]
    units, akey = pk.build_absolute_packets(results, items_by_id, calibration_records=cal)
    leaks = pk.identity_leak_check(units)
    pw, pwkey = pk.build_pairwise_packets(results, items_by_id)

    # write artifacts (bulky ones git-ignored; report + summaries committed)
    def w(sub, name, obj):
        d = os.path.join(RUN_DIR, sub)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=2)
    w("mechanical-results", "mechanical.json", [o["mechanical"] for o in scored["per_output"]])
    for o in scored["per_output"]:
        w("slop-reports", f"{o['model_role']}__{o['item_id']}.json", o["slop"])
    for role, cs in scored["corpus_summaries"].items():
        w("corpus-summaries", f"{role}.json", cs)
    w("reviewer-packets", "absolute-units.json", units)
    w("reviewer-packets", "pairwise-packets.json", pw)
    w("reviewer-packets/calibration-key", "keys.json", {"absolute": akey, "pairwise": pwkey})

    # aggregate for the report
    def agg(role):
        outs = [o for o in scored["per_output"] if o["model_role"] == role]
        mech_fail = sum(1 for o in outs if not o["mechanical"]["mechanical_pass"])
        from collections import Counter
        labels = Counter(l for o in outs for l in o["mechanical"]["failure_labels"])
        sev = Counter(o["slop"]["summary"]["severity"] for o in outs)
        return {"outputs": len(outs), "mechanical_pass": len(outs) - mech_fail,
                "mechanical_fail": mech_fail, "top_failure_labels": dict(labels.most_common(6)),
                "slop_severity": dict(sev)}

    summary = {
        "run_id": RUN_ID, "plan_hash": plan["plan_hash"], "execution_mode": plan["execution_mode"],
        "base_host": "gx10-9141", "candidate_host": "gx10-5611",
        "completion": {"job_counts": counts, **integ_stats},
        "integrity_problems": integ_problems,
        "instrument": {"mechanical_replay_identical": replay_ok,
                       "instrument_valid": bool(replay_ok and not integ_problems),
                       "overall": "ok" if (replay_ok and not integ_problems) else "insufficient_evidence"},
        "mechanical": {"target_base": agg("target_base"), "new_candidate": agg("new_candidate")},
        "slop": {"per_output_reports": len(scored["per_output"]),
                 "corpus_summaries": list(scored["corpus_summaries"]),
                 "thresholds_status": "unvalidated", "semantic_detector_status": "interface_only"},
        "review": {"absolute_units": len(units), "pairwise_packets": len(pw),
                   "calibration_items_seeded": len(cal), "identity_leaks": leaks,
                   "independent_review_status": "pending (implementation agent is not a blind reviewer)"},
        "advancement_decision_deferred_to_dispatch_25": True,
    }
    with open(os.path.join(RUN_DIR, "completed-run-summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    # compact, committable per-item evidence (no full model text — that stays in the
    # git-ignored normalized-results/; only verdicts, hashes, and metadata are committed)
    by = {r["job_id"]: r for r in results}
    rows = []
    for o in scored["per_output"]:
        r = by[f"{RUN_ID}::{o['item_id']}::{o['model_role']}"]
        rows.append({"item_id": o["item_id"], "model_role": o["model_role"],
                     "mechanical_pass": o["mechanical"]["mechanical_pass"],
                     "failure_labels": o["mechanical"]["failure_labels"],
                     "slop_severity": o["slop"]["summary"]["severity"],
                     "dominant_slop": o["slop"]["summary"]["dominant_failure_types"],
                     "hit_token_cap": r.get("hit_token_cap"), "output_tokens": r.get("output_tokens"),
                     "output_hash": r["output_hash"]})
    rows.sort(key=lambda x: (x["item_id"], x["model_role"]))
    with open(os.path.join(RUN_DIR, "item-level-results.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(json.dumps({"jobs": integ_stats, "replay_ok": replay_ok, "leaks": leaks,
                      "base": agg("target_base"), "candidate": agg("new_candidate")}, indent=1))


if __name__ == "__main__":
    main()
