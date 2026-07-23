"""Dispatch 28B — build the generation plan from the FROZEN prompt manifest (read-only).

Emits benchmarks/runs/linewright-prompt-execution-v1/generation-plan.json: one record per prompt
(100) plus 6 comprehension probes (stored + generated separately, NOT part of the 100-output means).
Same per-task output cap across all arms of a task; P3-Ideal gets no larger allowance. This dispatch
newly authorizes generation — records carry generation_authorized True, but the FROZEN prompt files
are never modified.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
RUN = os.path.join(REPO, "benchmarks", "runs", "linewright-prompt-execution-v1")

MODEL_ID = "Qwen/Qwen3-8B"
MODEL_REV = "b968826d9c46dd6066d109eabc6255188de91218"
SEED = 20260723

CAPS = {"multi_constraint_focused_revision": 768, "protected_text_revision": 512,
        "no_change_judgment": 512, "canon_continuation": 512, "voice_preserving_revision": 512,
        "constraint_bound_scene": 768, "structured_protocol": 256}
ARM_DIR = {"P0-Realistic": "p0-realistic", "P0-Maximal": "p0-maximal",
           "P1-Contract": "p1-contract", "P3-Ideal": "p3-ideal"}

COMP_SYS = ("You are analyzing a fiction-writing request to check your understanding. Do NOT perform "
            "the task or revise any text. Only report what the request asks for.")
COMP_INSTR = ("\n\nDo not perform the task. Answer with a single JSON object and nothing else, with "
              "exactly these keys: \"required_change_count\" (integer — how many distinct changes are "
              "required), \"protected_element_count\" (integer — how many pieces of text must be kept "
              "verbatim), \"forbidden_operation_count\" (integer — how many things you are told not to "
              "do), \"output_contract\" (string — the required output format: prose, json, or list).")


def main():
    man = json.load(open(os.path.join(HERE, "prompt-arm-manifest.json"), encoding="utf-8"))["prompts"]
    tasks = {json.loads(l)["task_id"]: json.loads(l)
             for l in open(os.path.join(HERE, "task-manifest.jsonl"), encoding="utf-8") if l.strip()}
    p1_by_task = {r["task_id"]: r for r in man if r["arm"] == "P1-Contract"}

    records = []
    for r in man:
        fam = tasks[r["task_id"]]["task_family"]
        cap = CAPS[fam]
        records.append({
            "task_id": r["task_id"], "task_family": fam, "arm": r["arm"],
            "prompt_sha256": r["prompt_sha256"], "source_task_sha256": r["source_task_sha256"],
            "model_id": MODEL_ID, "model_revision": MODEL_REV, "thinking": "disabled",
            "decoding": "greedy", "seed": SEED, "max_new_tokens": cap,
            "expected_output_path": f"raw-results/{ARM_DIR[r['arm']]}/{r['task_id']}.json",
        })

    # comprehension probes: present the P1-Contract of each probed task, ask to enumerate (not execute)
    comp = []
    for tid, t in tasks.items():
        cp = t.get("comprehension_probe", {})
        if not cp.get("enabled"):
            continue
        contract_body = p1_by_task[tid]["prompt_text"]
        # strip the leading system paragraph, keep the yaml contract block for analysis
        idx = contract_body.find("```yaml")
        body = contract_body[idx:] if idx != -1 else contract_body
        comp_prompt = COMP_SYS + "\n\n" + body + COMP_INSTR
        comp.append({
            "task_id": tid, "task_family": t["task_family"], "kind": "comprehension_probe",
            "prompt_text": comp_prompt, "model_id": MODEL_ID, "model_revision": MODEL_REV,
            "thinking": "disabled", "decoding": "greedy", "seed": SEED, "max_new_tokens": 256,
            "expected_output_path": f"comprehension-results/{tid}.json",
            "expected": {"required_change_count": cp["expected_required_changes"],
                         "protected_element_count": cp["expected_protected_elements"],
                         "forbidden_operation_count": cp["expected_forbidden_operations"],
                         "output_contract": cp["expected_output_contract"]},
        })

    from collections import Counter
    arms = Counter(r["arm"] for r in records)
    plan = {
        "instrument": "linewright-prompt-execution-v1", "dispatch": "28B",
        "model_id": MODEL_ID, "model_revision": MODEL_REV, "thinking": "disabled",
        "decoding": "greedy", "temperature": 0.0, "do_sample": False, "seed": SEED,
        "generation_authorized": True,
        "expected_records": 100, "actual_records": len(records),
        "duplicate_task_arm_pairs": len(records) - len({(r["task_id"], r["arm"]) for r in records}),
        "missing_task_arm_pairs": 0, "p3_compiled_records": 0,
        "arm_counts": dict(arms), "task_caps": CAPS,
        "records": records, "comprehension_records": comp,
        "comprehension_count": len(comp),
    }
    # missing pair check: each of 30 tasks must have the 3 main arms; 10 have P3-Ideal
    main_pairs = {(r["task_id"], r["arm"]) for r in records}
    missing = 0
    for tid in tasks:
        for arm in ("P0-Realistic", "P0-Maximal", "P1-Contract"):
            if (tid, arm) not in main_pairs:
                missing += 1
    plan["missing_task_arm_pairs"] = missing

    os.makedirs(RUN, exist_ok=True)
    with open(os.path.join(RUN, "generation-plan.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(plan, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"records": len(records), "arm_counts": dict(arms),
                      "comprehension": len(comp), "duplicates": plan["duplicate_task_arm_pairs"],
                      "missing": plan["missing_task_arm_pairs"], "p3_compiled": 0}, indent=1))


if __name__ == "__main__":
    main()
