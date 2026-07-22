# Blind reviewer packets — Dataset A.2 pilot (Dispatch 21, Phase G)

Each `packet-<record_id>.json` is identity-free: candidates are labeled Candidate A/B/... in a deterministic, content-derived order that cannot leak identity. The packet never names base/LoRA/QAT, checkpoint step, loss, or gate scores.

## Workflow
1. Three reviewers (Aedan, Claude, ChatGPT) score every candidate on the 1-5 dimensions **independently**, choose an overall preference, and flag any fatal flaw — before any discussion.
2. Only after a reviewer locks their scores is `keys.json` consulted to un-blind candidate identity and reveal the mechanical gate summary.
3. Advancement is decided by `linewright/evaluation/advancement.py`: all three must prefer the candidate over base, zero fatal flags, zero schema/no-change/memorization/material regressions. A single fatal flag blocks advancement even if the other two approve; disagreement is investigated, not averaged.

NOTE: Dispatch 21 does not train. These packets use the pilot's own authored responses as stand-in candidates to exercise the workflow; real packets will draw candidates from a future training run.
