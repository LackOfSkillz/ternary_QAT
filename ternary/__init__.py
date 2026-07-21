from dataclasses import dataclass
from ternary.ste import RoundClampSTE, round_clamp_ste
from ternary.linear import TernaryLinear, ternarize_weight, GROUP_SIZE
from ternary.swap import (TernaryEmbedding, swap_linear,
                          ternarize_lora_params, reternarize_merged_linears)


@dataclass
class TernaryConfig:
    group_size: int = GROUP_SIZE  # 128 (paper default) or 64


__all__ = ["TernaryConfig", "TernaryLinear", "TernaryEmbedding", "swap_linear",
           "ternarize_lora_params", "reternarize_merged_linears", "GROUP_SIZE",
           "RoundClampSTE", "round_clamp_ste", "ternarize_weight"]
