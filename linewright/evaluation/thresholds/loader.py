"""Load + schema-validate provisional threshold files (Dispatch 25, D3)."""
import os

import yaml

from linewright import config as C

REQUIRED_META = {
    "research-continuation-v0": {"authorship": "agent_proposed", "authority": "delegated_by_gary",
                                 "status": "provisional", "final_product_ship_threshold": False},
    "starter-model-acceptance-v0": {"authorship": "agent_proposed", "authority": "delegated_by_gary",
                                    "status": "provisional", "final_commercial_ship_gate": False},
}


def load(path):
    with open(C.abs_repo(path), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def validate_metadata(doc):
    """Return a list of problems (empty == valid) for a threshold document."""
    problems = []
    tid = doc.get("threshold_id")
    req = REQUIRED_META.get(tid)
    if req is None:
        return [f"unknown threshold_id {tid!r}"]
    for k, v in req.items():
        if doc.get(k) != v:
            problems.append(f"[{tid}] {k} must be {v!r} (got {doc.get(k)!r})")
    # no threshold may claim final/ship authority
    if doc.get("final_product_ship_threshold") is True or doc.get("final_commercial_ship_gate") is True:
        problems.append(f"[{tid}] must not claim final ship authority")
    return problems
