# interpret-art.md

Load only for `observe @/art-folder` on a visual corpus, or `continue`. If the corpus is a knowledge index (INDEX.md / `*.md`), stop this file and load interpret-knowledge.md instead.

Do not open `bootstrap_harness.py`. Do not invent colours or faces the corpus does not evidence.

## Completion (checkable)

Stop when all are true:

1. A cohort of 3-6 elements is named in one sentence (what they share).
2. New drawings use new element ids, proposed at 1 star max.
3. Standing ranked elements outside the cohort are untouched.
4. `adopt` then `article` then `publish` then `doctor --quiet` ran once this turn.
5. The user has the companion URL (`?key=` included).

## Interpret a visual corpus

Read the named folder read-only. Cluster by recurring relationships, not decoration. Declare foundations (palette, faces, pairings) the user can rank. This is the only visual mode that adds fundamentals from outside.

A run with no corpus produces inference, not evidence. Missing or empty directory: say so and stop.

Then follow [loop.md](loop.md): Frame, Direct, Declare, Build, Critique, Capture.

## Open the round by naming the cohort

Before any other work, say which 3-6 elements this round works. Pick from `stats`: `polish` first (liked, badly drawn), then `unscored`.

`data-dh-cohort` goes on the same div as `data-dh-controls`. If you cannot say in one sentence what the cohort shares, it is not a cohort. `article` refuses one spanning more than two foundations unless you pass `--asks "<one sentence>"`.

A round that touches everything scores nothing. `doctor` fails a live element with no scoring row unless the screen declares a cohort.

## Every new implementation gets its own element id

Redrawing under an id the user already ranked leaves them nothing to judge. Record the new drawing with `decide` as `proposed` at 1 star max. Leave the competitor standing until the user ranks the replacement above it. Supersede only after that. Record a win with `supersede --element <loser> --by <winner>`, never `decide --supersedes`.

`doctor` fails a screen on which every element is already user-ranked: that round proposed nothing. `agent-set 0` in `stats` with coverage 100% means go build, not stop.

## Ship the article, not a list of rows

`adopt` before `article`, always. `article --out <screen>.html --cohort <ids> --cohort-name <name>` writes the page. Pass the project's `--bg/--ink/--accent`.

A section must show its material. `describe --tokens` records colours and faces. Name actual families. Pairings are decisions (`type.pairing.<a>-x-<b>`). Take hex and faces from the corpus, never invent them.

Rows group by foundation prefix. `init --language es` stores language; never hardcode generator copy.

## Signals

Stars 1-5 = graphic execution. 0 is a real worst score. Thumbs = direction. 👍 at 0-2 stars is polish: redraw, do not drop. Full semantics: [companion-contract.md](companion-contract.md).

A round ships 3-6 redraws in one turn. Per turn: one `doctor --quiet`, one `adopt`, one `article`, one `publish`, the rest drawing.

## Do not load

interpret-knowledge.md, `bootstrap_harness.py`, this skill's own files as writable.
