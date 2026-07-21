# Electro Phrase-Signature Research Artifact

A research artifact for **reducing recurring model-written prose signatures** so
LineWright-assisted books read as naturally authored, stylistically varied fiction
— not standardized AI prose.

> **This is not a blacklist and not training data.** No phrase here is prohibited,
> no phrase proves AI authorship, and no list is fed to training. The goal is to
> detect **patterns and clustering**, not to punish isolated normal English.

## What this is

Electro compiled bigram/trigram lists from **publicly available generative-model
output** (likely, not certainly, Kimi-heavy). LineWright uses them for corpus
diagnostics, phrase-family research, and adversarial-record design. See
[`provenance.yaml`](provenance.yaml).

## Layout

```text
electro-phrase-signatures/
  README.md                     # this file
  provenance.yaml               # compiler, source origin, permission, hashes
  methodology.md                # how normalization + families + tiers work
  raw/                          # the three uploaded lists, byte-for-byte
    bigrams-electro-a.txt        # original "bigrams (2).txt"
    bigrams-electro-b.txt        # original "bigrams (3).txt"
    trigrams-electro-a.txt       # original "trigrams (1).txt"
  normalized/
    candidate-phrases.yaml       # generated: deduped, attributed, tiered
    phrase-families.yaml         # authored: 10 structural risk families
    excluded-artifacts.yaml      # generated: proper names / malformed, with reasons
  reports/
    normalization-report.md      # generated: counts and audit summary
  scripts/
    normalize_phrase_lists.py    # deterministic normalization
    scan_phrase_signatures.py    # reusable Gate 0 v3 scanner (library + CLI)
  docs/
    evaluation-plan.md           # 3-layer evaluation + detector-resistance guardrails
```

## Regenerate

```bash
python datasets/research/electro-phrase-signatures/scripts/normalize_phrase_lists.py \
  --root datasets/research/electro-phrase-signatures
```

## The one-line intent

> LineWright reduces repetitive AI writing habits and helps preserve the author's
> individual voice. It does **not** claim to make AI writing undetectable.
