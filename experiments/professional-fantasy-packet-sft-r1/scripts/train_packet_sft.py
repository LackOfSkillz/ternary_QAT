"""Dispatch 30G — controlled Qwen3-8B LoRA SFT for one arm (atomic OR compositional).

Recipe = the repo's validated qwen3-8b-lora-pilot-v1 (Dispatch 27B) EXCEPT MAXLEN raised 2048->8192
(our gold targets need it; truncation is forbidden) and gradient checkpointing enabled to fit the
longer sequences. IDENTICAL settings for both arms; only the input dataset differs.

Runs inside linewright-ternary-train:d26 on the GX10. NON-THINKING enforced. Completion-only loss.

Env:
  ARM   = atomic | compositional         (selects /work/<arm>/train.jsonl and /work/<arm>/lora-out)
  SMOKE = 1  -> 5 optimizer steps, no checkpoints, no final save (dataset/mask/fwd/bwd/finite check)
"""
import json, os, hashlib, time
import torch
from transformers import (AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments,
                          TrainerCallback)
from peft import LoraConfig, get_peft_model

QWEN = "/hf/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218"
ARM = os.environ.get("ARM", "atomic")
SMOKE = os.environ.get("SMOKE") == "1"
WORK = "/work"
RECS = f"{WORK}/{ARM}/train.jsonl"
OUT = f"{WORK}/{ARM}/lora-out"
SEED = 20260722
MAXLEN = 8192

torch.manual_seed(SEED)
tok = AutoTokenizer.from_pretrained(QWEN)
if tok.pad_token_id is None:
    tok.pad_token = tok.eos_token

recs = [json.loads(l) for l in open(RECS, encoding="utf-8") if l.strip()]


def encode(r):
    msgs = [{"role": "system", "content": r["system"]}, {"role": "user", "content": r["prompt"]}]
    enc = tok.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False, tokenize=True)
    prompt_ids = enc["input_ids"] if hasattr(enc, "keys") else enc
    if prompt_ids and isinstance(prompt_ids[0], list):
        prompt_ids = prompt_ids[0]
    gold = tok(r["gold_output"], add_special_tokens=False)["input_ids"] + [tok.eos_token_id]
    ids = (prompt_ids + gold)[:MAXLEN]
    labels = ([-100] * len(prompt_ids) + gold)[:MAXLEN]
    return {"input_ids": ids, "labels": labels, "attention_mask": [1] * len(ids),
            "_prompt_len": len(prompt_ids), "_gold_len": len(gold), "_total": len(prompt_ids) + len(gold)}


enc = [encode(r) for r in recs]
# integrity: completion-only mask (all prompt tokens masked, >=1 gold token unmasked), eos present, no truncation
mask_ok = all(all(x == -100 for x in e["labels"][:e["_prompt_len"]]) and
              any(x != -100 for x in e["labels"][e["_prompt_len"]:]) for e in enc)
eos_ok = all(e["input_ids"][min(e["_total"], MAXLEN) - 1] == tok.eos_token_id for e in enc)
no_trunc = all(e["_total"] <= MAXLEN for e in enc)
print(f"[{ARM}] records={len(enc)} mask_ok={mask_ok} eos_ok={eos_ok} no_truncation={no_trunc} "
      f"total_range=[{min(e['_total'] for e in enc)},{max(e['_total'] for e in enc)}]", flush=True)
assert mask_ok and eos_ok and no_trunc, "serialization integrity failed"
train = [{k: v for k, v in e.items() if not k.startswith("_")} for e in enc]


class Coll:
    def __call__(self, feats):
        m = max(len(f["input_ids"]) for f in feats)
        def pad(x, v): return x + [v] * (m - len(x))
        import torch as T
        return {"input_ids": T.tensor([pad(f["input_ids"], tok.pad_token_id) for f in feats]),
                "attention_mask": T.tensor([pad(f["attention_mask"], 0) for f in feats]),
                "labels": T.tensor([pad(f["labels"], -100) for f in feats])}


model = AutoModelForCausalLM.from_pretrained(QWEN, torch_dtype=torch.bfloat16, device_map="cuda")
model.config.use_cache = False
model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
model.enable_input_require_grads()
lcfg = LoraConfig(r=16, lora_alpha=16, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
                  target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
model = get_peft_model(model, lcfg)
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"[{ARM}] trainable params: {trainable}", flush=True)

