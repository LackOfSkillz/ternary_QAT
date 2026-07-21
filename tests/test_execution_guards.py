"""Failure-injection tests proving the execution guards trigger (Part 11).

Unit-level tests of the guard functions plus one integration abort. Uses stubs and
temp dirs; the 4B checkpoint is never required.
"""
import os
import shutil
import sys

import pytest

_HERE = os.path.dirname(__file__)
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
sys.path.insert(0, _ROOT)

yaml = pytest.importorskip("yaml")
from linewright import config as C            # noqa: E402
from linewright import integrity, runtime     # noqa: E402
from linewright.backends import StubBackend   # noqa: E402
from linewright.eval import structural_check  # noqa: E402
from linewright.reproducibility import compare_runs  # noqa: E402

LORA = os.path.join(_ROOT, "training", "configs", "dataset-a-lora-smoke-v1.yaml")
QAT = os.path.join(_ROOT, "training", "configs", "dataset-a-ternary-qat-smoke-v1.yaml")


# 1-4 non-finite loss/grad -> StopCondition
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_loss_aborts(bad):
    with pytest.raises(runtime.StopCondition) as e:
        runtime.check_loss_finite(bad, step=1)
    assert e.value.reason == "loss_non_finite"


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_non_finite_gradient_aborts(bad):
    with pytest.raises(runtime.StopCondition) as e:
        runtime.check_gradients_finite(bad, step=1)
    assert e.value.reason == "gradient_non_finite"


# 5 + 6 gradient explosion: two consecutive breaches abort; one only warns
def test_one_grad_breach_warns_not_abort():
    m = runtime.GradientMonitor(max_global_norm=100.0, consecutive_step_limit=2)
    assert m.observe(250.0, step=1) == "warn"          # one breach: warn only


def test_two_consecutive_grad_breaches_abort():
    m = runtime.GradientMonitor(max_global_norm=100.0, consecutive_step_limit=2)
    m.observe(250.0, step=1)
    with pytest.raises(runtime.StopCondition) as e:
        m.observe(300.0, step=2)
    assert e.value.reason == "gradient_explosion"


# 7 train/eval overlap -> validation failure
def test_train_eval_overlap_fails(tmp_path):
    import json
    tr = tmp_path / "t.jsonl"
    ev = tmp_path / "e.jsonl"
    tr.write_text(json.dumps({"id": "shared"}) + "\n", encoding="utf-8")
    ev.write_text(json.dumps({"id": "shared"}) + "\n", encoding="utf-8")
    sp = C.abs_repo("datasets/dataset-a/prompts/linewright-training-system-v1.txt")
    cfg = {"experiment_id": "x", "production_approved": False, "experimental_use_only": True,
           "model": {"base_model": "b", "base_model_revision": "r"},
           "paths": {"output_dir": "training/runs/dataset-a-smoke-v1/x"},
           "dataset": {"train_file": str(tr), "evaluation_file": str(ev),
                       "system_prompt_file": "datasets/dataset-a/prompts/linewright-training-system-v1.txt",
                       "train_checksum": C.sha256_file(str(tr)),
                       "evaluation_checksum": C.sha256_file(str(ev)),
                       "system_prompt_checksum": C.sha256_file(sp)},
           "reproducibility": {"seed": 1}, "sequence": {"max_sequence_length": 8},
           "optimization": {"max_steps": 1, "micro_batch_size": 1, "gradient_accumulation_steps": 8}}
    r = C.validate_config(cfg, "x")
    assert any("leakage" in p for p in r.problems)


# 8 + 9 wrong hashes -> failure
def test_wrong_train_hash_fails():
    cfg = C.load_config(LORA)
    cfg["dataset"]["train_checksum"] = "0" * 64
    r = C.validate_config(cfg, LORA)
    assert any("train hash mismatch" in p for p in r.problems)


def test_wrong_system_prompt_hash_fails():
    cfg = C.load_config(LORA)
    cfg["dataset"]["system_prompt_checksum"] = "0" * 64
    r = C.validate_config(cfg, LORA)
    assert any("system_prompt hash mismatch" in p for p in r.problems)


# 10 unauthorized output path -> failure (config + writer)
def test_unauthorized_output_dir_fails():
    cfg = C.load_config(LORA)
    cfg["paths"]["output_dir"] = "some/unauthorized/dir"
    r = C.validate_config(cfg, LORA)
    assert any("outside authorized roots" in p for p in r.problems)


def test_path_traversal_rejected():
    w = runtime.AuthorizedWriter([C.abs_repo("training/runs/dataset-a-smoke-v1")])
    with pytest.raises(runtime.PathGuardError):
        w.resolve(C.abs_repo("training/runs/dataset-a-smoke-v1/../../../etc/passwd"))
    with pytest.raises(runtime.PathGuardError):
        w.resolve(os.path.abspath(os.path.join(os.sep, "tmp", "evil")))
    # a proper checkpoint path resolves fine
    assert w.resolve(C.abs_repo("training/runs/dataset-a-smoke-v1/lora/checkpoints/step-10"))


# 11 symlink escape (where supported)
def test_symlink_escape_rejected(tmp_path):
    root = C.abs_repo("training/runs/dataset-a-smoke-v1")
    link = os.path.join(root, "_pytest_escape_link")
    outside = str(tmp_path)
    try:
        if os.path.exists(link):
            os.remove(link)
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation not supported here")
    try:
        w = runtime.AuthorizedWriter([root])
        with pytest.raises(runtime.PathGuardError):
            w.resolve(os.path.join(link, "evil.txt"))
    finally:
        os.remove(link)


