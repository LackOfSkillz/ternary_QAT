"""Workers + deterministic stub generation (Dispatch 23, Workstream B).

A worker leases a job, generates, and returns a normalized result. ``StubWorker`` is a
deterministic test worker: its output is a pure function of (item prompt, model role,
generation settings), so parallel and sequential runs of the same plan produce identical
normalized results — the invariant the orchestration tests assert (never a false promise of
bit-identical real inference).
"""
import hashlib


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class StubWorker:
    endpoint_type = "test_stub"

    def __init__(self, worker_id, host_id, roles, endpoint_id="stub"):
        self.worker_id = worker_id
        self.host_id = host_id
        self.endpoint_id = endpoint_id
        self.roles = list(roles)

    def can_handle(self, role):
        return role in self.roles

    def generate(self, plan, item_id, role):
        item = plan["items"][item_id]
        prompt = item["prompt"]
        settings_hash = plan["generation_settings_hash"]
        # deterministic pseudo-output keyed by (prompt, role, settings) — NOT identity-leaking
        seed = _sha(f"{prompt}|{role}|{settings_hash}")
        text = f"[stub-output {seed[:12]}] " + " ".join(prompt.split()[:8])
        return {
            "output_text": text,
            "output_hash": _sha(text),
            "input_tokens": len(prompt.split()),
            "output_tokens": len(text.split()),
            "finish_reason": "stop",
            "hit_token_cap": False,
        }


def normalized_result(plan, run_id, job_id, item_id, role, gen, worker, execution_mode,
                      started_at, completed_at, result_id=None):
    """Assemble a normalized-generation-result record (identity fields present here; stripped
    before a reviewer packet is built)."""
    d = plan["model_descriptors"][role]
    return {
        "schema": "normalized-generation-result",
        "result_id": result_id or f"res::{job_id}",
        "run_id": run_id, "job_id": job_id, "plan_id": plan["plan_id"],
        "benchmark_item_id": item_id, "model_role": role,
        "model_identity_ref": d.get("identity", role), "model_revision": d.get("revision"),
        "checkpoint_ref": d.get("checkpoint"),
        "prompt_hash": plan["item_hashes"][item_id],
        "behavior_contract_hash": plan["behavior_contract_hashes"][item_id],
        "generation_settings_hash": plan["generation_settings_hash"],
        "execution_mode": execution_mode, "worker_id": worker.worker_id,
        "host_id": worker.host_id, "started_at": started_at, "completed_at": completed_at,
        "input_tokens": gen["input_tokens"], "output_tokens": gen["output_tokens"],
        "finish_reason": gen["finish_reason"], "hit_token_cap": gen["hit_token_cap"],
        "output_text": gen["output_text"], "output_hash": gen["output_hash"],
        "backend_metadata": {"endpoint_type": worker.endpoint_type},
        "status": "completed",
    }


STRIP_FOR_REVIEW = ("model_role", "model_identity_ref", "model_revision", "checkpoint_ref",
                    "host_id", "execution_mode", "worker_id", "started_at", "completed_at",
                    "backend_metadata")


def to_anonymous(result, candidate_label):
    """Strip identity/timing/backend to make a blind anonymous-output record."""
    return {
        "output_id": f"anon::{result['job_id']}",
        "item_id": result["benchmark_item_id"],
        "candidate_label": candidate_label,
        "output_text": result["output_text"],
        "hit_token_cap": result["hit_token_cap"],
    }
