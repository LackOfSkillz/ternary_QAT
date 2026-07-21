# Normalization Report — Electro phrase lists

Deterministic. Nothing is silently discarded; every excluded entry is in
`normalized/excluded-artifacts.yaml` with a reason.

## Raw entry counts (non-blank lines)

- bigrams-electro-a.txt: 1000
- bigrams-electro-b.txt: 1000
- trigrams-electro-a.txt: 999
- **total raw entries:** 2999

## Deduplication

- unique entries: **2475**
- exact duplicates removed: **524**
- cross-file overlap (phrases in >1 file): **524**

## Exclusions (corpus artifacts)

- proper-name entries: **120**
- setting/numeric identifiers: **3**
- malformed/truncated entries: **3**
- **total excluded:** 126

## Retained candidates by tier

- high_risk_signature: **27**
- contextual_risk: **861**
- ordinary_phrase: **1461**
- **total retained candidates:** 2349

All thresholds downstream are REVIEW, never FAIL. No phrase is labeled "AI-only"; tiers are repetition-risk priors only.
