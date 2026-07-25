"""Dispatch 30G — serialize the 54-pair training corpus into two controlled SFT arms.

Two arms from the SAME 54 targets, identical in every respect EXCEPT the packet representation:
  atomic arm       -> Atomic packet as the user prompt
  compositional arm -> Compositional packet as the user prompt

Each record: frozen system + packet-as-user-prompt + unchanged target prose as the assistant
completion (completion-only loss is applied at encode time in the trainer). No provenance, no other
arm's packet, no structural-risk / reviewer metadata. Records carry split flags so the contamination
guard (serialization_guard.assert_training_safe) can verify no held-out c01 record is present.

Private output (git-ignored):
  private-data/serialized/qwen3-8b/atomic/train.jsonl
  private-data/serialized/qwen3-8b/compositional/train.jsonl
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from serialize_packet import SYSTEM, render_user  # noqa: E402
from serialization_guard import assert_training_safe  # noqa: E402

TP = os.path.join(EXP, "private-data", "training-packets")
TARGETS = os.path.join(EXP, "private-data", "targets")
ACCEPTED = os.path.join(EXP, "manifests", "accepted-passages.jsonl")
OUTROOT = os.path.join(EXP, "private-data", "serialized", "qwen3-8b")
BATCHES = ("batch1rev", "batch2rev", "batch3rev", "batch4rev", "batch5rev")


def load_jsonl(path, key):
    return {json.loads(l)[key]: json.loads(l) for l in open(path, encoding="utf-8") if l.strip()}


def main():
    acc = {json.loads(l)["passage_id"]: json.loads(l)
           for l in open(ACCEPTED, encoding="utf-8") if l.strip()}
    comp, atom = {}, {}
    for b in BATCHES:
        comp.update(load_jsonl(os.path.join(TP, f"{b}-compositional.jsonl"), "record_id"))
        atom.update(load_jsonl(os.path.join(TP, f"{b}-atomic.jsonl"), "record_id"))
    passages = sorted({rid[:-2] for rid in comp})     # canonical, identical order for both arms
    assert len(passages) == 54, f"expected 54 passages, got {len(passages)}"

    FLAGS = {"split": "production_train", "training_eligible": True, "evaluation_eligible": False}
    arms = {"atomic": atom, "compositional": comp}
    out_counts = {}
    for arm, recs in arms.items():
        rows = []
        for pid in passages:
            rid = f"{pid}-{'A' if arm == 'atomic' else 'C'}"
            r = recs[rid]
            tgt_hash = r["target"]["target_sha256"]
            assert tgt_hash == acc[pid]["target_sha256"], f"hash mismatch {pid}"
            gold = json.load(open(os.path.join(TARGETS, pid + ".json"), encoding="utf-8"))["text"]
            rows.append({
                "record_id": rid, "passage_id": pid, "arm": arm, **FLAGS,
                "system": SYSTEM,
                "prompt": render_user(r["training_packet"]),   # user message (packet only)
                "gold_output": gold,                            # unchanged target prose (completion)
                "target_sha256": tgt_hash,
            })
        # guard: must be training-safe (no held-out c01)
        assert_training_safe(rows, context=f"serialize {arm} arm")
        outdir = os.path.join(OUTROOT, arm)
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "train.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
            for x in rows:
                fh.write(json.dumps(x, ensure_ascii=False) + "\n")
        out_counts[arm] = {"records": len(rows),
                           "unique_targets": len({x["target_sha256"] for x in rows}),
                           "unique_record_ids": len({x["record_id"] for x in rows})}
    print(json.dumps({"passages": len(passages), "order_identical_across_arms": True,
                      "arms": out_counts}, indent=1))


if __name__ == "__main__":
    main()
