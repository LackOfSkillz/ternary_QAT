"""Shared message formatting + assistant-only loss masking (Parts 2 & 3).

One formatter is used by training, base/LoRA/QAT evaluation, and reload checks, so
the same row produces the same prompt everywhere. Prefers the tokenizer chat
template; falls back to an explicit, versioned format only when no compatible chat
template exists.
"""
FALLBACK_FORMAT_VERSION = "linewright-fallback-v1"


class MaskingError(Exception):
    pass


def _fallback_prompt(messages, add_generation_prompt):
    parts = []
    for m in messages:
        role = m["role"].capitalize()
        parts.append(f"{role}: {m['content']}")
    text = "\n\n".join(parts)
    if add_generation_prompt:
        text += "\n\nAssistant:"
    return text


def has_chat_template(tokenizer):
    return bool(getattr(tokenizer, "chat_template", None))


def render_prompt_text(tokenizer, messages, add_generation_prompt=True):
    """Return (text, used_chat_template). Never invents a new format silently."""
    if has_chat_template(tokenizer):
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=add_generation_prompt)
        return text, True
    return _fallback_prompt(messages, add_generation_prompt), False


def _template_ids(tokenizer, messages, add_generation_prompt):
    """Token ids from the chat template, robust to the transformers return type
    (list[int], tensor, dict, or rendered-string)."""
    out = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=add_generation_prompt)
    if isinstance(out, str):                       # some versions return rendered text
        out = tokenizer(out, add_special_tokens=False)["input_ids"]
    elif hasattr(out, "input_ids"):                # BatchEncoding (UserDict, not dict)
        out = out.input_ids
    elif isinstance(out, dict):
        out = out["input_ids"]
    if hasattr(out, "tolist"):
        out = out.tolist()
    if out and isinstance(out[0], (list, tuple)):
        out = out[0]
    return [int(x) for x in out]


def build_generation_ids(tokenizer, messages):
    """Token ids for a generation prompt (system+user, assistant to be produced)."""
    if has_chat_template(tokenizer):
        return _template_ids(tokenizer, messages, add_generation_prompt=True)
    text, _ = render_prompt_text(tokenizer, messages, add_generation_prompt=True)
    return list(tokenizer(text, add_special_tokens=True)["input_ids"])


def build_training_example(tokenizer, messages, max_length, truncation="right"):
    """Assistant-only completion masking (Part 3).

    Returns dict with input_ids, labels, and per-example counts. Prompt (system +
    user) and padding tokens get label -100; only assistant target tokens keep
    labels. Raises MaskingError on the failure modes in Part 3.
    """
    assert messages[-1]["role"] == "assistant", "last message must be assistant"
    prompt_msgs = messages[:-1]
    prompt_ids = build_generation_ids(tokenizer, prompt_msgs)

    if has_chat_template(tokenizer):
        full_ids = _template_ids(tokenizer, messages, add_generation_prompt=False)
    else:
        prompt_text, _ = render_prompt_text(tokenizer, prompt_msgs, add_generation_prompt=True)
        full_text = prompt_text + " " + messages[-1]["content"]
        if tokenizer.eos_token:
            full_text += tokenizer.eos_token
        full_ids = tokenizer(full_text, add_special_tokens=True)["input_ids"]
    full_ids = list(full_ids)

    prompt_len = len(prompt_ids)
    if prompt_len >= len(full_ids):
        raise MaskingError("assistant target boundary not found (prompt >= full)")

    truncated = 0
    if len(full_ids) > max_length:
        if truncation != "right":
            raise MaskingError(f"sequence exceeds max_length with no declared "
                               f"truncation policy ({len(full_ids)} > {max_length})")
        truncated = len(full_ids) - max_length
        full_ids = full_ids[:max_length]
        if prompt_len >= len(full_ids):
            raise MaskingError("assistant tokens entirely truncated")

    labels = [-100] * len(full_ids)
    for i in range(prompt_len, len(full_ids)):
        labels[i] = full_ids[i]

    if all(l == -100 for l in labels):
        raise MaskingError("every label is -100 (no assistant target)")
    if any(l != -100 for l in labels[:prompt_len]):
        raise MaskingError("prompt tokens are not fully masked")

    target_tokens = sum(1 for l in labels if l != -100)
    if target_tokens == 0:
        raise MaskingError("assistant target retains no labels")

    return {
        "input_ids": full_ids,
        "labels": labels,
        "input_token_count": len(full_ids),
        "prompt_token_count": prompt_len,
        "target_token_count": target_tokens,
        "masked_token_count": len(full_ids) - target_tokens,
        "truncated_token_count": truncated,
        "used_chat_template": has_chat_template(tokenizer),
    }


def collate_batch(tokenizer, examples, pad_token_id):
    """Right-pad a list of build_training_example dicts into batch tensors.
    Padding positions get label -100 (masked)."""
    import torch
    max_len = max(len(e["input_ids"]) for e in examples)
    input_ids, labels, attn = [], [], []
    for e in examples:
        pad = max_len - len(e["input_ids"])
        input_ids.append(e["input_ids"] + [pad_token_id] * pad)
        labels.append(e["labels"] + [-100] * pad)
        attn.append([1] * len(e["input_ids"]) + [0] * pad)
    return {"input_ids": torch.tensor(input_ids),
            "labels": torch.tensor(labels),
            "attention_mask": torch.tensor(attn)}
