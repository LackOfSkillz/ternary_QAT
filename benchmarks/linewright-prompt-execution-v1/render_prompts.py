"""Dispatch 28A — render the prompt arms from the FROZEN task layer (read-only).

Arms: P0-Realistic (casual, may omit requirements), P0-Maximal (exhaustive NL, every requirement),
P1-Contract (the SAME information as P0-Maximal in a canonical research contract), P3-Ideal (a
hand-built theoretical ceiling on a frozen 10-task subset; NOT product-generated). P3-Compiled is
deferred. P0-Maximal and P1-Contract are rendered from ONE shared information inventory so they are
information-equivalent by construction; the equivalence validator confirms it independently.

Emits prompts/<arm>/<task_id>.txt, prompt-arm-manifest.json, prompt-plan.json, p3-ideal-subset.json.
generation_authorized is False on every record — this dispatch renders and freezes only.
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_VERSION = 1

SYS = ("You are a careful fiction-writing assistant working inside an author's private studio. "
       "You revise and draft prose on request. You follow the author's instructions exactly: you "
       "make the changes asked for, you preserve anything marked to keep, and you do not rewrite, "
       "expand, or embellish beyond what was requested.")

MODE = {
    "multi_constraint_focused_revision": ("focused_revision",
        "Revise the passage: make every required change and change nothing else."),
    "protected_text_revision": ("protected_revision",
        "Make only the required correction and preserve all protected text verbatim."),
    "no_change_judgment": ("judgment",
        "Decide whether any change is genuinely needed; if the passage is already correct, return it unchanged."),
    "canon_continuation": ("continuation",
        "Continue the passage in a way that is consistent with the canon."),
    "voice_preserving_revision": ("voice_preserving_revision",
        "Make the required correction while preserving the author's distinctive voice exactly."),
    "constraint_bound_scene": ("scene_draft",
        "Draft the scene, honouring every hard constraint."),
    "structured_protocol": ("extraction",
        "Produce exactly the requested structured output and nothing else."),
}
SHAPE_TEXT = {"prose": "Return the result as prose.",
              "json": "Return the result as a single JSON object and nothing else.",
              "list": "Return the result as a numbered list, one item per line."}

# frozen P3-Ideal subset: focused_revision x4, protected_text x2, canon x1, voice x1, no_change x1, scene x1
P3_SUBSET = ["fr-01", "fr-04", "fr-07", "fr-09", "pt-01", "pt-03", "cn-01", "vp-02", "nc-01", "sc-01"]


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _task_sha(task):
    return hashlib.sha256(json.dumps(task, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def inventory(task):
    """The shared information inventory rendered identically into P0-Maximal and P1-Contract."""
    gt = task["evaluation_ground_truth"]
    ci = task["compiler_inputs"]
    mode, authority = MODE[task["task_family"]]
    ctx = []
    if ci.get("project_context"):
        ctx.append(f"project: {ci['project_context']}")
    if ci.get("scene_context"):
        ctx.append(f"scene: {ci['scene_context']}")
    for c in ci.get("canon_records", []):
        ctx.append(f"canon: {c}")
    return {
        "task_authority": authority,
        "mode": mode,
        "required_changes": [r["desc"] for r in gt["required_changes"]],
        "protected_elements": [p["text"] for p in gt["protected_elements"]],
        "forbidden_changes": [f["desc"] for f in gt["forbidden_changes"]],
        "authorized_scope": [a["desc"] for a in gt["authorized_spans"]],
        "context": ctx,
        "output_contract": gt["expected_output_shape"],
    }


def render_p0_maximal(task, inv):
    p = [SYS, ""]
    if task["source_passage"]:
        p += ["Here is the passage:", "", task["source_passage"], ""]
    p.append(inv["task_authority"])
    if inv["required_changes"]:
        p.append("")
        p.append("Make all of the following changes:")
        p += [f"  {i}. {d}" for i, d in enumerate(inv["required_changes"], 1)]
    if inv["protected_elements"]:
        p.append("")
        p.append("Keep the following exactly as written, word for word:")
        p += [f"  - {t}" for t in inv["protected_elements"]]
    if inv["forbidden_changes"]:
        p.append("")
        p.append("Do not do any of the following:")
        p += [f"  - {d}" for d in inv["forbidden_changes"]]
    if inv["authorized_scope"]:
        p.append("")
        p.append("You may only change: " + "; ".join(inv["authorized_scope"]) + ".")
    if inv["context"]:
        p.append("")
        p.append("Context you should respect:")
        p += [f"  - {c}" for c in inv["context"]]
    p.append("")
    p.append(SHAPE_TEXT[inv["output_contract"]])
    return "\n".join(p).strip()


def render_p1_contract(task, inv):
    lines = [SYS, "", "```yaml", "linewright_contract:", "  protocol: lw-research-contract",
             "  schema_version: 1", "  task:", f"    mode: {inv['mode']}",
             f"    authority: {json.dumps(inv['task_authority'])}"]
    if task["source_passage"]:
        lines += ["  source:", f"    passage: {json.dumps(task['source_passage'])}"]
    lines.append("  required_changes:")
    lines += [f"    - {json.dumps(d)}" for d in inv["required_changes"]] or ["    []"]
    lines.append("  protected_elements:")
    lines += [f"    - {json.dumps(t)}" for t in inv["protected_elements"]] or ["    []"]
    lines.append("  forbidden_changes:")
    lines += [f"    - {json.dumps(d)}" for d in inv["forbidden_changes"]] or ["    []"]
    lines.append("  authorized_scope:")
    lines += [f"    - {json.dumps(d)}" for d in inv["authorized_scope"]] or ["    []"]
    lines.append("  context:")
    lines += [f"    - {json.dumps(c)}" for c in inv["context"]] or ["    []"]
    lines.append(f"  output_contract: {inv['output_contract']}")
    lines.append("```")
    return "\n".join(lines).strip()


def render_p0_realistic(task):
    p = [SYS, "", task["compiler_inputs"]["user_request"]]
    if task["source_passage"]:
        p += ["", task["source_passage"]]
    return "\n".join(p).strip()


def omission_inventory(task, inv):
    """Which requirements the realistic request states / implies / omits — a product finding."""
    req = task["compiler_inputs"]["user_request"].lower()
    stated, implied, not_stated = [], [], []
    items = ([("required", d) for d in inv["required_changes"]]
             + [("protected", t) for t in inv["protected_elements"]]
             + [("forbidden", d) for d in inv["forbidden_changes"]]
             + [("output", SHAPE_TEXT[inv["output_contract"]])])
    for kind, d in items:
        words = [w for w in d.lower().replace("'", " ").split() if len(w) > 4][:6]
        hits = sum(1 for w in words if w in req)
        if hits >= 2:
            stated.append(f"{kind}: {d}")
        elif hits == 1:
            implied.append(f"{kind}: {d}")
        else:
            not_stated.append(f"{kind}: {d}")
    return {"requirements_explicitly_stated": stated, "requirements_implicitly_stated": implied,
            "requirements_not_stated": not_stated}


def render_p3_ideal(task, inv):
    """Hand-built theoretical ceiling: the contract PLUS the full compiled context an ideal product
    could retrieve (voice, character state, invention budget, all canon). Never includes ground
    truth or machine checks."""
    ci = task["compiler_inputs"]
    lines = [SYS, "", "```yaml", "linewright_packet:", "  protocol: lw-ideal-packet",
             "  schema_version: 1", "  note: theoretical ceiling; not produced by the product compiler",
             "  task:", f"    mode: {inv['mode']}", f"    authority: {json.dumps(inv['task_authority'])}"]
    if task["source_passage"]:
        lines += ["  source:", f"    passage: {json.dumps(task['source_passage'])}"]
    lines.append("  required_changes:")
    lines += [f"    - {json.dumps(d)}" for d in inv["required_changes"]] or ["    []"]
    lines.append("  protected_elements:")
    lines += [f"    - {json.dumps(t)}" for t in inv["protected_elements"]] or ["    []"]
    lines.append("  forbidden_changes:")
    lines += [f"    - {json.dumps(d)}" for d in inv["forbidden_changes"]] or ["    []"]
    lines.append("  authorized_scope:")
    lines += [f"    - {json.dumps(d)}" for d in inv["authorized_scope"]] or ["    []"]
    lines.append("  compiled_context:")
    if ci.get("project_context"):
        lines.append(f"    project: {json.dumps(ci['project_context'])}")
    if ci.get("scene_context"):
        lines.append(f"    scene: {json.dumps(ci['scene_context'])}")
    if ci.get("character_state"):
        lines.append(f"    character_state: {json.dumps(ci['character_state'])}")
    if ci.get("voice_profile"):
        lines.append(f"    voice_profile: {json.dumps(ci['voice_profile'])}")
    if ci.get("canon_records"):
        lines.append("    canon:")
        lines += [f"      - {json.dumps(c)}" for c in ci["canon_records"]]
    lines.append("  constraint_hierarchy:")
    lines += ["    1: preserve protected elements verbatim",
              "    2: make every required change",
              "    3: obey all forbidden-change limits",
              "    4: honour the output contract",
              "    5: preserve manuscript quality and voice"]
    lines.append(f"  invention_budget: {json.dumps(ci.get('invention_budget', 'none'))}")
    lines.append(f"  output_contract: {inv['output_contract']}")
    lines.append("```")
    return "\n".join(lines).strip()


def main():
    tasks = [json.loads(l) for l in open(os.path.join(HERE, "task-manifest.jsonl"), encoding="utf-8") if l.strip()]
    records = []

    def emit(task, arm, text, inv, is_ideal=False, extra=None):
        rec = {
            "task_id": task["task_id"], "arm": arm, "prompt_text": text,
            "prompt_sha256": _sha(text), "source_task_sha256": _task_sha(task),
            "information_inventory": inv, "instruction_position": task["diagnostics"]["instruction_position"],
            "schema_version": SCHEMA_VERSION, "is_product_compiled": False, "is_ideal_packet": is_ideal,
            "generation_authorized": False,
        }
        if extra:
            rec.update(extra)
        records.append(rec)
        d = os.path.join(HERE, "prompts", arm.lower().replace("-", "_"))
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, task["task_id"] + ".txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    for task in tasks:
        inv = inventory(task)
        emit(task, "P0-Realistic", render_p0_realistic(task), inv,
             extra={"omission_inventory": omission_inventory(task, inv)})
        emit(task, "P0-Maximal", render_p0_maximal(task, inv), inv)
        emit(task, "P1-Contract", render_p1_contract(task, inv), inv)
    by_id = {t["task_id"]: t for t in tasks}
    for tid in P3_SUBSET:
        task = by_id[tid]
        inv = inventory(task)
        emit(task, "P3-Ideal", render_p3_ideal(task, inv), inv, is_ideal=True)

    # manifests
    with open(os.path.join(HERE, "prompt-arm-manifest.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"schema_version": SCHEMA_VERSION, "prompts": records}, fh, ensure_ascii=False, indent=1)
    from collections import Counter
    counts = Counter(r["arm"] for r in records)
    plan = {
        "instrument": "linewright-prompt-execution-v1", "dispatch": "28A",
        "prompt_counts": {
            "p0_realistic": counts["P0-Realistic"], "p0_maximal": counts["P0-Maximal"],
            "p1_contract": counts["P1-Contract"], "p3_ideal": counts["P3-Ideal"],
            "p3_compiled": 0, "total": len(records)},
        "arms_by_task": {t["task_id"]: [r["arm"] for r in records if r["task_id"] == t["task_id"]]
                         for t in tasks},
        "generation_authorized": False,
    }
    with open(os.path.join(HERE, "prompt-plan.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(plan, fh, ensure_ascii=False, indent=1)

    from collections import Counter as Ctr
    fam_of = {t["task_id"]: t["task_family"] for t in tasks}
    sub_dist = Ctr(fam_of[t] for t in P3_SUBSET)
    p3 = {
        "p3_ideal_subset": {"focused_revision": sub_dist["multi_constraint_focused_revision"],
                            "protected_text": sub_dist["protected_text_revision"],
                            "canon": sub_dist["canon_continuation"], "voice": sub_dist["voice_preserving_revision"],
                            "no_change": sub_dist["no_change_judgment"],
                            "scene_drafting": sub_dist["constraint_bound_scene"]},
        "tasks": P3_SUBSET,
        "represents_current_product_compiler": False,
        "purpose": "theoretical_packet_ceiling",
    }
    with open(os.path.join(HERE, "p3-ideal-subset.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(p3, fh, ensure_ascii=False, indent=1)

    print(json.dumps({"prompt_counts": plan["prompt_counts"], "p3_subset_distribution": p3["p3_ideal_subset"]},
                     indent=1))


if __name__ == "__main__":
    main()
