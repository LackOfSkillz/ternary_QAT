# Blind-review access separation (Dispatch 25, D7)

Blindness is enforced by **access separation**, not convention
(`linewright/evaluation/battery/blind.py`, tested in `tests/test_lwdb_dispatch25.py`).

```
review/                      # anonymous — the only thing a reviewer/scoring process reads
  anonymous/
    absolute-units/          # identity-free units (no role in id or filename)
    scoring-forms/           # blank forms; finalized + hashed before unblinding
    score-locks/             # sha256 of each locked form — REQUIRED before unblinding
private-unblinding/          # OUTSIDE review/ — scoring code never opens this
  identity-key.json          # unit_id -> {model_role,...}
  pairwise-key.json
```

Enforced invariants:

- `private-unblinding/` must live **outside** `review/` (a build error otherwise).
- Scoring (`finalize_scores`) touches only `review/`; a test runs it with reads of
  `private-unblinding/` **denied** and it still succeeds — proving it never accesses identity.
- A reviewer/process that tries to open `identity-key.json` raises `IdentityAccessError`.
- `unblind()` refuses unless **every** score is locked (`score-locks/` present).
- Anonymous unit ids / filenames never encode the model role.

Both `review/` and `private-unblinding/` are **git-ignored** (raw run artifacts). Only the
enforcement code, tests, and this README are committed. The implementation agent knows the
model placement, so its judgement is **not** an independent blind review — the three-reviewer +
Gary blind pass over these packets remains outstanding.
