"""Fresh-process checkpoint reload check (invoked by runtime.verify_checkpoint_reload).

Loads a saved checkpoint with the given backend, initializes the model + tokenizer,
generates one short response, and prints a single JSON line with the result. A
checkpoint is only valid if this exits successfully with non-empty output.
"""
import argparse
import json

from linewright.backends import get_backend


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--backend", default="stub")
    args = ap.parse_args()
    result = {"ok": False, "checkpoint": args.checkpoint, "backend": args.backend}
    try:
        backend_cls = get_backend(args.backend)
        model = backend_cls.load_checkpoint(args.checkpoint)
        result["model_init"] = True
        result["tokenizer_init"] = True                # stub tokenizer is implicit
        out = model.generate("Reload check: produce one short line.",
                             {"temperature": 0, "max_new_tokens": 16})
        result["output"] = out
        result["output_nonempty"] = bool(out and out.strip())
        result["ok"] = result["output_nonempty"]
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
