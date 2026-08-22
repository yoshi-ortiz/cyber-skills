# Roadmap

The burndown. One row per item, each in exactly one state, so "what is left"
is answerable without reading prose.

States: `TODO` · `IN-PROGRESS` · `BLOCKED` · `DONE`

Bugs live in [BUGS.md](BUGS.md) with their root causes. Shipped changes live in
[CHANGELOG.md](CHANGELOG.md). This file is what remains.

Fog. Lives on `dev`, never published to `main`.

## Now

| id | State | Item | Notes |
| --- | --- | --- | --- |
| R-01 | `DONE` | Lightbox spacing scale revived | B-001 |
| R-02 | `DONE` | Per-comp CSS scoping | B-002 |
| R-03 | `DONE` | Variant cap counts the ledger | B-003 |
| R-04 | `DONE` | Status staleness, both directions | B-004, B-005 |
| R-05 | `DONE` | Round stays live during inference | B-006 |
| R-06 | `DONE` | Project brief, one question at a time | |
| R-07 | `DONE` | Brief write path (`POST /brief`) | |
| R-08 | `DONE` | Bookmark as a fourth signal | |
| R-09 | `DONE` | Publication guardrails, `dev` / `main` split | |
| R-10 | `DONE` | Repo docs: README, BUGS, CHANGELOG, this file | |

## Next

| id | State | Item | Why it is not done |
| --- | --- | --- | --- |
| R-11 | `TODO` | Deterministic corpus tagging | `observe_corpus` tags only `image`/`text` by file extension. Wanted: a stable per-item record of *why* a reference was added, keyed by content hash so it is computed once. "Deterministic" has to mean stable storage and schema; the classification pass itself needs inference, since intent cannot be read off a filename. |
| R-12 | `TODO` | Aspect-scoped corpus valuation | A weak draft should be creditable for one aspect only (its colour, its layout, its text). `validate_art_direction` is strictly binary today: every item is fully observed or fully omitted. Needs a third state. |
| R-13 | `TODO` | Redraw the 62 bare-SVG previews | B-007. Mechanical but large; each needs redrawing in HTML/CSS and re-shooting. |
| R-14 | `BLOCKED` | Judge design quality afresh | B-010. Blocked on a real round run after R-01..R-05, because the rendering defects made every previous judgement unreliable. |
| R-15 | `TODO` | Split `bootstrap_harness.py` | 300KB against a 30KB budget, ~10x over. Recorded as accepted debt in `aesthetic/scripts/CONTEXT.md` and `AGENTS.md`: split before adding to it, do not widen the budget to silence the check. |

## Someday

| id | State | Item | Notes |
| --- | --- | --- | --- |
| R-16 | `TODO` | Enforce the ubiquitous language | `UBIQUITOUS_LANGUAGE.md` defines 30 terms with banned synonyms and nothing verifies it. A checker would make the document load-bearing. |
| R-17 | `TODO` | Automate the verification loop | Four commands, all manual, no CI. Fine while one person runs them; a trap the moment two people do. |

## Working notes

**The published article is a static file.** Restarting the companion does not
regenerate it, so a render change is invisible until an `article` + `publish`
round writes a fresh one. Screenshotting the live URL after a code change shows
the *old* article and makes any fix look like it did nothing. This has cost two
sessions. To check a render change without a real round:

```bash
cd aesthetic/scripts && python3 -c "
import sys; sys.path.insert(0,'.')
import bootstrap_harness as bh
from pathlib import Path
root = Path('<project>')
d = bh.load_decisions(root/'spec'/'design-harness')
bh.canonicalize_recorded_previews(root, d)
Path('/tmp/check.html').write_text(
    bh.render_article(root, d, set(), '', 'es', None, None, '', '', '', '', '', False),
    encoding='utf-8')"
```

**The installed copy does not sync itself.** Propagate `aesthetic/` to
`~/.claude/skills/aesthetic` before running a real round against it.
