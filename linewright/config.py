"""Shared config loader + validator for the LineWright training harness."""
import hashlib
import json
import os

import yaml

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Only training-run outputs may be written here (Part 5).
AUTHORIZED_OUTPUT_ROOTS = [os.path.join("training", "runs", "dataset-a-smoke-v1")]

# Fields that LoRA and ternary-QAT smoke configs MUST share for an interpretable
# comparison. Anything else that differs must be a documented QAT-only field.
SHARED_CRITICAL_FIELDS = [
    "max_steps", "seed", "effective_batch_size", "max_sequence_length",
    "train_file", "evaluation_file", "base_model_revision",
]
# Explicitly documented allowed differences between the two configs.
QAT_ONLY_DIFFERENCES = {"learning_rate", "ternary_qat"}


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load_config(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def abs_repo(rel):
    if os.path.isabs(rel):
        return os.path.abspath(rel)
    return os.path.abspath(os.path.join(REPO_ROOT, rel))


def effective_batch_size(cfg):
    o = cfg.get("optimization", {})
    return int(o.get("micro_batch_size", 1)) * int(o.get("gradient_accumulation_steps", 1))


def _critical_view(cfg):
    """The comparison-critical fields, flattened."""
    o = cfg.get("optimization", {})
    d = cfg.get("dataset", {})
    return {
        "max_steps": o.get("max_steps"),
        "seed": cfg.get("reproducibility", {}).get("seed"),
        "effective_batch_size": effective_batch_size(cfg),
        "max_sequence_length": cfg.get("sequence", {}).get("max_sequence_length"),
        "train_file": d.get("train_file"),
        "evaluation_file": d.get("evaluation_file"),
        "base_model_revision": cfg.get("model", {}).get("base_model_revision"),
    }


class ValidationResult:
    def __init__(self):
        self.messages = []
        self.problems = []

    @property
    def ok(self):
        return not self.problems

    def emit(self, m):
        self.messages.append(m)

    def fail(self, m):
        self.problems.append(m)


def validate_config(cfg, cfg_path, require_hashes=True, check_overrides=None):
    """Reject a configuration that is unsafe to execute (Part 3)."""
    r = ValidationResult()
    o = cfg.get("optimization", {})
    d = cfg.get("dataset", {})
    m = cfg.get("model", {})
    paths = cfg.get("paths", {})

    # required fields
    required = {
        "experiment_id": cfg.get("experiment_id"),
        "model.base_model": m.get("base_model"),
        "model.base_model_revision": m.get("base_model_revision"),
        "dataset.train_file": d.get("train_file"),
        "dataset.evaluation_file": d.get("evaluation_file"),
        "dataset.system_prompt_file": d.get("system_prompt_file"),
        "reproducibility.seed": cfg.get("reproducibility", {}).get("seed"),
        "sequence.max_sequence_length": cfg.get("sequence", {}).get("max_sequence_length"),
        "optimization.max_steps": o.get("max_steps"),
        "paths.output_dir": paths.get("output_dir"),
    }
    for k, v in required.items():
        if v in (None, ""):
            r.fail(f"missing required field '{k}'")

    # max_steps positive integer
    ms = o.get("max_steps")
    if check_overrides and "max_steps" in check_overrides:
        ms = check_overrides["max_steps"]
    if not (isinstance(ms, int) and ms > 0):
        r.fail(f"max_steps must be a positive integer (got {ms!r})")

    # effective batch size valid
    ebs = effective_batch_size(cfg)
    if ebs <= 0:
        r.fail(f"effective batch size invalid ({ebs})")

    # production flags
    if cfg.get("production_approved") is not False:
        r.fail("production_approved must be false (experimental only)")
    if cfg.get("experimental_use_only") is not True:
        r.fail("experimental_use_only must be true")

    # referenced input files exist + pinned hashes
    file_hash_pairs = [
        (d.get("train_file"), d.get("train_checksum"), "train"),
        (d.get("evaluation_file"), d.get("evaluation_checksum"), "evaluation"),
        (d.get("system_prompt_file"), d.get("system_prompt_checksum"), "system_prompt"),
    ]
    hashes_ok = True
    for rel, pinned, name in file_hash_pairs:
        if not rel:
            continue
        p = abs_repo(rel)
        if not os.path.exists(p):
            r.fail(f"{name} file does not exist: {rel}")
            hashes_ok = False
            continue
        if require_hashes and pinned:
            actual = sha256_file(p)
            if actual != pinned:
                r.fail(f"{name} hash mismatch: pinned {pinned[:12]}… actual {actual[:12]}…")
                hashes_ok = False

    # output dir under an authorized root
    out = paths.get("output_dir")
    out_ok = False
    if out:
        out_abs = abs_repo(out)
        for root in AUTHORIZED_OUTPUT_ROOTS:
            if out_abs == abs_repo(root) or out_abs.startswith(abs_repo(root) + os.sep):
                out_ok = True
        if not out_ok:
            r.fail(f"output_dir '{out}' is outside authorized roots {AUTHORIZED_OUTPUT_ROOTS}")

    # a one-step rehearsal config must never train on the real Dataset A file
    if "onestep" in str(cfg.get("experiment_id", "")):
        tf = (d.get("train_file") or "").replace("\\", "/")
        if tf.endswith("compiled/experimental-v1/train.jsonl"):
            r.fail("one-step rehearsal config must not reference the production "
                   "Dataset A train file for gradients")

    # train/evaluation splits disjoint
    disjoint = True
    try:
        tr = _ids(abs_repo(d["train_file"]))
        ev = _ids(abs_repo(d["evaluation_file"]))
        overlap = tr & ev
        if overlap:
            r.fail(f"train/evaluation leakage: shared ids {sorted(overlap)}")
            disjoint = False
    except Exception as e:
        r.fail(f"could not check split disjointness: {e}")
        disjoint = False

    if r.ok:
        r.emit("CONFIG VALID")
        if require_hashes and hashes_ok:
            r.emit("INPUT HASHES VALID")
        if disjoint:
            r.emit("TRAIN/EVALUATION SPLITS DISJOINT")
        if out_ok:
            r.emit("AUTHORIZED OUTPUT PATH VALID")
    return r


def _ids(jsonl_path):
    out = set()
    with open(jsonl_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.add(json.loads(line)["id"])
    return out


def compare_configs(lora_cfg, qat_cfg):
    """Verify LoRA and QAT configs agree on every shared-critical field; only
    documented QAT-only fields may differ (Part 1 / Part 11 #19)."""
    problems = []
    lv, qv = _critical_view(lora_cfg), _critical_view(qat_cfg)
    for field in SHARED_CRITICAL_FIELDS:
        if lv[field] != qv[field]:
            problems.append(f"shared-critical field '{field}' differs: "
                            f"lora={lv[field]!r} qat={qv[field]!r}")
    # learning_rate is an allowed QAT-only difference; ternary_qat block is QAT-only
    if "ternary_qat" not in qat_cfg:
        problems.append("qat config missing ternary_qat block")
    if "ternary_qat" in lora_cfg:
        problems.append("lora config must not contain a ternary_qat block")
    return problems