meta = []


class MetaCb(TrainerCallback):
    def on_save(self, args, state, control, **kw):
        step = state.global_step
        ex = step * args.per_device_train_batch_size * args.gradient_accumulation_steps
        ck = os.path.join(OUT, f"checkpoint-{step}", "adapter_model.safetensors")
        h = hashlib.sha256(open(ck, "rb").read()).hexdigest() if os.path.exists(ck) else None
        last = {k: v for lg in state.log_history for k, v in lg.items()}
        meta.append({"optimizer_step": step, "examples_seen": ex,
                     "estimated_dataset_passes": round(ex / len(train), 2),
                     "training_loss": last.get("loss"), "learning_rate": last.get("learning_rate"),
                     "grad_norm": last.get("grad_norm"), "adapter_hash": h})
        json.dump(meta, open(os.path.join(OUT, "checkpoint-meta.json"), "w"), indent=1)
        print(f"[{ARM} ckpt {step}] ex={ex} loss={last.get('loss')} gnorm={last.get('grad_norm')} "
              f"adapter={h[:12] if h else None}", flush=True)


common = dict(output_dir=OUT, per_device_train_batch_size=2, gradient_accumulation_steps=1,
              learning_rate=1e-5, lr_scheduler_type="cosine", warmup_ratio=0.03, weight_decay=0.0,
              max_grad_norm=1.0, bf16=True, logging_steps=1, seed=SEED, report_to=[],
              dataloader_num_workers=0, remove_unused_columns=False, gradient_checkpointing=False,
              disable_tqdm=True)
if SMOKE:
    args = TrainingArguments(max_steps=5, save_strategy="no", **common)
else:
    args = TrainingArguments(num_train_epochs=1, save_steps=3, save_strategy="steps",
                             save_total_limit=30, **common)
tr = Trainer(model=model, args=args, train_dataset=train, data_collator=Coll(), callbacks=[MetaCb()])
t0 = time.time()
out = tr.train()
finite = all(v == v and abs(v) != float("inf") for lg in tr.state.log_history for v in
             [lg.get("loss", 0.0), lg.get("grad_norm", 0.0)])
peak = torch.cuda.max_memory_allocated() / 1e9
if SMOKE:
    losses = [lg["loss"] for lg in tr.state.log_history if "loss" in lg]
    print("SMOKE_DONE", json.dumps({"arm": ARM, "steps": len(losses), "finite_loss": finite,
          "first_loss": losses[0] if losses else None, "last_loss": losses[-1] if losses else None,
          "peak_gb": round(peak, 2), "oom": False}), flush=True)
else:
    model.save_pretrained(os.path.join(OUT, "final"))
    fh = hashlib.sha256(open(os.path.join(OUT, "final", "adapter_model.safetensors"), "rb").read()).hexdigest()
    losses = [lg["loss"] for lg in tr.state.log_history if "loss" in lg]
    summary = {"arm": ARM, "trainable_params": trainable, "train_records": len(train),
               "seed": SEED, "lr": 1e-5, "rank": 16, "alpha": 16, "max_length": MAXLEN,
               "epochs": 1, "per_device_batch": 2, "grad_accum": 1, "grad_checkpointing": True,
               "base_revision": "b968826d9c46dd6066d109eabc6255188de91218", "thinking": "disabled",
               "completion_only_loss": True, "train_seconds": round(time.time() - t0, 1),
               "peak_gpu_gb": round(peak, 2), "steps": tr.state.global_step,
               "train_loss_start": losses[0] if losses else None, "train_loss_end": losses[-1] if losses else None,
               "min_loss": min(losses) if losses else None, "final_adapter_hash": fh,
               "n_checkpoints": len(meta), "finite_throughout": finite}
    json.dump(summary, open(os.path.join(OUT, "training-summary.json"), "w"), indent=1)
    print("TRAIN_DONE", json.dumps({"arm": ARM, "steps": summary["steps"], "seconds": summary["train_seconds"],
          "peak_gb": summary["peak_gpu_gb"], "loss": [summary["train_loss_start"], summary["train_loss_end"]],
          "final": fh[:12]}), flush=True)
