"""Select a focused, genuinely-blind reviewer packet from the anonymous units (Dispatch 26, D5).

Reads only review/anonymous (never the identity key). Selects core-prose units + scene-drafting
packet units + a sample of hidden calibration items, and emits a compact reviewer packet
(unit_id + task_context + text only — no identity). Sub-agent reviewers score this packet
blind; their scores are then locked and only afterwards mapped back to models.
"""
import glob
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RUN = os.path.join(_REPO, "benchmarks", "runs", "lwdb-stronger-base-v1")
ANON = os.path.join(RUN, "review", "review", "anonymous", "absolute-units")
PRIVATE = os.path.join(RUN, "private-unblinding", "identity-key.json")


def main():
    units = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(ANON, "*.json")))]
    key = json.load(open(PRIVATE, encoding="utf-8"))["units"]
    selected = []
    for u in units:
        tc = u.get("task_context", "")
        k = key.get(u["unit_id"], {})
        is_cal = k.get("calibration", False)
        keep = (tc == "core-prose") or ("scene_drafting-realistic" in tc) or ("scene_drafting-long" == tc.split(":")[-1]) or is_cal
        if keep and len(u.get("text", "").strip()) > 0:
            selected.append({"unit_id": u["unit_id"], "task_context": tc, "text": u["text"]})
    # cap calibration to 6 to keep the packet compact but calibrated
    cal_ids = [u["unit_id"] for u in selected if key.get(u["unit_id"], {}).get("calibration")]
    keep_cal = set(cal_ids[:6])
    selected = [u for u in selected if not key.get(u["unit_id"], {}).get("calibration") or u["unit_id"] in keep_cal]
    out = os.path.join(RUN, "review", "review", "anonymous", "reviewer-packet.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(selected, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"selected_units": len(selected),
                      "core_prose": sum(1 for u in selected if u["task_context"] == "core-prose"),
                      "scene": sum(1 for u in selected if u["task_context"].startswith("packet:scene")),
                      "calibration": len(keep_cal), "packet_file": os.path.relpath(out, _REPO)}, indent=1))


if __name__ == "__main__":
    main()
