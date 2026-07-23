"""Dispatch 28B — generation integrity gate. Verifies the 100 primary outputs against the frozen
generation plan + prompt manifest: counts, missing/duplicate task-arm pairs, prompt-hash and
model-revision consistency, identical decoding settings, token-cap and reasoning-trace scan, and
technical retries/failures. Writes generation-integrity.{json,md}. Outcome gates scoring.
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(
    HERE, "..", "runs", "linewright-prompt-execution-v1")
RUN = os.path.abspath(RUN)
ARM_DIR = {"P0-Realistic": "p0-realistic", "P0-Maximal": "p0-maximal",
           "P1-Contract": "p1-contract", "P3-Ideal": "p3-ideal"}


def main():
    plan = json.load(open(os.path.join(RUN, "generation-plan.json"), encoding="utf-8"))
    man = {(r["task_id"], r["arm"]): r for r in
           json.load(open(os.path.join(HERE, "prompt-arm-manifest.json"), encoding="utf-8"))["prompts"]}

    outs = {}
    dup = 0
    for arm, d in ARM_DIR.items():
        dd = os.path.join(RUN, "raw-results", d)
        if not os.path.isdir(dd):
            continue
        for fn in os.listdir(dd):
            if not fn.endswith(".json"):
                continue
            r = json.load(open(os.path.join(dd, fn), encoding="utf-8"))
            k = (r["task_id"], arm)
            if k in outs:
                dup += 1
            outs[k] = r

    expected = {(r["task_id"], r["arm"]) for r in plan["records"]}
    got = set(outs)
    missing = sorted(expected - got)
    phash_mismatch = mrev_mismatch = setting_mismatch = caps = traces = retries = fails = 0
    malformed = 0
    for k, r in outs.items():
        if r.get("generation_status") == "technical_failure":
            fails += 1
            continue
        for field in ("output_text", "output_sha256"):
            if field not in r:
                malformed += 1
        if man.get(k, {}).get("prompt_sha256") != r.get("prompt_sha256"):
            phash_mismatch += 1
        if r.get("token_cap_hit"):
            caps += 1
        if r.get("reasoning_trace_detected"):
            traces += 1
        retries += r.get("technical_retry_count", 0) or 0
    # model revision / settings come from env manifest (single run, one config)
    env = json.load(open(os.path.join(RUN, "environment-manifest.json"), encoding="utf-8"))
    if env.get("model_revision") != plan["model_revision"]:
        mrev_mismatch += 1
    if not (env.get("thinking") == "disabled" and env.get("decoding") == "greedy" and env.get("seed") == plan["seed"]):
        setting_mismatch += 1

    comp_dir = os.path.join(RUN, "comprehension-results")
    comp = len([f for f in os.listdir(comp_dir) if f.endswith(".json")]) if os.path.isdir(comp_dir) else 0

    integ = {
        "dispatch": "28B", "expected_outputs": 100, "actual_outputs": len(outs),
        "complete_outputs": sum(1 for r in outs.values() if r.get("generation_status", "").startswith("complete")),
        "comprehension_outputs": comp,
        "missing_outputs": len(missing), "missing_list": missing, "duplicate_outputs": dup,
        "malformed_records": malformed, "prompt_hash_mismatches": phash_mismatch,
        "model_revision_mismatches": mrev_mismatch, "generation_setting_mismatches": setting_mismatch,
        "token_cap_hits": caps, "reasoning_trace_count": traces,
        "technical_retries": retries, "technical_failures": fails,
        "arm_counts": dict(Counter(a for (_, a) in outs)),
        "environment": {k: env.get(k) for k in ("gpu", "torch", "transformers", "model_revision",
                                                "thinking", "decoding", "seed")},
    }
    ok = (integ["actual_outputs"] == 100 and integ["missing_outputs"] == 0 and integ["duplicate_outputs"] == 0
          and integ["malformed_records"] == 0 and integ["prompt_hash_mismatches"] == 0
          and integ["model_revision_mismatches"] == 0 and integ["generation_setting_mismatches"] == 0
          and integ["technical_failures"] <= 5)
    if not ok:
        integ["outcome"] = "invalid_generation_rerun_required"
    elif integ["technical_retries"] > 0:
        integ["outcome"] = "valid_with_documented_exact_retries"
    else:
        integ["outcome"] = "valid"

    json.dump(integ, open(os.path.join(RUN, "generation-integrity.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    md = ["# Generation integrity — Prompt-Execution v1 (Dispatch 28B)", "",
          f"- Outcome: **{integ['outcome']}**",
          f"- Outputs: {integ['actual_outputs']}/100 (complete {integ['complete_outputs']}); comprehension {comp}",
          f"- Missing: {integ['missing_outputs']} · duplicates: {integ['duplicate_outputs']} · malformed: {integ['malformed_records']}",
          f"- Prompt-hash mismatches: {integ['prompt_hash_mismatches']} · model-rev mismatches: {integ['model_revision_mismatches']} · setting mismatches: {integ['generation_setting_mismatches']}",
          f"- Token-cap hits: {integ['token_cap_hits']} · reasoning traces: {integ['reasoning_trace_count']}",
          f"- Technical retries: {integ['technical_retries']} · failures: {integ['technical_failures']}",
          f"- Env: {integ['environment']}"]
    open(os.path.join(RUN, "generation-integrity.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md))
    print(json.dumps({"outcome": integ["outcome"], "actual": integ["actual_outputs"], "missing": integ["missing_outputs"],
                      "dup": integ["duplicate_outputs"], "phash_mm": integ["prompt_hash_mismatches"],
                      "caps": caps, "traces": traces, "fails": fails}, indent=1))
    return integ


if __name__ == "__main__":
    main()
