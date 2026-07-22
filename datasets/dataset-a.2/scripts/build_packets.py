"""Generate blind reviewer packets for the pilot evaluation records (Dispatch 21, Phase G).

Dispatch 21 does NOT train, so there are no checkpoint outputs yet. To exercise the packet
workflow end-to-end this uses the pilot's own authored responses as stand-in candidates
(the preferred response plus each rejected response), with their identities hidden behind
neutral ids. When a real training run exists, swap ``candidates_for`` to read model
outputs; the packet/keys structure is unchanged.

Writes:
  training/reviewer-packets/dataset-a.2-pilot/packet-<record_id>.json   (identity-free)
  training/reviewer-packets/dataset-a.2-pilot/keys.json                 (un-blinding, kept apart)
  training/reviewer-packets/dataset-a.2-pilot/README.md
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.reviewer_packet import build_packet, anonymization_ok
from linewright.evaluation.gates import evaluate_response, gate_summary
from linewright.evaluation import contracts as contract_mod

PILOT = os.path.join(_REPO, "datasets", "dataset-a.2", "pilot")
OUT = os.path.join(_REPO, "training", "reviewer-packets", "dataset-a.2-pilot")


def candidates_for(record, train_targets):
    """Stand-in candidates: the authored responses, identities hidden. Each carries a
    gate_summary (for the post-scoring key, never the packet body)."""
    spec = contract_mod.spec_from_record(record, train_targets=train_targets)
    cands = [{"identity": "authored-preferred", "output": record["preferred_response"]}]
    for i, rr in enumerate(record.get("rejected_responses", []) or []):
        cands.append({"identity": f"authored-rejected-{i}", "output": rr["response"]})
    for c in cands:
        gm = evaluate_response(c["output"], spec)
        c["gate_summary"] = gate_summary(gm)["gates"]
    return cands


def main():
    os.makedirs(OUT, exist_ok=True)
    ev = [json.loads(l) for l in open(os.path.join(PILOT, "evaluation.jsonl"), encoding="utf-8") if l.strip()]
    train_targets = [json.loads(l)["preferred_response"]
                     for l in open(os.path.join(PILOT, "train.jsonl"), encoding="utf-8") if l.strip()]
    keys = {}
    leaks = []
    for rec in ev:
        cands = candidates_for(rec, train_targets)
        packet, key = build_packet(rec, cands, seed="dispatch-21-pilot")
        leak = anonymization_ok(packet)
        if leak:
            leaks.append((rec["record_id"], leak))
        with open(os.path.join(OUT, f"packet-{rec['record_id']}.json"), "w",
                  encoding="utf-8", newline="\n") as fh:
            json.dump(packet, fh, ensure_ascii=False, indent=2); fh.write("\n")
        keys[rec["record_id"]] = key
    with open(os.path.join(OUT, "keys.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(keys, fh, ensure_ascii=False, indent=2); fh.write("\n")
    readme = (
        "# Blind reviewer packets — Dataset A.2 pilot (Dispatch 21, Phase G)\n\n"
        "Each `packet-<record_id>.json` is identity-free: candidates are labeled "
        "Candidate A/B/... in a deterministic, content-derived order that cannot leak "
        "identity. The packet never names base/LoRA/QAT, checkpoint step, loss, or gate "
        "scores.\n\n"
        "## Workflow\n"
        "1. Three reviewers (Aedan, Claude, ChatGPT) score every candidate on the 1-5 "
        "dimensions **independently**, choose an overall preference, and flag any fatal "
        "flaw — before any discussion.\n"
        "2. Only after a reviewer locks their scores is `keys.json` consulted to un-blind "
        "candidate identity and reveal the mechanical gate summary.\n"
        "3. Advancement is decided by `linewright/evaluation/advancement.py`: all three "
        "must prefer the candidate over base, zero fatal flags, zero schema/no-change/"
        "memorization/material regressions. A single fatal flag blocks advancement even "
        "if the other two approve; disagreement is investigated, not averaged.\n\n"
        "NOTE: Dispatch 21 does not train. These packets use the pilot's own authored "
        "responses as stand-in candidates to exercise the workflow; real packets will draw "
        "candidates from a future training run.\n")
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(readme)
    print(f"wrote {len(ev)} packets -> {OUT}")
    print("anonymization leaks:", leaks or "none")


if __name__ == "__main__":
    main()
