import torch
from torch.autograd import Function


class RoundClampSTE(Function):
    """round_clamp(x, -1, 1) with straight-through estimator.

    Forward: round(x).clamp(-1, 1). Backward: identity (gradient flows
    through the non-differentiable round/clamp as ones). All weight
    ternarize ops route through this.
    """

    @staticmethod
    def forward(ctx, x):
        # fp32 round is exact; bf16 round drops precision in the scale divide
        orig_dtype = x.dtype
        x32 = x.float() if orig_dtype != torch.float32 else x
        return torch.round(x32).clamp_(-1, 1).to(orig_dtype)

    @staticmethod
    def backward(ctx, g):
        return g  # STE: identity


def round_clamp_ste(x):
    return RoundClampSTE.apply(x)


if __name__ == "__main__":
    torch.manual_seed(0)
    x = torch.randn(5, requires_grad=True)
    y = round_clamp_ste(x)
    assert set(torch.unique(y).tolist()) <= {-1.0, 0.0, 1.0}, y
    y.sum().backward()
    assert torch.allclose(x.grad, torch.ones_like(x)), x.grad
    assert round_clamp_ste(torch.zeros(3)).abs().sum() == 0
    print("ste ok")
