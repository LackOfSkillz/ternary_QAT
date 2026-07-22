"""Output-integrity verification before a resume skips a completed job (Workstream C9).

Never silently trust a missing or corrupted output. A completed job is skipped on resume
ONLY when: the result record + output file exist, the output hash matches, the item hash and
behavior-contract hash match the frozen plan, the generation-settings hash matches, and the
model-role assignment matches. Any failure demotes completed -> interrupted.
"""
import hashlib
import json
import os


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def result_path(output_dir, job_id):
    return os.path.join(output_dir, job_id.replace(":", "_").replace("/", "_") + ".json")


def write_result(output_dir, job_id, result):
    os.makedirs(output_dir, exist_ok=True)
    p = result_path(output_dir, job_id)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    return p


def verify_completed_job(plan, ledger_job, output_dir):
    """Return (ok, reason). ok=True means the completed job may be safely skipped."""
    jid = ledger_job["job_id"]
    if not ledger_job.get("output_hash"):
        return False, "no output_hash in ledger"
    p = ledger_job.get("output_path") or result_path(output_dir, jid)
    if not os.path.exists(p):
        return False, "output file missing"
    try:
        result = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        return False, f"output file unreadable: {e}"
    if not result.get("output_text") and result.get("output_text") != "":
        return False, "result structurally incomplete"
    if _sha(result.get("output_text", "")) != ledger_job["output_hash"]:
        return False, "output hash mismatch"
    if result.get("output_hash") != ledger_job["output_hash"]:
        return False, "result output_hash mismatch"
    item_id, role = ledger_job["benchmark_item_id"], ledger_job["model_role"]
    if result.get("prompt_hash") != plan["item_hashes"].get(item_id):
        return False, "item/prompt hash mismatch vs plan"
    if result.get("behavior_contract_hash") != plan["behavior_contract_hashes"].get(item_id):
        return False, "behavior-contract hash mismatch vs plan"
    if result.get("generation_settings_hash") != plan["generation_settings_hash"]:
        return False, "generation-settings hash mismatch vs plan"
    if result.get("model_role") != role:
        return False, "model-role mismatch vs job"
    return True, "ok"
