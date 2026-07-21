"""LineWright training-execution harness.

Guarded, deterministic entry points for the Dataset A smoke pipeline:
  python -m linewright.train   --config <cfg> [--validate-only|--dry-run|--max-steps-override N]
  python -m linewright.eval    --harness <harness> --target <base|lora|ternary-qat> --out <json>
  python -m linewright.compare --base <j> --lora <j> --ternary-qat <j> --out <md>

This dispatch (18A) runs on CPU with a deterministic STUB backend so the whole
pipeline (config validation, path guard, stop conditions, integrity inventory,
run manifests, reproducibility gate, one-step rehearsal) can be exercised WITHOUT
the 4B checkpoint or CUDA. On the GX10 run001 image, select backend: hf to run the
real model. No real Dataset A gradient training is performed here.
"""
__version__ = "0.1.0"
