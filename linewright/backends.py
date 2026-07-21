"""Model backends.

StubBackend: a deterministic, CPU-only stand-in used to rehearse the whole pipeline
without the 4B checkpoint or CUDA. Its generate() is a pure function of the prompt
and adapter state (stable hash, no RNG), so two evaluation runs produce byte-
identical output -> exact_match reproducibility. It does NOT approximate the real
model's quality; it exercises load/generate/save/reload plumbing only.

HFBackend: a placeholder for the real transformers model on the GX10 run001 image;
importing transformers is deferred so the stub path runs on a plain CPU host.
"""
import hashlib
import json
import os


def _stable_tag(*parts):
    h = hashlib.sha256("\x1f".join(str(p) for p in parts).encode("utf-8")).hexdigest()
    return h[:16]


class StubBackend:
    kind = "stub"

    def __init__(self, adapter_tag="base", step=0, seed=0):
        self.adapter_tag = adapter_tag
        self.step = int(step)
        self.seed = int(seed)

    @classmethod
    def from_config(cls, cfg, target="base"):
        seed = cfg.get("reproducibility", {}).get("seed", 0)
        return cls(adapter_tag=target, step=0, seed=seed)

    def generate(self, prompt, gen=None):
        """Deterministic canned output; pure function of (prompt, adapter, seed)."""
        gen = gen or {}
        tag = _stable_tag(prompt, self.adapter_tag, self.step, self.seed,
                          gen.get("temperature", 0), gen.get("max_new_tokens", 0))
        # a fixed, deterministic response; not valid structured output on purpose
        return f"[stub:{self.adapter_tag}:{tag}] deterministic placeholder response."

    def train_step(self, step, inject=None):
        """Return (loss, grad_norm) for a synthetic step. Deterministic. `inject`
        forces a failure value to exercise the stop conditions."""
        if inject == "nan_loss":
            return float("nan"), 0.5
        if inject == "inf_loss":
            return float("inf"), 0.5
        if inject == "nan_grad":
            return 0.5, float("nan")
        if inject == "inf_grad":
            return 0.5, float("inf")
        if inject == "explode_grad":
            return 0.5, 250.0
        loss = round(1.0 / (step + 1), 6)          # smooth, deterministic, finite
        grad_norm = round(0.5 + 0.1 / (step + 1), 6)
        self.step = step
        return loss, grad_norm

    def save_checkpoint(self, path, writer=None):
        target = writer.resolve(path) if writer else os.path.abspath(path)
        os.makedirs(target, exist_ok=True)
        meta = {"backend": "stub", "adapter_tag": self.adapter_tag,
                "step": self.step, "seed": self.seed}
        with open(os.path.join(target, "adapter.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(meta, fh, indent=2, sort_keys=True)
            fh.write("\n")
        return target

    @classmethod
    def load_checkpoint(cls, path):
        meta = json.load(open(os.path.join(path, "adapter.json"), encoding="utf-8"))
        return cls(adapter_tag=meta["adapter_tag"], step=meta["step"], seed=meta["seed"])


class HFBackend:
    """Placeholder for the real model on GX10. Not runnable on the CPU host."""
    kind = "hf"

    @classmethod
    def from_config(cls, cfg, target="base"):
        raise RuntimeError(
            "HFBackend requires the transformers stack and the base checkpoint; "
            "run on the GX10 run001 image (backend: hf). Dispatch 18A rehearses "
            "the pipeline on the CPU host with backend: stub.")


def get_backend(name):
    return {"stub": StubBackend, "hf": HFBackend}[name]
