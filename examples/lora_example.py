"""
LoRA example: ternary frozen base + FP LoRA adapters.
pip install ternary peft transformers datasets
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from datasets import load_dataset
from ternary import swap_linear, TernaryConfig, ternarize_lora_params, reternarize_merged_linears

model = AutoModelForCausalLM.from_pretrained(
    "prism-ml/Ternary-Bonsai-1.7B-unpacked", dtype=torch.bfloat16,
)
tokenizer = AutoTokenizer.from_pretrained("prism-ml/Ternary-Bonsai-1.7B-unpacked")

# swap all linears + embed -> ternary g128
swap_linear(model, TernaryConfig(group_size=128))

# apply LoRA (r=4, small for example)
model = get_peft_model(model, LoraConfig(
    r=4, lora_alpha=8, lora_dropout=0, bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
))
model.gradient_checkpointing_enable()

n_train = sum(p.numel() for p in model.parameters() if p.requires_grad)
n_total = sum(p.numel() for p in model.parameters())
print(f"trainable: {n_train:,} / {n_total:,}")

# dataset
ds = load_dataset("mlabonne/FineTome-100k", split="train[:300]")

def tokenize(examples):
    role_map = {"human": "user", "gpt": "assistant", "system": "system"}
    results = {"input_ids": [], "attention_mask": [], "labels": []}
    for msgs in examples["conversations"]:
        msgs = [{"role": role_map[m["from"]], "content": m["value"]} for m in msgs]
        full_text = tokenizer.apply_chat_template(msgs, tokenize=False)
        prompt_text = tokenizer.apply_chat_template(
            msgs[:-1], tokenize=False, add_generation_prompt=True)
        full = tokenizer(full_text, truncation=True, max_length=2048)
        prompt_len = len(tokenizer(prompt_text)["input_ids"])
        labels = [-100] * min(prompt_len, 2048) + full["input_ids"][min(prompt_len, 2048):]
        results["input_ids"].append(full["input_ids"])
        results["attention_mask"].append(full["attention_mask"])
        results["labels"].append(labels)
    return results

ds = ds.map(tokenize, batched=True, remove_columns=ds.column_names)

# ternary QAT needs a higher LR than FP training
opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.0)

for step, batch in enumerate(ds):
    ids = torch.tensor(batch["input_ids"], dtype=torch.long).unsqueeze(0).to(model.device)
    mask = torch.tensor(batch["attention_mask"], dtype=torch.long).unsqueeze(0).to(model.device)
    labels = torch.tensor(batch["labels"], dtype=torch.long).unsqueeze(0).to(model.device)
    out = model(ids, attention_mask=mask, labels=labels)
    loss = out.loss
    opt.zero_grad(); loss.backward(); opt.step()
    print(f"  step {step}: loss={loss.item():.4f}")

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
