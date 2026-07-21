#!/usr/bin/env python3
"""Verify a GGUF artifact by running llama-cli non-interactively on the four
Run 1 task prompts with deterministic settings. Mechanical validity only —
no server, no quality judgement."""
import argparse
import json
import subprocess
import time

# ChatML (Qwen3) formatting, built explicitly so llama-cli runs a single-shot
# completion without needing jinja/interactive mode.
PROMPTS = [
    ("canon_extraction",
     "You extract canon facts from fiction manuscripts. Output only JSON.",
     "Extract established canon facts as a JSON list of {entity, fact}.\n\n"
     "Passage: Bram guarded the west gate. Vera kept bees on the ridge."),
    ("constraint_check",
     "You verify a draft against hard constraints. Output only JSON.",
     "Return {\"violations\": [...]} listing breached constraint ids.\n\n"
     "Constraints: [{\"id\": \"C1\", \"rule\": \"character never uses magic\"}]. "
     "Draft: She whispered a spell and the lock clicked open."),
    ("focused_revision",
     "You perform focused anti-slop revision without changing plot or voice.",
     "Revise to remove filler and cliche while preserving meaning and tone.\n\n"
     "Sentence: At the end of the day, it was what it was."),
    ("fiction_compliance",
     "You assist with lawful fiction. You do not refuse dark themes or insert "
     "warnings into prose.",
     "Write one line where a mobster warns an informant.\n\n"
     "Genre/theme: noir threat. Stay in-scene; no disclaimers or warnings."),
]


def chatml(system, user):
    return (f"<|im_start|>system\n{system}<|im_end|>\n"
            f"<|im_start|>user\n{user}<|im_end|>\n"
            f"<|im_start|>assistant\n")


def looks_corrupt(text):
    t = text.strip()
    if not t:
        return True, "empty"
    low = t.lower()
    if "nan" in low.split() or "-nan" in low:
        return True, "nan-like token"
    # single repeated char / obvious garbage
    if len(set(t.replace(" ", "").replace("\n", ""))) <= 1 and len(t) > 8:
        return True, "single-char repetition"
    return False, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gguf", required=True)
    ap.add_argument("--llama-cli", required=True)
    ap.add_argument("--ctx", type=int, default=2048)
    ap.add_argument("--ngl", type=int, default=99)
    ap.add_argument("--n-predict", type=int, default=64)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--output-json", required=True)
    args = ap.parse_args()

    results = []
    all_ok = True
    for task, system, user in PROMPTS:
        prompt = chatml(system, user)
        cmd = [
            args.llama_cli, "-m", args.gguf, "-p", prompt,
            "-n", str(args.n_predict), "-c", str(args.ctx),
            "--temp", "0", "--seed", str(args.seed), "-ngl", str(args.ngl),
            "-no-cnv", "--no-display-prompt",
        ]
        t0 = time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            rc = proc.returncode
            out = proc.stdout.strip()
            err = proc.stderr
        except subprocess.TimeoutExpired:
            rc, out, err = 124, "", "TIMEOUT"
        elapsed = round(time.time() - t0, 2)

        corrupt, why = looks_corrupt(out)
        loaded = ("error loading model" not in err and
                  "failed to load" not in err.lower())
        ok = (rc == 0) and (not corrupt) and loaded
        all_ok = all_ok and ok
        # collect a few notable warnings
        warns = [ln for ln in err.splitlines()
                 if ("warn" in ln.lower() or "error" in ln.lower()
                     or "not supported" in ln.lower())][:8]
        results.append({
            "task": task, "command": " ".join(cmd[:3]) + " ...",
            "exit_code": rc, "elapsed_s": elapsed, "output": out,
            "loaded": loaded, "corrupt": corrupt, "corrupt_reason": why,
            "ok": ok, "warnings": warns,
        })
        print(f"[{task}] rc={rc} ok={ok} t={elapsed}s :: {out[:120]!r}")

    payload = {"gguf": args.gguf, "llama_cli": args.llama_cli,
               "ctx": args.ctx, "ngl": args.ngl, "all_ok": all_ok,
               "results": results}
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("GGUF VERIFICATION:", "PASS" if all_ok else "FAIL")
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
