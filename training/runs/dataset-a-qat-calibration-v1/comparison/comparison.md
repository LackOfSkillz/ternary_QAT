# Dataset A smoke comparison

Base / LoRA / ternary-QAT on the same 7 held-out records. Diagnostic only;
NOT evidence of production quality.

| target | records | format_valid | backend |
|---|---|---|---|
| base | 7 | 6 | hf |
| lora | 7 | 5 | hf |
| ternary-qat | 7 | 6 | hf |

## Per-record format validity

| record | base | lora | ternary-qat |
|---|---|---|---|
| dsa-boundary-001 | ✓ | ✓ | ✓ |
| dsa-canon-003 | ✓ | ✓ | ✓ |
| dsa-constraint-002 | ✓ | ✗ | ✓ |
| dsa-revision-002 | ✗ | ✗ | ✗ |
| dsa-revision-007 | ✓ | ✓ | ✓ |
| dsa-revision-018 | ✓ | ✓ | ✓ |
| dsa-scene-002 | ✓ | ✓ | ✓ |

_Behavioral rubric scoring is recorded per record in each eval JSON for Gate review; this table is the mechanical format-validity summary only._
