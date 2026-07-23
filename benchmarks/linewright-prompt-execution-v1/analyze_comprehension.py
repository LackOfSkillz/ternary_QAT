"""Dispatch 28B — comprehension-vs-execution analysis for the 6 frozen probes.

Parses each probe's JSON answer (required_change_count, protected_element_count,
forbidden_operation_count, output_contract), compares to the expected values, and classifies each
probed task on the comprehension x execution grid using the P1-Contract EXECUTION result (the
structured arm the probe mirrors). Probes are NOT part of the 100-output means.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(
    HERE, "..", "runs", "linewright-prompt-execution-v1")
RUN = os.path.abspath(RUN)


def parse_answer(text):
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def comprehension_ok(ans, exp):
    if not ans:
        return False
    def eqi(a, b):
        try:
            return int(a) == int(b)
        except Exception:
            return False
    return (eqi(ans.get("required_change_count"), exp["required_change_count"])
            and eqi(ans.get("protected_element_count"), exp["protected_element_count"])
            and eqi(ans.get("forbidden_operation_count"), exp["forbidden_operation_count"])
            and str(ans.get("output_contract", "")).lower().strip() == str(exp["output_contract"]).lower().strip())


def main():
    item = json.load(open(os.path.join(RUN, "item-level-results.json"), encoding="utf-8"))
    comp_dir = os.path.join(RUN, "comprehension-normalized")
    if not os.path.isdir(comp_dir):
        comp_dir = os.path.join(RUN, "comprehension-results")
    rows, grid = [], {"pass_pass": 0, "fail_fail": 0, "pass_fail": 0, "fail_pass": 0}
    for fn in sorted(os.listdir(comp_dir)):
        if not fn.endswith(".json"):
            continue
        r = json.load(open(os.path.join(comp_dir, fn), encoding="utf-8"))
        tid = r["task_id"]
        ans = parse_answer(r.get("normalized_text", r.get("output_text", "")))
        comp_pass = comprehension_ok(ans, r["expected"])
        exec_item = item.get(f"{tid}::P1-Contract")
        exec_pass = bool(exec_item and exec_item["clean_execution"])
        cell = ("pass_pass" if comp_pass and exec_pass else
                "fail_fail" if not comp_pass and not exec_pass else
                "pass_fail" if comp_pass and not exec_pass else "fail_pass")
        grid[cell] += 1
        rows.append({"task_id": tid, "comprehension_pass": comp_pass, "execution_pass_p1": exec_pass,
                     "cell": cell, "answer": ans, "expected": r["expected"]})

    interp = []
    if grid["pass_fail"]:
        interp.append(f"{grid['pass_fail']} task(s) understood but not executed -> execution-discipline failure")
    if grid["fail_fail"]:
        interp.append(f"{grid['fail_fail']} task(s) both failed -> representation/salience failure")
    if grid["pass_pass"]:
        interp.append(f"{grid['pass_pass']} task(s) understood and executed")
    if grid["fail_pass"]:
        interp.append(f"{grid['fail_pass']} task(s) executed despite mis-stating the contract -> possible accidental success")
    out = {"dispatch": "28B", "probes": len(rows), "grid": grid,
           "interpretation": "; ".join(interp) or "no probes scored", "rows": rows}
    json.dump(out, open(os.path.join(RUN, "comprehension-execution-analysis.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    md = ["# Comprehension vs execution (Dispatch 28B)", "",
          f"- Probes: {len(rows)}", f"- Grid: {grid}", f"- Interpretation: {out['interpretation']}", "",
          "| task | comprehension | execution (P1) | cell |", "|---|---|---|---|"]
    md += [f"| {r['task_id']} | {r['comprehension_pass']} | {r['execution_pass_p1']} | {r['cell']} |" for r in rows]
    open(os.path.join(RUN, "comprehension-execution-analysis.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md))
    print(json.dumps(out["grid"], indent=1))
    return out


if __name__ == "__main__":
    main()