# 12-14 base-model inventory: byte change / new file / missing file
def test_inventory_byte_change_detected(tmp_path):
    d = tmp_path / "base"
    d.mkdir()
    (d / "w.txt").write_text("aaa", encoding="utf-8")
    before = integrity.capture_inventory(str(d))
    (d / "w.txt").write_text("bbb", encoding="utf-8")
    after = integrity.capture_inventory(str(d))
    v = integrity.verify_inventory(before, after)
    assert not v["ok"] and "w.txt" in v["changed_bytes"]


def test_inventory_new_file_detected(tmp_path):
    d = tmp_path / "base"
    d.mkdir()
    (d / "w.txt").write_text("a", encoding="utf-8")
    before = integrity.capture_inventory(str(d))
    (d / "new.bin").write_text("x", encoding="utf-8")
    v = integrity.verify_inventory(before, integrity.capture_inventory(str(d)))
    assert not v["ok"] and "new.bin" in v["new_files"]


def test_inventory_missing_file_detected(tmp_path):
    d = tmp_path / "base"
    d.mkdir()
    (d / "w.txt").write_text("a", encoding="utf-8")
    before = integrity.capture_inventory(str(d))
    os.remove(d / "w.txt")
    v = integrity.verify_inventory(before, integrity.capture_inventory(str(d)))
    assert not v["ok"] and "w.txt" in v["missing"]


# 15 checkpoint reload failure marks failure
def test_checkpoint_reload_failure_detected(tmp_path):
    result = runtime.verify_checkpoint_reload(str(tmp_path / "nonexistent"), backend="stub")
    assert result["ok"] is False


# 16 invalid JSON eval output reported, not repaired
def test_invalid_json_output_reported():
    gold = '{"violation": true, "constraint_ids": ["C1"]}'
    checks, parsed = structural_check("constraint_check", gold, "not json at all")
    assert checks["format_valid"] is False and parsed is None


# 17 no-change text corruption fails the deterministic check
def test_no_change_corruption_fails():
    gold = '{"changed": false, "reason": "ok", "text": "the exact source"}'
    good = '{"changed": false, "reason": "x", "text": "the exact source"}'
    bad = '{"changed": false, "reason": "x", "text": "corrupted different text"}'
    ok_checks, _ = structural_check("focused_revision", gold, good)
    bad_checks, _ = structural_check("focused_revision", gold, bad)
    assert ok_checks["no_change_preserved"] is True
    assert bad_checks["no_change_preserved"] is False


# 18 reproducibility cannot be accepted when checks disagree
def test_reproducibility_fails_on_disagreement():
    def run(valid):
        return {"records": [{"record_id": "r", "raw_output": "o", "parsed_output": None,
                             "format_valid": valid, "deterministic_checks": {"format_valid": valid}}]}
    res = compare_runs(run(True), run(False))
    assert res["disposition"] == "failed" and res["accepted"] is False


# 19 LoRA/QAT comparison validation fails when a shared field differs
def test_config_comparison_detects_shared_field_drift():
    lora = C.load_config(LORA)
    qat = C.load_config(QAT)
    assert C.compare_configs(lora, qat) == []              # baseline agrees
    qat2 = C.load_config(QAT)
    qat2["optimization"]["max_steps"] = 999
    assert any("max_steps" in p for p in C.compare_configs(lora, qat2))


# 20 both real smoke configs use exactly 20 steps
def test_real_configs_use_20_steps():
    assert C.load_config(LORA)["optimization"]["max_steps"] == 20
    assert C.load_config(QAT)["optimization"]["max_steps"] == 20


# integration: injected NaN loss aborts a full (synthetic) run
def test_injected_nan_loss_aborts_run(tmp_path):
    import json
    out_sub = "training/runs/dataset-a-smoke-v1/_pytest_inject"
    tr = tmp_path / "t.jsonl"
    ev = tmp_path / "e.jsonl"
    tr.write_text(json.dumps({"id": "a"}) + "\n", encoding="utf-8")
    ev.write_text(json.dumps({"id": "b"}) + "\n", encoding="utf-8")
    sp_rel = "datasets/dataset-a/prompts/linewright-training-system-v1.txt"
    cfg = {"experiment_id": "inject", "production_approved": False, "experimental_use_only": True,
           "model": {"base_model": "b", "base_model_revision": "r"},
           "paths": {"output_dir": out_sub},
           "dataset": {"train_file": str(tr), "evaluation_file": str(ev),
                       "system_prompt_file": sp_rel,
                       "train_checksum": C.sha256_file(str(tr)),
                       "evaluation_checksum": C.sha256_file(str(ev)),
                       "system_prompt_checksum": C.sha256_file(C.abs_repo(sp_rel))},
           "reproducibility": {"seed": 1}, "sequence": {"max_sequence_length": 8},
           "optimization": {"max_steps": 3, "micro_batch_size": 1, "gradient_accumulation_steps": 8},
           "intervals": {"checkpoint_interval_steps": 1}}
    cfg_path = tmp_path / "c.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    from linewright import train
    try:
        manifest, code = train.run(str(cfg_path), backend_name="stub", inject="nan_loss")
        assert manifest["status"] == "aborted"
        assert manifest["stop_reason"] == "loss_non_finite"
        assert code == 2
    finally:
        shutil.rmtree(C.abs_repo(out_sub), ignore_errors=True)
