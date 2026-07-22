"""Output-contract registry loader (Dispatch 21, Phase C glue).

Resolves a Dataset A.2 record's ``output_contract.schema_id`` to the full machine-checkable
contract from ``datasets/dataset-a.2/schema/output-contracts.yaml``, merged with any
per-record overrides. The result is what :func:`linewright.evaluation.gates.evaluate_response`
consumes, so every record in a family is judged by the same gate unless it deliberately
overrides a field.
"""
import os

import yaml

from linewright import config as C

REGISTRY_PATH = os.path.join("datasets", "dataset-a.2", "schema", "output-contracts.yaml")


def load_registry(path=None):
    p = C.abs_repo(path or REGISTRY_PATH)
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)["contracts"]


def resolve(record_output_contract, registry=None):
    """Return the merged contract dict for a record's ``output_contract``.

    Record fields win over registry defaults (an override is intentional). ``schema_id``
    must exist in the registry.
    """
    reg = registry if registry is not None else load_registry()
    oc = dict(record_output_contract or {})
    sid = oc.get("schema_id")
    if sid not in reg:
        raise KeyError(f"unknown schema_id {sid!r}; known: {sorted(reg)}")
    merged = dict(reg[sid])
    merged.update({k: v for k, v in oc.items() if k != "schema_id"})
    merged["schema_id"] = sid
    return merged


def spec_from_record(record, registry=None, train_targets=None):
    """Build the :func:`evaluate_response` ``spec`` from an A.2 record."""
    contract = resolve(record.get("output_contract", {}), registry)
    exps = dict(record.get("validation_expectations") or {})
    if exps.get("changed") is False:
        contract["expects_no_change"] = True
        exps["expects_no_change"] = True
    return {
        "output_contract": contract,
        "source": record.get("input", {}).get("source", "") or "",
        "gold": record.get("preferred_response", "") or "",
        "validation_expectations": exps,
        "train_targets": train_targets or [],
    }
