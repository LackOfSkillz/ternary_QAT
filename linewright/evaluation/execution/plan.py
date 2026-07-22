"""Frozen generation plan (Dispatch 23, Workstream B3).

A plan is created and HASHED before generation. The hash covers the immutable body (items,
contracts, model descriptors/revisions, generation settings, seeds, token limits) and
EXCLUDES timing, plan_id, plan_hash, and the output directory. Parallel and sequential runs
of the same plan produce structurally identical results. Mutating benchmark semantics
requires a NEW plan_id + plan_hash + run_id. Secrets are never serialized into a plan.
"""
import hashlib
import json

# execution_mode + scheduling_policy are HOW a plan is run (parallel vs sequential), not
# benchmark semantics — they are excluded so the SAME plan run either way shares a plan_hash.
HASH_EXCLUDES = ("created_at", "plan_id", "plan_hash", "output_directory",
                 "execution_mode", "scheduling_policy")
EXECUTION_MODES = ("parallel_multi_host", "parallel_single_host",
                   "sequential_single_host", "sequential_multi_host")


def _h(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def create_plan(*, battery_version, battery_profile, execution_mode, scheduling_policy,
                items, model_descriptors, generation_settings, seeds, max_new_tokens,
                retry_policy_id, output_directory, stop_sequences=None, created_at="unset",
                plan_id="plan-unset"):
    """``items`` = [{item_id, prompt, behavior_contract, model_roles?}]; ``model_descriptors``
    = {role: {identity, checkpoint, revision, tokenizer_revision, endpoint_id, chat_template,
    system_prompt}}. Secrets must NOT appear in model_descriptors."""
    assert execution_mode in EXECUTION_MODES, execution_mode
    for role, d in model_descriptors.items():
        for k in d:
            assert "api_key" not in k.lower() and "secret" not in k.lower(), \
                f"secret-like field {k!r} must not be serialized in a plan"

    item_ids = [it["item_id"] for it in items]
    item_hashes = {it["item_id"]: _h(it["prompt"]) for it in items}
    contract_hashes = {it["item_id"]: _h(it.get("behavior_contract", {})) for it in items}
    gen_hash = _h(generation_settings)
    roles = sorted(model_descriptors)

    body = {
        "battery_version": battery_version, "battery_profile": battery_profile,
        "execution_mode": execution_mode, "scheduling_policy": scheduling_policy,
        "item_ids": sorted(item_ids), "item_hashes": item_hashes,
        "behavior_contract_hashes": contract_hashes,
        "model_roles": roles,
        "model_descriptors": model_descriptors,
        "model_revisions": {r: model_descriptors[r].get("revision") for r in roles},
        "tokenizer_revisions": {r: model_descriptors[r].get("tokenizer_revision") for r in roles},
        "chat_templates": {r: model_descriptors[r].get("chat_template") for r in roles},
        "system_prompts": {r: model_descriptors[r].get("system_prompt") for r in roles},
        "generation_settings": generation_settings,
        "generation_settings_hash": gen_hash,
        "seeds": seeds, "max_new_tokens": max_new_tokens,
        "stop_sequences": stop_sequences or [], "retry_policy": retry_policy_id,
    }
    plan = dict(body)
    plan["plan_hash"] = _h({k: v for k, v in body.items() if k not in HASH_EXCLUDES})
    plan["plan_id"] = plan_id
    plan["created_at"] = created_at
    plan["output_directory"] = output_directory
    # store the item prompts/contracts alongside (not part of the hash body beyond their hash)
    plan["items"] = {it["item_id"]: {"prompt": it["prompt"],
                                     "behavior_contract": it.get("behavior_contract", {}),
                                     "model_roles": it.get("model_roles", roles)}
                     for it in items}
    return plan


def plan_body(plan):
    return {k: plan[k] for k in plan if k not in HASH_EXCLUDES and k != "items"}


def verify_plan_hash(plan):
    """True if the plan's stored hash matches a recompute over its immutable body."""
    return plan.get("plan_hash") == _h(plan_body(plan))


def job_tuples(plan):
    """Enumerate (item_id, model_role) jobs for the plan (one job per item x role)."""
    out = []
    for item_id in plan["item_ids"]:
        for role in plan["items"][item_id].get("model_roles", plan["model_roles"]):
            out.append((item_id, role))
    return out
