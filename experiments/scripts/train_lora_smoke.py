#!/usr/bin/env python3
"""Run 1 conventional-LoRA smoke training.

Standard Transformers + PEFT + Trainer. NO Unsloth, TRL, bitsandbytes,
FlashAttention, or ternary swap_linear(). This is the conventional-LoRA
baseline that proves the training loop mechanically.

Assistant-only loss IS implemented: the chat prompt (system + user) is masked
to -100 and loss is computed only on the assistant response tokens.

Usage:
  python train_lora_smoke.py --config experiments/configs/run001-lora-smoke.yaml
  python train_lora_smoke.py --config ... --dry-run
  python train_lora_smoke.py --config ... --resume-from-checkpoint auto|<path>
"""
import argparse
import glob
import json
import os
import shutil
import sys

import torch
import yaml
from transformers import (AutoModelForCausalLM, AutoTokenizer, Trainer,
                          TrainingArguments)
from peft import LoraConfig, get_peft_model


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_examples(path, tokenizer, max_len):
    """Return list of {input_ids, attention_mask, labels} with assistant-only labels."""
    examples = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            user = r["instruction"]
            if r.get("context"):
                user = f"{user}\n\n{r['context']}"
            msgs = [
                {"role": "system", "content": r["system"]},
                {"role": "user", "content": user},
                {"role": "assistant", "content": r["response"]},
            ]
            # Render to text then tokenize (robust across transformers versions).
            full_text = tokenizer.apply_chat_template(
                msgs, tokenize=False, add_generation_prompt=False)
            prompt_text = tokenizer.apply_chat_template(
                msgs[:-1], tokenize=False, add_generation_prompt=True)
            full = tokenizer(full_text, add_special_tokens=False)["input_ids"]
            prompt = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
            # assistant-only masking: prompt should be a prefix of full
            plen = len(prompt)
            if full[:plen] != prompt:
                # defensive fallback: if not a clean prefix, mask nothing extra
                plen = 0
            labels = [-100] * plen + full[plen:]
            full = full[:max_len]
            labels = labels[:max_len]
            if all(t == -100 for t in labels):
                continue  # nothing to learn from
            examples.append({
                "input_ids": full,
                "attention_mask": [1] * len(full),
                "labels": labels,
            })
    return examples


