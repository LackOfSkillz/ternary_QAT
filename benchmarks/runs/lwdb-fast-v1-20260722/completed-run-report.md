# Fast Battery v1 — First Live Dual-GX10 Run: Completed Report (Dispatch 24)

**The live base-vs-candidate execution ran.** Both real models completed the frozen fast
battery on the two GX10 systems, in `parallel_multi_host`. This supersedes
`preliminary-report.md`. Findings are **preliminary and instrument-valid**; the advancement
decision is **deferred to Dispatch 25**. No winner, capability floor, or release claim is made.

> Experimental only. Two experimental smoke checkpoints on a 20-item first battery do not
> establish general quality.

## Execution

| | |
|---|---|
| run_id | `lwdb-fast-v1-20260722` |
| plan_hash | `a726365ad640…` (verified; unchanged) |
| execution_mode | `parallel_multi_host` (both nodes concurrent) |
| target_base | prism-ml/Ternary-Bonsai-4B-unpacked @ **gx10-9141** |
| new_candidate | base + LoRA step-20 @ **gx10-5611** (QAT-20 excluded) |
| env (both nodes) | `linewright-ternary-train:run001` — torch 2.10, transformers 5.14.1, peft 0.19.1 |
| jobs | **40 / 40 completed**, 0 failed, 0 missing, 0 retried, 0 interrupted |
| integrity | **0 problems** (output/prompt/contract/settings hashes verified; roles routed correctly) |
| token-cap hits | base 3, candidate 9 |

Provisioning: the candidate host was provisioned over the 192.168.10.0/24 jumbo link (image
19.7 GB, base model 7.6 GB, LoRA-20 adapter hash-verified MATCH). Both endpoints passed a
non-benchmark `READY` health check before the run.

## Instrument validity

| check | result |
|---|---|
| mechanical replay identical | **true** (every deterministic gate re-scored identically) |
| calibration set valid | true (dogfoods the gates, Dispatch 23) |
| **instrument_valid** | **true → findings are trusted** |

## Mechanical results (per model role)

| role | mechanical pass /20 | top failure labels |
|---|---|---|
| target_base | **9** | invalid_json 4, prose_outside_structure 4, incomplete_output 3, runaway_length 3, omitted_required_change 3, truncated_structure 3 |
| new_candidate | **5** | incomplete_output 9, low_lexical_diversity 9, repeated_ngram 9, duplicate_sentence 8, runaway_length 7, omitted_required_change 3 |

Both models are weak — the base struggles with structured-output protocol (JSON/YAML shape,
no-change wrapper), and the candidate additionally **degenerates**.

## Module J slop (per model role)

| role | severity distribution | corpus summary |
|---|---|---|
| target_base | none 9, inconclusive 7, low 2, high 1, **severe 1** | `corpus-summaries/target_base.json` |
| new_candidate | none 2, inconclusive 9, **severe 9** | `corpus-summaries/new_candidate.json` |

Slop thresholds remain **unvalidated**; semantic detectors **interface-only**. The severe
verdicts are driven by the justified Dispatch-21 repetition gate (repeated n-grams, low
lexical diversity, duplicate sentences), with evidence spans retained per report.

## Preliminary matched-pair signals (hypotheses, not verdicts)

- **Surface pair (F, bare↔compiled):** the base passes **both** arms (no slop); the candidate
  fails **both** (severe, token-capped). Because the split is the same across surfaces, the
  candidate's failure is **model/training, not the context compiler** — no context-compiler
  diagnosis is warranted.
- **Length pair (A, short↔long) & stability (I):** the candidate hits severe degeneration and
  the token cap on both length arms and the long stability item; the base only degrades on the
  long arm. Signal: **long-horizon degeneration is worse for the candidate** (consistent with
  the Dispatch-20 overfitting evidence).
- **Canon pair (D, extract↔apply):** the candidate degenerates on both; the base cleanly
  applies canon (`canon-apply` pass/none) but fails to extract clean JSON (`invalid_json`).
- **Restraint / no-change (C, E):** both fail the structured no-change and revision-wrapper
  protocol — a shared capability gap, not a candidate regression.
- **Refusal (H):** both produced non-empty prose on the ordinary and the harmful-disguised
  items; whether the harmful item was correctly **declined** is a reviewer judgement (seeded
  for blind review), not decided mechanically.

## Blind review

- **44 absolute review units** (40 outputs + **4 hidden grader-calibration seeds**,
  indistinguishable), identity-stripped, content-shuffled — **0 identity leaks**.
- **20 pairwise packets** (base-vs-candidate per item), candidate labels shuffled per item.
- Independent-review status: **pending** — the implementation agent knows model placement, so
  its judgment is **not** a blind independent review; the three-reviewer + Gary blind pass is
  future work.

## What this establishes / does not

Establishes: the first **trustworthy, instrument-valid, blind-ready dual-GX10 run** produced
comparable base-vs-candidate evidence. Preliminary signal: the LoRA-20 candidate **degenerates
markedly more** than the untouched base (severe slop 9 vs 1; token-cap 9 vs 3; both surface
arms fail), while both share a structured-protocol weakness.

Does **not** establish: a winner, a capability floor, a dataset-change direction, or release
readiness. Per the dispatch, the advancement decision is **deferred to Dispatch 25**, after the
diagnostic-engine validation and a blind human/independent review.

## Artifacts

Committed: this report, `completed-run-summary.json`, `item-level-results.json` (compact
per-item verdicts + hashes), `corpus-summaries/`, the frozen `generation-plan.json`,
`run-manifest.json`, `preflight.json`, `provisioning.json`. Git-ignored (bulky/raw, on the
run host + local): `normalized-results/`, `slop-reports/`, `reviewer-packets/`,
`run-ledger.sqlite`.
