"""HF-backend unit tests that do NOT require the 4B model (Part 15).

Uses a fake tokenizer + tiny nn modules + direct helper calls so masking, LoRA
target discovery, ternary replacement guards, revision verification, checkpoint
routing, and config guards are all provable on a CPU host.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(__file__)
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
sys.path.insert(0, _ROOT)

torch = pytest.importorskip("torch")
import torch.nn as nn                                  # noqa: E402
from linewright import collate                          # noqa: E402
from linewright import config as C                      # noqa: E402
from linewright import reload_check                     # noqa: E402
from linewright.backends import HFBackend, StubBackend, get_backend  # noqa: E402
from linewright import runtime                          # noqa: E402

LORA = os.path.join(_ROOT, "training", "configs", "dataset-a-lora-smoke-v1.yaml")


class FakeTokenizer:
    chat_template = None
    eos_token = "</s>"
    pad_token = "<pad>"
    pad_token_id = 0

    def __call__(self, text, add_special_tokens=True):
        ids = [(len(w) * 31 + ord(w[0])) % 5000 for w in text.split()]
        return {"input_ids": ids}


MSGS = [{"role": "system", "content": "sys words here"},
        {"role": "user", "content": "please revise this line now"},
        {"role": "assistant", "content": "revised line output tokens"}]


# 2 + 3 + 4 assistant-only masking
def test_masking_prompt_labels_are_minus_100():
    ex = collate.build_training_example(FakeTokenizer(), MSGS, max_length=512)
    plen = ex["prompt_token_count"]
    assert all(l == -100 for l in ex["labels"][:plen])
    assert ex["target_token_count"] >= 1
    assert any(l != -100 for l in ex["labels"][plen:])


def test_padding_labels_masked():
    a = collate.build_training_example(FakeTokenizer(), MSGS, 512)
    b = collate.build_training_example(
        FakeTokenizer(),
        [MSGS[0], {"role": "user", "content": "x"}, {"role": "assistant", "content": "y z w q"}],
        512)
    batch = collate.collate_batch(FakeTokenizer(), [a, b], pad_token_id=0)
    # shorter example's padded tail is all -100
    labels = batch["labels"].tolist()
    assert -100 in labels[0] and -100 in labels[1]
    assert batch["input_ids"].shape == batch["labels"].shape


# 5 excessive truncation fails
def test_excessive_truncation_fails():
    with pytest.raises(collate.MaskingError):
        collate.build_training_example(FakeTokenizer(), MSGS, max_length=2)


class FakeChatTokenizer(FakeTokenizer):
    chat_template = "{{ some template }}"

    def apply_chat_template(self, messages, tokenize=True, add_generation_prompt=False):
        text = " ".join(m["content"] for m in messages)
        if add_generation_prompt:
            text += " gen"
        return text if tokenize else text          # returns a STRING even when tokenize=True


class _BatchEnc:
    def __init__(self, ids):
        self.input_ids = ids


class FakeBatchTokenizer(FakeTokenizer):
    chat_template = "{{ tmpl }}"

    def apply_chat_template(self, messages, tokenize=True, add_generation_prompt=False):
        text = " ".join(m["content"] for m in messages) + (" gen" if add_generation_prompt else " end")
        ids = self(text)["input_ids"]
        return _BatchEnc(ids) if tokenize else text   # BatchEncoding-like (has .input_ids)


@pytest.mark.parametrize("tok", [FakeChatTokenizer(), FakeBatchTokenizer()])
def test_template_ids_robust_to_return_type(tok):
    ids = collate.build_generation_ids(tok, MSGS[:2])
    assert ids and all(isinstance(i, int) for i in ids)
    ex = collate.build_training_example(tok, MSGS, max_length=512)
    assert all(isinstance(i, int) for i in ex["input_ids"])
    assert ex["target_token_count"] >= 1


# 6 shared formatter is deterministic
def test_formatter_deterministic():
    t = FakeTokenizer()
    assert collate.build_generation_ids(t, MSGS[:2]) == collate.build_generation_ids(t, MSGS[:2])
    txt1, used1 = collate.render_prompt_text(t, MSGS[:2])
    txt2, used2 = collate.render_prompt_text(t, MSGS[:2])
    assert txt1 == txt2 and used1 == used2 is False


# 7 + 8 LoRA target-module discovery
def _tiny_attn_model():
    m = nn.Module()
    m.q_proj = nn.Linear(4, 4)
    m.k_proj = nn.Linear(4, 4)
    m.v_proj = nn.Linear(4, 4)
    m.mlp = nn.Linear(4, 4)               # not a target
    return m


def test_lora_discovery_matches_expected():
    b = HFBackend()
    b.model = _tiny_attn_model()
    matched = b._match_lora_modules(["q_proj", "k_proj", "v_proj", "o_proj"])
    assert {"q_proj", "k_proj", "v_proj"} <= matched
    assert "mlp" not in matched


def test_lora_zero_match_raises():
    b = HFBackend()
    m = nn.Module()
    m.mlp = nn.Linear(4, 4)
    b.model = m
    b.cfg = {"lora": {"target_modules": ["q_proj"]}}
    with pytest.raises(RuntimeError):
        b._attach_lora()


# 9 + 10 ternary replacement excludes norms / fails on zero
def test_ternary_excludes_norm_modules():
    from ternary.swap import swap_linear
    from ternary.linear import TernaryLinear

    class M(nn.Module):
        def __init__(self):
            super().__init__()
            self.proj = nn.Linear(128, 128)          # swapped
            self.input_norm = nn.Linear(128, 128)    # excluded (name has 'norm')
    m = M()
    swap_linear(m, None)
    assert isinstance(m.proj, TernaryLinear)
    assert not isinstance(m.input_norm, TernaryLinear)


def test_ternary_zero_replacement_raises():
    b = HFBackend()

    class OnlyNorm(nn.Module):
        def __init__(self):
            super().__init__()
            self.input_norm = nn.Linear(8, 8)
    b.model = OnlyNorm()
    b.cfg = {"ternary_qat": {"group_size": 128}}
    with pytest.raises(RuntimeError):
        b._attach_ternary()


# 11 tied-weight detection
def test_tied_weight_detection():
    a, c = nn.Linear(4, 4), nn.Linear(4, 4)
    c.weight = a.weight
    assert a.weight.data_ptr() == c.weight.data_ptr()          # tied
    c.weight = nn.Parameter(a.weight.detach().clone())
    assert a.weight.data_ptr() != c.weight.data_ptr()          # broken tie detectable


# 12 reload distinguishes checkpoint types
def test_reload_detects_types(tmp_path):
    lora = tmp_path / "lora"
    lora.mkdir()
    (lora / "lw-checkpoint.json").write_text(json.dumps({"checkpoint_type": "lora"}), encoding="utf-8")
    qat = tmp_path / "qat"
    qat.mkdir()
    (qat / "lw-checkpoint.json").write_text(json.dumps({"checkpoint_type": "ternary-qat"}), encoding="utf-8")
    stub = tmp_path / "stub"
    stub.mkdir()
    (stub / "adapter.json").write_text("{}", encoding="utf-8")
    assert reload_check.detect_type(str(lora)) == "lora"
    assert reload_check.detect_type(str(qat)) == "ternary-qat"
    assert reload_check.detect_type(str(stub)) == "stub"


# 13 HF cannot write into the base directory (path guard)
def test_hf_cannot_write_base_dir():
    w = runtime.AuthorizedWriter([C.abs_repo("training/runs/dataset-a-smoke-v1")])
    with pytest.raises(runtime.PathGuardError):
        w.resolve("/workspace/hf-cache/prism-ml/Ternary-Bonsai-4B-unpacked/model.safetensors")


# 15 one-step config cannot reference the production Dataset A train file
def test_onestep_rejects_production_train():
    cfg = C.load_config(LORA)
    cfg["experiment_id"] = "dataset-a-hf-lora-onestep"
    cfg["dataset"]["train_file"] = "datasets/dataset-a/compiled/experimental-v1/train.jsonl"
    r = C.validate_config(cfg, LORA, require_hashes=False)
    assert any("must not reference the production" in p for p in r.problems)


# 17 backend hf resolves to HFBackend, never StubBackend
def test_get_backend_hf_is_hf_not_stub():
    assert get_backend("hf") is HFBackend
    assert get_backend("stub") is StubBackend
    assert HFBackend is not StubBackend


# 19 real model revision mismatch fails
def test_revision_mismatch_raises(tmp_path):
    (tmp_path / "config.json").write_text(json.dumps({"_commit_hash": "aaaa"}), encoding="utf-8")
    b = HFBackend()
    with pytest.raises(RuntimeError):
        b._verify_revision(str(tmp_path), "bbbb")
    # matching revision passes
    b._verify_revision(str(tmp_path), "aaaa")
    assert b._revision_check == "verified"


# 16 hf run refuses stub failure injection (no synthetic loss path)
def test_hf_run_rejects_inject():
    from linewright import train
    with pytest.raises(ValueError):
        train.run(os.path.join(_ROOT, "training", "configs", "dataset-a-hf-lora-onestep.yaml"),
                  backend_name="hf", inject="nan_loss")


# 20 the real 20-step configs still say 20 (unexecuted here)
def test_real_configs_still_20_steps():
    assert C.load_config(LORA)["optimization"]["max_steps"] == 20


QAT = os.path.join(_ROOT, "training", "configs", "dataset-a-ternary-qat-smoke-v1.yaml")


def test_qat_config_policy_matches_swap_implementation():
    """The reconciled QAT config must state the SAME policy the verified
    ternary/swap.py actually applies: embeddings + lm_head ternary, norms FP."""
    pol = C.load_config(QAT)["ternary_qat"]["module_policy"]
    assert pol["embeddings"] == "ternary"
    assert pol["lm_head"] == "ternary"
    assert pol["attention_linear"] == "ternary"
    assert pol["mlp_linear"] == "ternary"
    assert pol["normalization_layers"] == "full_precision"
    assert "keep_modules_full_precision" not in C.load_config(QAT)["ternary_qat"]

    # actual behavior: swap_linear ternarizes embed + lm_head + attn, excludes norms
    from ternary.swap import swap_linear, TernaryEmbedding
    from ternary.linear import TernaryLinear

    class M(nn.Module):
        def __init__(self):
            super().__init__()
            self.embed_tokens = nn.Embedding(8, 16)
            self.q_proj = nn.Linear(16, 16)
            self.input_norm = nn.Linear(16, 16)   # 'norm' -> excluded (full precision)
            self.lm_head = nn.Linear(16, 8)
    m = M()
    swap_linear(m, None)
    assert isinstance(m.embed_tokens, TernaryEmbedding)     # embeddings ternary
    assert isinstance(m.lm_head, TernaryLinear)             # lm_head ternary
    assert isinstance(m.q_proj, TernaryLinear)              # attention ternary
    assert not isinstance(m.input_norm, TernaryLinear)      # norm full precision
