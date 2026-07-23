"""Dispatch 30A-R1 — build the private token-count input file. For each atomic/compositional record it
pairs the frozen system prompt + serialized packet (the exact model input) with the unchanged gold
target, so the GX10 tokenizer can measure exact input/target/total tokens. Output is PRIVATE
(contains target text); only token COUNTS return from the GX10. No prose is printed.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from serialize_packet import SYSTEM, render_user  # noqa: E402

TARGETS = os.path.join(EXP, "private-data", "targets")
COMPO = os.path.join(EXP, "manifests", "compositional-records.jsonl")
ATOMIC = os.path.join(EXP, "manifests", "atomic-records.jsonl")
OUT = os.path.join(EXP, "private-data", "tokcount-input.jsonl")


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def main():
    rows = []
    for rec in load(COMPO) + load(ATOMIC):
        pid = rec["record_id"].rsplit("-", 1)[0]
        target = json.load(open(os.path.join(TARGETS, pid + ".json"), encoding="utf-8"))["text"]
        rows.append({"record_id": rec["record_id"], "arm": rec["arm"],
                     "source_filename": rec["target"]["source_filename"],
                     "system": SYSTEM, "user": render_user(rec["training_packet"]), "target": target})
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"records": len(rows),
                      "arms": {a: sum(1 for r in rows if r["arm"] == a) for a in ("atomic", "compositional")}}, indent=1))


if __name__ == "__main__":
    main()