class PadCollator:
    def __init__(self, pad_id):
        self.pad_id = pad_id

    def __call__(self, batch):
        maxlen = max(len(b["input_ids"]) for b in batch)
        ids, masks, labels = [], [], []
        for b in batch:
            n = maxlen - len(b["input_ids"])
            ids.append(b["input_ids"] + [self.pad_id] * n)
            masks.append(b["attention_mask"] + [0] * n)
            labels.append(b["labels"] + [-100] * n)
        return {
            "input_ids": torch.tensor(ids, dtype=torch.long),
            "attention_mask": torch.tensor(masks, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def matched_lora_modules(model):
    suffixes = set()
    count = 0
    for name, mod in model.named_modules():
        if hasattr(mod, "lora_A"):
            count += 1
            suffixes.add(name.split(".")[-1])
    return sorted(suffixes), count


def build_model_and_tok(cfg):
    model_path = cfg["model"]["base_model_path"]
    tok = AutoTokenizer.from_pretrained(model_path)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        dtype=torch.bfloat16,
        attn_implementation="sdpa",
        low_cpu_mem_usage=True,
        device_map={"": 0},
    )
    model.config.use_cache = False
    lc = cfg["lora"]
    lora = LoraConfig(
        r=lc["rank"], lora_alpha=lc["alpha"], lora_dropout=lc["dropout"],
        target_modules=lc["target_modules"], bias="none", task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)
    if cfg["optimization"].get("gradient_checkpointing", True):
        model.enable_input_require_grads()
    return model, tok


def resolve_resume(arg, output_dir):
    if not arg:
        return None
    if arg in ("auto", "latest"):
        cks = glob.glob(os.path.join(output_dir, "checkpoint-*"))
        if not cks:
            return None
        return max(cks, key=lambda p: int(p.rsplit("-", 1)[-1]))
    return arg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume-from-checkpoint", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    seed = cfg["reproducibility"]["seed"]
    torch.manual_seed(seed)
    max_len = cfg["sequence"]["max_seq_length"]
    opt = cfg["optimization"]
    out_dir = cfg["paths"]["output_dir"]
    log_dir = cfg["paths"].get("logging_dir", os.path.join(out_dir, "logs"))

    print(f"=== Run 1 LoRA smoke ({'DRY-RUN' if args.dry_run else 'TRAIN'}) ===")
    print("torch:", torch.__version__, "| cuda avail:", torch.cuda.is_available())

    model, tok = build_model_and_tok(cfg)
    suffixes, n_adapters = matched_lora_modules(model)
    print("matched LoRA target-module suffixes:", suffixes, "| adapter layers:", n_adapters)
    model.print_trainable_parameters()

    train_ex = build_examples(cfg["dataset"]["train_path"], tok, max_len)
    eval_ex = build_examples(cfg["dataset"]["eval_path"], tok, max_len)
    print(f"train examples: {len(train_ex)} | eval examples: {len(eval_ex)}")
    collator = PadCollator(tok.pad_token_id)

    if args.dry_run:
        print("=== DRY-RUN: tokenize 3 examples + one forward/backward step ===")
        for e in train_ex[:3]:
            print(f"  ex len={len(e['input_ids'])} "
                  f"trained_tokens={sum(1 for t in e['labels'] if t != -100)}")
        batch = collator(train_ex[:1])
        batch = {k: v.to("cuda") for k, v in batch.items()}
        model.train()
        out = model(**batch)
        loss = out.loss
        loss.backward()
        finite = bool(torch.isfinite(loss))
        print(f"dry-run loss: {loss.item():.4f} | finite: {finite}")
        print(f"peak mem (GB): {round(torch.cuda.max_memory_allocated()/1e9, 3)}")
        model.zero_grad(set_to_none=True)
        # no checkpoints/outputs written by dry-run; nothing to clean
        print("DRY-RUN OK" if finite else "DRY-RUN FAILED")
        sys.exit(0 if finite else 1)

    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    targs = TrainingArguments(
        output_dir=out_dir,
        logging_dir=log_dir,
        per_device_train_batch_size=opt["micro_batch_size"],
        per_device_eval_batch_size=opt["micro_batch_size"],
        gradient_accumulation_steps=opt["gradient_accumulation_steps"],
        max_steps=opt["max_steps"],
        learning_rate=float(opt["learning_rate"]),
        bf16=(opt.get("precision", "bf16") == "bf16"),
        gradient_checkpointing=opt.get("gradient_checkpointing", True),
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim=opt.get("optimizer", "adamw_torch"),
        lr_scheduler_type=opt.get("lr_scheduler", "cosine"),
        warmup_ratio=opt.get("warmup_ratio", 0.03),
        logging_steps=cfg["intervals"]["logging_interval_steps"],
        save_steps=cfg["intervals"]["checkpoint_interval_steps"],
        eval_strategy="steps",
        eval_steps=cfg["intervals"]["eval_interval_steps"],
        seed=seed,
        dataloader_num_workers=0,
        report_to="none",
    )
    trainer = Trainer(
        model=model, args=targs,
        train_dataset=train_ex, eval_dataset=eval_ex,
        data_collator=collator,
    )
    resume = resolve_resume(args.resume_from_checkpoint, out_dir)
    print("resume_from_checkpoint:", resume)
    trainer.train(resume_from_checkpoint=resume)
    trainer.save_model(out_dir)
    tok.save_pretrained(out_dir)
    print("=== TRAINING COMPLETE ===")
    print("adapter saved to:", out_dir)
    print("peak mem (GB):", round(torch.cuda.max_memory_allocated()/1e9, 3))


if __name__ == "__main__":
    main()
