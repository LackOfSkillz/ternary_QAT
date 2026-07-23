# Comprehension vs execution (Dispatch 28B)

- Probes: 6
- Grid: {'pass_pass': 2, 'fail_fail': 0, 'pass_fail': 4, 'fail_pass': 0}
- Interpretation: 4 task(s) understood but not executed -> execution-discipline failure; 2 task(s) understood and executed

| task | comprehension | execution (P1) | cell |
|---|---|---|---|
| cn-01 | True | True | pass_pass |
| fr-01 | True | False | pass_fail |
| fr-04 | True | False | pass_fail |
| fr-07 | True | False | pass_fail |
| pt-01 | True | True | pass_pass |
| sp-01 | True | False | pass_fail |