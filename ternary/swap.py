import torch
import torch.nn as nn
from .linear import TernaryLinear, ternarize_weight, GROUP_SIZE


class TernaryEmbedding(nn.Embedding):
    """nn.Embedding with g128 ternary fake-quant on the weight (Bonsai format).

    Paper quantizes embeddings too. Subclasses nn.Embedding so HF internals
    (resize_token_embeddings etc.) keep working.
    """

    def __init__(self, weight, group_size=GROUP_SIZE):
        super().__init__(weight.shape[0], weight.shape[1])
        self.weight = nn.Parameter(weight.detach().clone())
        self.group_size = group_size

    def forward(self, x):
        # x is int64 indices; weight stays FP — embedding is a gather, not a matmul
        w_q = ternarize_weight(self.weight, self.group_size)
        return torch.nn.functional.embedding(
            x, w_q, self.padding_idx, self.max_norm,
            self.norm_type, self.scale_grad_by_freq, self.sparse)


# don't ternarize norms (tiny, paper keeps them FP)
_EXCLUDE_SUBSTR = ("norm", "q_norm", "k_norm")


def _should_swap(name, mod):
    if not isinstance(mod, nn.Linear) or isinstance(mod, TernaryLinear):
        return False  # TernaryLinear IS an nn.Linear; don't double-swap
    return not any(s in name for s in _EXCLUDE_SUBSTR)


def swap_linear(model, cfg=None):
    """Swap nn.Linear -> TernaryLinear (incl. lm_head) and embed_tokens ->
    TernaryEmbedding, per the Bonsai paper (embeddings, attn, MLP, lm_head
    all ternary; norms stay FP). group_size from cfg (128 paper, 64 finer).
    Mutates model in place; call before building the optimizer / Trainer.
    """
    gs = getattr(cfg, "group_size", GROUP_SIZE) if cfg else GROUP_SIZE
    for name, mod in list(model.named_modules()):
        for child_name, child in list(mod.named_children()):
            full = f"{name}.{child_name}" if name else child_name
            if isinstance(child, nn.Embedding) and not isinstance(child, TernaryEmbedding) \
                    and "embed" in full:
                setattr(mod, child_name, TernaryEmbedding(child.weight, gs))
            elif _should_swap(full, child):
                setattr(mod, child_name, TernaryLinear(child.weight, getattr(child, "bias", None), gs))
    return None


def ternarize_lora_params(model, group_size=GROUP_SIZE):
    """In-place ternarize LoRA A/B params of every peft LoraLayer (g128).

    Runs at save time (after training). Guarded by clamp(min=1e-8) inside
    ternarize_weight so lora_B's zero-init rows ternarize to ~0 safely.
    Duck-typed: any module with lora_A/lora_B ModuleDicts gets walked.
    Returns count of params touched.
    """
    n = 0
    for mod in model.modules():
        lora_A = getattr(mod, "lora_A", None)
        lora_B = getattr(mod, "lora_B", None)
        if lora_A is None and lora_B is None:
            continue
        for container in (lora_A, lora_B):
            if container is None:
                continue
            for layer in container.values():
                w = getattr(layer, "weight", None)
                if w is None or w.shape[-1] % group_size:
                    continue
                with torch.no_grad():
                    w.copy_(ternarize_weight(w, group_size))
                n += 1
    return n


def reternarize_merged_linears(model):
    """After LoRA merge, snap every TernaryLinear/TernaryEmbedding weight
    back onto the g128 grid so the saved artifact is actually ternary."""
    n = 0
    for mod in model.modules():
        if type(mod).__name__ in ("TernaryLinear", "TernaryEmbedding"):
            with torch.no_grad():
                mod.weight.copy_(ternarize_weight(mod.weight, mod.group_size))
            n += 1
    return n
