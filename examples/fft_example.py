"""
Full-finetune (FFT) example: ternary QAT on all weights.
pip install ternary transformers datasets
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset
from ternary import swap_linear, TernaryConfig

model = AutoModelForCausalLM.from_pretrained(
    "prism-ml/Ternary-Bonsai-1.7B-unpacked", dtype=torch.bfloat16,
)
tokenizer = AutoTokenizer.from_pretrained("prism-ml/Ternary-Bonsai-1.7B-unpacked")

# swap all linears + embed -> ternary g128
swap_linear(model, TernaryConfig(group_size=128))
model.gradient_checkpointing_enable()

n_total = sum(p.numel() for p in model.parameters())
print(f"params: {n_total:,}")

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

opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.0)

for step, batch in enumerate(ds):
    ids = torch.tensor(batch["input_ids"], dtype=torch.long).unsqueeze(0).to(model.device)
    mask = torch.tensor(batch["attention_mask"], dtype=torch.long).unsqueeze(0).to(model.device)
    labels = torch.tensor(batch["labels"], dtype=torch.long).unsqueeze(0).to(model.device)
    out = model(ids, attention_mask=mask, labels=labels)
    loss = out.loss
    opt.zero_grad(); loss.backward(); opt.step()
    print(f"  step {step}: loss={loss.item():.4f}")

model.save_pretrained("./fft_example_output")
tokenizer.save_pretrained("./fft_example_output")
print("saved to ./fft_example_output")
