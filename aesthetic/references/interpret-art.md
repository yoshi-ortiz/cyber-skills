# interpret-art.md

Load only for **observe** on a visual corpus, or **continue** on art. Knowledge index (INDEX.md) → stop; load [interpret-knowledge.md](interpret-knowledge.md).

Do not open `bootstrap_harness.py`. Do not invent colours or faces the corpus does not evidence.

## Completion (checkable)

Stop when all are true:

1. A cohort of 3-6 elements is named in one sentence (what they share).
2. New drawings use new element ids, proposed at 0 stars until the user ranks.
3. Standing ranked elements outside the cohort are untouched.
4. User has the companion URL and a PNG pasted in chat for each new comp.

## Interpret a visual corpus

Read the named folder read-only. Cluster by recurring relationships, not decoration. Declare foundations the user can rank. Missing or empty directory: say so and stop.

Then follow [loop.md](loop.md): Frame, Direct, Declare, Build, Critique, Capture.

## Open the round by naming the cohort

Load [stats.md](stats.md) and run the aggregate command. Pick **polish** first, then **unscored**.

`data-dh-cohort` goes on the same div as `data-dh-controls`. If you cannot say in one sentence what the cohort shares, it is not a cohort.

## Every new implementation gets its own element id

Redrawing under a user-ranked id leaves nothing to judge. Record new work with `decide --source agent --stars 0`. Supersede only after the user ranks the replacement higher — `supersede --element <loser> --by <winner>`.

## Ship the article

`adopt` before `article`. Pass project `--bg/--ink/--accent`. Take hex and faces from the corpus.

Signals: stars = execution; sentiment = direction. Full semantics: [companion-contract.md](companion-contract.md).

## Do not load

interpret-knowledge.md, okf-index.md, this skill's scripts as writable.
