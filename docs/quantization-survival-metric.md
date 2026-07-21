# Quantization-Survival Metric — Specification

Defines a **difference-of-differences** metric that answers: *how much of the
behavioral change training produced actually survives packing to the Prism
deployment grid?* Run 1 showed conventional-LoRA change can vanish after ternary
Q2_0 reprojection; this metric turns "did it survive" into a number that Run 2/3
can be gated on. Reference scaffold: `experiments/scripts/measure_quant_survival.py`.

## Model states

| State | Meaning |
|---|---|
| `B_bf16` | untouched BF16 base |
| `T_bf16` | trained BF16 model (before packing) |
| `B_pack` | untouched **packed** model (Prism Q2_0 grid) |
| `T_pack` | trained **packed** model (Prism Q2_0 grid) |

"Packed" MUST mean the confirmed Prism grid (g128, ternary embeddings, tied
lm_head), evaluated on the Prism runtime — see
`experiments/results/prism-format-characterization.md`. Not upstream TQ2_0.

## Behavioral distances

For each evaluation example `i` (and token position where practical), collect the
next-token probability distribution from each state and compute a **symmetric**
divergence. Primary metric: **Jensen–Shannon divergence** (JSD, natural log,
bounded `[0, ln2]`):

```
JSD(p, q) = 0.5·KL(p‖m) + 0.5·KL(q‖m),   m = 0.5·(p+q)

D_bf16 = JSD(B_bf16, T_bf16)     # behavioral movement BEFORE packing
D_pack = JSD(B_pack, T_pack)     # behavioral movement AFTER packing

survival_ratio = D_pack / D_bf16
```

Raw trained pre/post-quant KL — `KL(T_bf16 ‖ T_pack)` — is recorded only as a
**secondary distortion diagnostic**, never as the headline (it conflates training
movement with quantization noise).

### Near-zero denominator policy

`D_bf16` near zero means "training barely moved behavior here," so the ratio is
undefined. With `eps = 1e-8` and a reporting threshold `near_zero = 1e-4`:
- per-example ratio is `NaN` when `D_bf16 < near_zero` (excluded from ratio stats),
  and the count of such examples is reported;
- a robust **global** figure `survival_ratio_of_means = mean(D_pack) / max(mean(D_bf16), eps)`
  is reported alongside the per-example distribution, because it does not divide
  small-by-small.

Interpretation: `≈1` behavior survived packing; `≈0` packing erased the training
change (the Run 1 finding); `>1` packing amplified/゚distorted behavior.

## Required outputs (future harness)

- global `D_bf16`, global `D_pack`, global survival ratio (of-means and
  per-example mean/median/std)
- per-task values (the four Run 1 tasks)
- per-example values; per-token-position where practical
- mean, median, standard deviation
- confidence interval across seeds (`aggregate_seeds`)
- denominator-near-zero count
- invalid/nonfinite count

### Behavioral task metrics (objective only)

Recorded next to the divergence, per task:
- structured-output exact accuracy (canon JSON parses + matches)
- constraint-violation classification accuracy
- focused-revision target similarity (e.g. normalized edit / token-F1 to the gold)
- fiction-compliance success vs refusal/moralizing rate (rule-based detector)

No subjective literary scoring is defined or implemented in this phase.

## Weight-space companion metrics

Behavioral survival should be explained by grid movement. Compute on the packed
ternary codes (base vs trained), per the Prism grid:

- **ternary-state flip rate** (fraction of weights whose code changed)
- **flip matrix**: counts for `-1→0, -1→1, 0→-1, 0→1, 1→0, 1→-1`
- flip rate **by layer** and **by module type** (attn q/k/v/o, mlp gate/up/down)
- **fraction of groups with no changed codes** (dead groups)
- **scale-change distribution** (per-group amax before vs after) and by layer/module
- **embedding flip rate** and **lm_head flip rate** (tied ⇒ shared; verify consistency)
- **tied-weight consistency** (embed and head codes identical when tied)
- **correlation** between per-layer flip rate and per-layer behavioral survival

## Three quantities that are NOT interchangeable

1. **Grid movement** — did the packed ternary codes/scales change (weight space)?
2. **Behavioral movement** — did output distributions change (JSD)?
3. **Quantization distortion** — how far packing moves a *fixed* model
   (`JSD(T_bf16, T_pack)`), independent of training.

A conventional-LoRA run can have large behavioral movement at BF16, near-zero
grid movement after packing, and therefore near-zero behavioral survival — which
is exactly Run 1. The harness must report all three so a low survival ratio can
be attributed to "codes didn't flip" rather than mis-measured.

## Scope of this dispatch

`measure_quant_survival.py` implements only the **format-independent** math over
pre-collected distributions (`.npz` of probs/logits for the four states + a
`tasks` array), plus `aggregate_seeds`. Model/runtime collection (producing the
four states, especially `*_pack` via the Prism runtime) is deferred to the next
dispatch, once the deployment grid — now confirmed — is wired in.
