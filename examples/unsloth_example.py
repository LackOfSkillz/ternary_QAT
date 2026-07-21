"""Unsloth LoRA example: ternary frozen base + FP LoRA adapters via unsloth.
pip install ternary unsloth transformers datasets trl
"""
import torch
from unsloth import FastModel
from datasets import load_dataset
from trl import SFTConfig, SFTTrainer
from ternary import swap_linear, TernaryConfig, ternarize_lora_params, reternarize_merged_linears

model, tokenizer = FastModel.from_pretrained(
    "prism-ml/Ternary-Bonsai-1.7B-unpacked", dtype=torch.bfloat16,
    max_seq_length=2048, load_in_4bit=False,
    use_gradient_checkpointing="unsloth",
)

# swap all linears + embed -> ternary g128
swap_linear(model, TernaryConfig(group_size=128))

# apply LoRA (r=4, small for example)
model = FastModel.get_peft_model(
    model, r=4, lora_alpha=8, lora_dropout=0, bias="none",
    random_state=3407,
)

n_train = sum(p.numel() for p in model.parameters() if p.requires_grad)
n_total = sum(p.numel() for p in model.parameters())
print(f"trainable: {n_train:,} / {n_total:,}")

# dataset
ds = load_dataset("mlabonne/FineTome-100k", split="train[:300]")

def tokenize(examples):
    texts = []
    for msgs in examples["conversations"]:
        # FineTome uses from/value with human/gpt roles; Qwen3 expects user/assistant
        role_map = {"human": "user", "gpt": "assistant", "system": "system"}
        msgs = [{"role": role_map[m["from"]], "content": m["value"]} for m in msgs]
        text = tokenizer.apply_chat_template(msgs, tokenize=False)
        texts.append(text)
    return tokenizer(texts, truncation=True, max_length=2048)

ds = ds.map(tokenize, batched=True, remove_columns=ds.column_names)

# train
trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,
    train_dataset=ds,
    args=SFTConfig(
        max_seq_length=2048, max_steps=300, completion_only_loss=True,
        per_device_train_batch_size=1,
        learning_rate=1e-3, optim="adamw_8bit", weight_decay=0,
        bf16=True, logging_steps=1,
        output_dir="./trainer_output", report_to="none",
        remove_unused_columns=False, dataset_num_proc=1,
    ),
)
trainer.train()

# save: ternarize LoRA params, merge, re-ternarize
n = ternarize_lora_params(model)
print(f"ternarized {n} LoRA params")

from peft import PeftModel
if isinstance(model, PeftModel):
    model = model.merge_and_unload()
    n2 = reternarize_merged_linears(model)
    print(f"merged + re-ternarized {n2} linears")

model.save_pretrained("./lora_example_output")
tokenizer.save_pretrained("./lora_example_output")
print("saved to ./lora_example_output")
