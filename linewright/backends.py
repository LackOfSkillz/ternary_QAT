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
    def from_config(cls, cfg, target="base", **_):
        seed = cfg.get("reproducibility", {}).get("seed", 0)
        return cls(adapter_tag=target, step=0, seed=seed)

    def generate(self, messages, gen=None):
        """Deterministic canned output; pure function of (messages, adapter, seed).
        `messages` is a list of {role, content} (or a plain string, legacy)."""
        gen = gen or {}
        if isinstance(messages, str):
            prompt = messages
        else:
            prompt = "\n\n".join(m["content"] for m in messages)
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


LORA_TARGET_DEFAULT = ["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"]


class HFBackend:
    """Real transformers/PEFT/ternary backend. Heavy imports are deferred so this
    module stays importable on a plain CPU host. NEVER falls back to the stub."""
    kind = "hf"

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.cfg = None
        self.target = "base"
        self.device = "cpu"
        self.optimizer = None
        self.scheduler = None
        self._batches = None
        self._batch_ptr = 0
        self.last_batch_ids = []
        self.diagnostics = {}

    # ---- loading ----
    @classmethod
    def from_config(cls, cfg, target="base", for_training=False, device=None,
                    checkpoint_dir=None, **_):
        import time
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self = cls()
        self.cfg = cfg
        self.target = target
        m = cfg["model"]
        base_path = m.get("base_model_path")
        revision = m.get("base_model_revision")
        cache_dir = cfg.get("paths", {}).get("cache_dir")
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        t0 = time.time()
        load_kwargs = dict(torch_dtype=torch.bfloat16, attn_implementation="sdpa",
                           local_files_only=True)
        if base_path and _os_isdir(base_path):
            model_src = base_path
        else:
            model_src = m["base_model"]
            load_kwargs["revision"] = revision
            load_kwargs["cache_dir"] = cache_dir
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_src, local_files_only=True,
            **({"revision": revision, "cache_dir": cache_dir}
               if not (base_path and _os_isdir(base_path)) else {}))
        self.model = AutoModelForCausalLM.from_pretrained(model_src, **load_kwargs)
        load_secs = round(time.time() - t0, 2)

        self._verify_revision(model_src, revision)
        self._setup_tokenizer()
        self.model.to(self.device)

        self.diagnostics = {
            "model_src": model_src, "resolved_revision": self._resolved_revision,
            "revision_check": self._revision_check,
            "model_class": type(self.model).__name__,
            "tokenizer_class": type(self.tokenizer).__name__,
            "chat_template": bool(getattr(self.tokenizer, "chat_template", None)),
            "load_seconds": load_secs, "device": self.device,
            "total_params": sum(p.numel() for p in self.model.parameters()),
        }

        if target == "lora":
            if checkpoint_dir:
                self._load_lora_checkpoint(checkpoint_dir)
            else:
                self._attach_lora()
        elif target == "ternary-qat":
            if checkpoint_dir:
                self._load_qat_checkpoint(checkpoint_dir)
            else:
                self._attach_ternary()

        if for_training:
            self._build_optimizer_and_data()
            self.model.train()
        else:
            self.model.eval()
        return self

    def _verify_revision(self, model_src, revision):
        import json as _json
        self._resolved_revision = revision
        self._revision_check = "path_pinned"
        cfg_json = _os_join(model_src, "config.json")
        if _os_isfile(cfg_json):
            data = _json.load(open(cfg_json, encoding="utf-8"))
            commit = data.get("_commit_hash") or data.get("_commit")
            if commit:
                self._resolved_revision = commit
                if revision and commit != revision:
                    raise RuntimeError(
                        f"model revision mismatch: resolved {commit} != configured {revision}")
                self._revision_check = "verified"

    def _setup_tokenizer(self):
        tok = self.tokenizer
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        if tok.eos_token is None:
            raise RuntimeError("tokenizer has no EOS token")
        tok.padding_side = "right"
        self.model.config.pad_token_id = tok.pad_token_id

    def _attach_lora(self):
        from peft import LoraConfig, get_peft_model
        o = self.cfg.get("lora", {})
        targets = o.get("target_modules", LORA_TARGET_DEFAULT)
        matched = self._match_lora_modules(targets)
        if not matched:
            raise RuntimeError(f"no LoRA target modules matched from {targets}")
        lc = LoraConfig(r=o.get("lora_rank", 16), lora_alpha=o.get("lora_alpha", 32),
                        lora_dropout=o.get("lora_dropout", 0.05),
                        target_modules=targets, task_type="CAUSAL_LM")
        self.model = get_peft_model(self.model, lc)
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.model.parameters())
        self.diagnostics.update({
            "lora_target_modules": targets,
            "lora_modules_matched": len(matched),
            "lora_matched_names": sorted(matched)[:20],
            "lora_trainable_params": trainable, "lora_total_params": total,
            "lora_trainable_pct": round(100 * trainable / total, 4),
            "lora_rank": o.get("lora_rank", 16), "lora_alpha": o.get("lora_alpha", 32),
            "lora_dropout": o.get("lora_dropout", 0.05),
        })

    def _match_lora_modules(self, targets):
        import torch.nn as nn
        matched = set()
        for name, mod in self.model.named_modules():
            if isinstance(mod, nn.Linear) and any(name.endswith(t) or f".{t}" in name
                                                  for t in targets):
                matched.add(name)
        return matched

    def _load_lora_checkpoint(self, checkpoint_dir):
        from peft import PeftModel
        self.model = PeftModel.from_pretrained(self.model, checkpoint_dir)
        self.diagnostics["loaded_checkpoint"] = checkpoint_dir
        self.diagnostics["checkpoint_type"] = "lora"

    def _load_qat_checkpoint(self, checkpoint_dir):
        import os
        import torch
        self._attach_ternary()               # rebuild the swapped layout
        state = torch.load(os.path.join(checkpoint_dir, "qat_state.pt"), map_location="cpu")
        res = self.model.load_state_dict(state, strict=False)
        self.diagnostics["loaded_checkpoint"] = checkpoint_dir
        self.diagnostics["checkpoint_type"] = "ternary-qat"
        self.diagnostics["reload_missing_keys"] = len(res.missing_keys)
        self.diagnostics["reload_unexpected_keys"] = len(res.unexpected_keys)

    def _attach_ternary(self):
        import torch.nn as nn
        from ternary.swap import swap_linear, TernaryEmbedding
        from ternary.linear import TernaryLinear
        qcfg = self.cfg.get("ternary_qat", {})
        before_linear = sum(1 for _n, mmod in self.model.named_modules()
                            if isinstance(mmod, nn.Linear))
        embed = getattr(getattr(self.model, "model", self.model), "embed_tokens", None)
        head = getattr(self.model, "lm_head", None)
        tied_before = (embed is not None and head is not None
                       and embed.weight.data_ptr() == head.weight.data_ptr())

        class _C:  # swap_linear reads .group_size off a cfg object
            group_size = qcfg.get("group_size", 128)
        swap_linear(self.model, _C())

        replaced = sum(1 for _n, mmod in self.model.named_modules()
                       if type(mmod).__name__ in ("TernaryLinear", "TernaryEmbedding"))
        remaining_plain = [n for n, mmod in self.model.named_modules()
                           if isinstance(mmod, nn.Linear)
                           and not isinstance(mmod, TernaryLinear)]
        new_embed = getattr(getattr(self.model, "model", self.model), "embed_tokens", None)
        new_head = getattr(self.model, "lm_head", None)
        tied_after = (new_embed is not None and new_head is not None
                      and new_embed.weight.data_ptr() == new_head.weight.data_ptr())
        if tied_before and not tied_after:
            raise RuntimeError("tied word embeddings broke during ternary swap")
        if replaced == 0:
            raise RuntimeError("ternary swap replaced zero modules")
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        self.diagnostics.update({
            "ternary_linear_before": before_linear,
            "ternary_modules_replaced": replaced,
            "ternary_excluded_remaining_linear": remaining_plain,
            "ternary_excluded_count": len(remaining_plain),
            "ternary_group_size": qcfg.get("group_size", 128),
            "tied_before": tied_before, "tied_after": tied_after,
            "tied_weight_result": "preserved" if (tied_before == tied_after) else "changed",
            "ternary_trainable_params": trainable,
        })

    # ---- training ----
    def _build_optimizer_and_data(self):
        import json
        import torch
        from linewright import config as C
        from linewright import collate
        o = self.cfg.get("optimization", {})
        lr = float(o.get("learning_rate", 2e-4))
        params = [p for p in self.model.parameters() if p.requires_grad]
        self.optimizer = torch.optim.AdamW(params, lr=lr)
        max_steps = o.get("max_steps", 1)
        self.scheduler = torch.optim.lr_scheduler.LambdaLR(
            self.optimizer, lambda s: 1.0)
        train_file = C.abs_repo(self.cfg["dataset"]["train_file"])
        rows = [json.loads(l) for l in open(train_file, encoding="utf-8") if l.strip()]
        max_len = self.cfg.get("sequence", {}).get("max_sequence_length", 2048)
        examples, ids = [], []
        for r in rows:
            ex = collate.build_training_example(self.tokenizer, r["messages"], max_len)
            examples.append(ex)
            ids.append(r["id"])
        micro = int(o.get("micro_batch_size", 1))
        self._batches = []
        for i in range(0, len(examples), micro):
            batch = collate.collate_batch(self.tokenizer, examples[i:i + micro],
                                          self.tokenizer.pad_token_id)
            self._batches.append((batch, ids[i:i + micro]))
        self.diagnostics["train_batches"] = len(self._batches)
        self.diagnostics["mask_counts_first_batch"] = {
            "input": examples[0]["input_token_count"],
            "masked": examples[0]["masked_token_count"],
            "target": examples[0]["target_token_count"],
            "truncated": examples[0]["truncated_token_count"]}

    def train_step(self, step, inject=None):
        import time
        import torch
        batch, ids = self._batches[self._batch_ptr % len(self._batches)]
        self._batch_ptr += 1
        self.last_batch_ids = ids
        batch = {k: v.to(self.device) for k, v in batch.items()}
        if self.device == "cuda":
            torch.cuda.reset_peak_memory_stats()
        t0 = time.time()
        out = self.model(**batch)
        loss = out.loss
        self.optimizer.zero_grad()
        tf = time.time()
        loss.backward()
        tb = time.time()
        params = [p for p in self.model.parameters() if p.requires_grad and p.grad is not None]
        grad_norm = torch.nn.utils.clip_grad_norm_(params, max_norm=1e9).item()
        lr = self.optimizer.param_groups[0]["lr"]
        self.optimizer.step()
        self.scheduler.step()
        to = time.time()
        target_tokens = int((batch["labels"] != -100).sum().item())
        input_tokens = int(batch["attention_mask"].sum().item())
        self.last_step_meta = {
            "lr": lr, "prompt_tokens": input_tokens - target_tokens,
            "target_tokens": target_tokens, "input_tokens": input_tokens,
            "forward_s": round(tf - t0, 4), "backward_s": round(tb - tf, 4),
            "optimizer_s": round(to - tb, 4), "step_s": round(to - t0, 4),
            "cuda_alloc_mb": (round(torch.cuda.memory_allocated() / 2**20, 1)
                              if self.device == "cuda" else None),
            "cuda_reserved_mb": (round(torch.cuda.memory_reserved() / 2**20, 1)
                                 if self.device == "cuda" else None),
            "cuda_peak_mb": (round(torch.cuda.max_memory_allocated() / 2**20, 1)
                             if self.device == "cuda" else None)}
        return float(loss.item()), float(grad_norm)

    # ---- generation ----
    def generate(self, messages, gen=None):
        import time
        import torch
        from linewright import collate
        gen = gen or {}
        ids = collate.build_generation_ids(self.tokenizer, messages)
        input_ids = torch.tensor([ids]).to(self.device)
        kwargs = dict(max_new_tokens=int(gen.get("max_new_tokens", 256)),
                      do_sample=(gen.get("temperature", 0) not in (0, None)),
                      pad_token_id=self.tokenizer.pad_token_id)
        if not kwargs["do_sample"]:
            kwargs["temperature"] = None
            kwargs["top_p"] = None
        if self.device == "cuda":
            torch.cuda.reset_peak_memory_stats()
        t0 = time.time()
        with torch.no_grad():
            out = self.model.generate(input_ids, **kwargs)
        elapsed = round(time.time() - t0, 3)
        new_tokens = out[0][len(ids):]
        self.last_gen_meta = {
            "prompt_tokens": len(ids), "generated_tokens": int(len(new_tokens)),
            "elapsed_s": elapsed,
            "cuda_peak_mb": (round(torch.cuda.max_memory_allocated() / 2**20, 1)
                             if self.device == "cuda" else None)}
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True)

    def unload(self):
        import gc
        import torch
        self.model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # ---- checkpoints ----
    def save_checkpoint(self, path, writer=None):
        import json
        import torch
        target = writer.resolve(path) if writer else _os_abspath(path)
        _os_makedirs(target)
        if self.target == "lora":
            self.model.save_pretrained(target)
            marker = {"checkpoint_type": "lora",
                      "base_model_path": self.cfg["model"].get("base_model_path"),
                      "base_model": self.cfg["model"].get("base_model"),
                      "base_model_revision": self.cfg["model"].get("base_model_revision")}
        else:
            torch.save(self.model.state_dict(), _os_join(target, "qat_state.pt"))
            marker = {"checkpoint_type": "ternary-qat",
                      "base_model_path": self.cfg["model"].get("base_model_path"),
                      "base_model": self.cfg["model"].get("base_model"),
                      "base_model_revision": self.cfg["model"].get("base_model_revision"),
                      "group_size": self.cfg.get("ternary_qat", {}).get("group_size", 128)}
        with open(_os_join(target, "lw-checkpoint.json"), "w", encoding="utf-8") as fh:
            json.dump(marker, fh, indent=2, sort_keys=True)
        return target


# small os shims so heavy imports stay inside methods
def _os_isdir(p):
    import os
    return bool(p) and os.path.isdir(p)


def _os_isfile(p):
    import os
    return os.path.isfile(p)


def _os_join(*a):
    import os
    return os.path.join(*a)


def _os_abspath(p):
    import os
    return os.path.abspath(p)


def _os_makedirs(p):
    import os
    os.makedirs(p, exist_ok=True)


def get_backend(name):
    return {"stub": StubBackend, "hf": HFBackend}[name]
