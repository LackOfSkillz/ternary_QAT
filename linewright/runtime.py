"""Runtime guards: authorized-path enforcement, automated stop conditions,
checkpoint-reload verification, and run manifests (Parts 5, 6, 7)."""
import json
import math
import os
import platform
import subprocess
import sys


# ---------- Part 5: authorized output-path guard ----------

class PathGuardError(Exception):
    pass


class AuthorizedWriter:
    def __init__(self, roots):
        self.roots = [os.path.realpath(os.path.abspath(r)) for r in roots]

    def resolve(self, path):
        """Return the safe absolute path or raise. Rejects traversal + symlink escape."""
        p = os.path.abspath(path)
        real = os.path.realpath(p)               # collapses .. and resolves symlinks
        for root in self.roots:
            if real == root or real.startswith(root + os.sep):
                return p
        raise PathGuardError(f"write outside authorized roots {self.roots}: {path}")

    def open(self, path, mode="w", **kw):
        safe = self.resolve(path)
        os.makedirs(os.path.dirname(safe), exist_ok=True)
        return open(safe, mode, **kw)


# ---------- Part 6: stop conditions ----------

class StopCondition(Exception):
    def __init__(self, reason, detail=None):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail or {}


def check_loss_finite(loss, step=None, lr=None, batch_ids=None):
    if loss is None or not math.isfinite(float(loss)):
        raise StopCondition("loss_non_finite",
                            {"step": step, "loss": repr(loss), "lr": lr,
                             "batch_record_ids": batch_ids})


def check_gradients_finite(grad_norm, step=None):
    if grad_norm is None or not math.isfinite(float(grad_norm)):
        raise StopCondition("gradient_non_finite",
                            {"step": step, "grad_norm": repr(grad_norm)})


class GradientMonitor:
    """Warn on one breach; abort on two consecutive; immediate abort on non-finite."""
    def __init__(self, max_global_norm=100.0, consecutive_step_limit=2):
        self.max = float(max_global_norm)
        self.limit = int(consecutive_step_limit)
        self.consecutive = 0
        self.warnings = []

    def observe(self, grad_norm, step=None):
        check_gradients_finite(grad_norm, step)
        if float(grad_norm) > self.max:
            self.consecutive += 1
            self.warnings.append({"step": step, "grad_norm": float(grad_norm)})
            if self.consecutive >= self.limit:
                raise StopCondition("gradient_explosion",
                                    {"step": step, "grad_norm": float(grad_norm),
                                     "consecutive": self.consecutive, "threshold": self.max})
            return "warn"
        self.consecutive = 0
        return "ok"


class StallMonitor:
    def __init__(self, accumulation_interval=1):
        self.last_step = -1
        self.no_progress = 0
        self.interval = accumulation_interval

    def observe(self, step, loss_available):
        if not loss_available:
            raise StopCondition("loss_unavailable", {"step": step})
        if step <= self.last_step:
            self.no_progress += 1
            if self.no_progress > self.interval:
                raise StopCondition("optimizer_stall", {"step": step})
        else:
            self.no_progress = 0
            self.last_step = step


# ---------- Part 6: checkpoint reload verification ----------

def verify_checkpoint_reload(checkpoint_dir, backend="stub"):
    """Start a FRESH python process, load the checkpoint, generate one short
    response, and confirm non-empty output. A checkpoint is not valid until this
    passes (Part 6)."""
    proc = subprocess.run(
        [sys.executable, "-m", "linewright.reload_check",
         "--checkpoint", checkpoint_dir, "--backend", backend],
        capture_output=True, text=True,
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    try:
        result = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        return {"ok": False, "error": "reload subprocess produced no parseable result",
                "stdout": proc.stdout[-500:], "stderr": proc.stderr[-500:]}
    return result


# ---------- Part 7: run manifest ----------

def software_environment():
    env = {"python": sys.version.split()[0], "platform": platform.platform()}
    try:
        import torch
        env["torch"] = torch.__version__
        env["cuda_available"] = bool(torch.cuda.is_available())
        env["device_name"] = (torch.cuda.get_device_name(0)
                              if torch.cuda.is_available() else "cpu")
    except Exception:
        env["torch"] = None
        env["cuda_available"] = False
        env["device_name"] = "cpu"
    for mod in ("transformers", "peft", "accelerate"):
        try:
            env[mod] = __import__(mod).__version__
        except Exception:
            env[mod] = None
    return env


def build_run_manifest(**fields):
    """Assemble a machine-readable run manifest (no secrets)."""
    manifest = {"software": software_environment()}
    manifest.update(fields)
    return manifest
