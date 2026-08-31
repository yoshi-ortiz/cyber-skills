---
type: Reference
title: Ledger statistics
description: Deterministic descriptive statistics for individual design elements.
status: stable
generated:
  by: codex/gpt-5
  at: 2026-08-20T23:57:30-05:00
---

# Ledger statistics

Deterministic aggregates over the standing ledger. Same decisions, same numbers — a **benchmark**, not proof the round is good.

## Command

```bash
python3 scripts/bootstrap_harness.py stats --project-root .
python3 scripts/bootstrap_harness.py stats --project-root . --json
```

Load this file before naming a cohort on a **continue** run. Run the command; do not infer counts from DECISIONS.md.

## Read the report

| Field | Meaning |
| --- | --- |
| **coverage** | Fraction of standing elements with a **user-set** rank. Headline metric. High mean stars at 20% coverage is agent inference. |
| **needsPolish** / polish line | 👍 sentiment and ≤2 stars — good idea, drawing not there. Redraw, never drop. |
| **conflicts** | 👎 sentiment and ≥4 stars — direction discouraged despite strong execution. |
| **unscored** | Standing elements still agent-set — need user clicks. |
| **histogram** | User star distribution 0–5. Zero is a real worst score, not “unrated”. |
| **likes** / **dislikes** | Sentiment counts on standing elements. Withdrawn sentiment (`null` in ledger) does not count. |

## Cohort selection

1. **polish** first — liked, low stars.
2. Then **unscored** — what still needs ranks.
3. Name 3–6 ids in one sentence before drawing.

Coverage ≠ quality. Golden-rule coverage (see [golden-rules.md](golden-rules.md)) is a separate determinism metric.

Signal semantics: [companion-contract.md](companion-contract.md).
