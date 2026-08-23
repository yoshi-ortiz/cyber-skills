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
| R-11 | `DONE` | Deterministic corpus tagging | Shipped in `corpus_tags.py`. Tags are stored keyed by sha256, so reorganizing or renaming an inspiration folder never orphans them. Intent still cannot be read off a filename, which is why the user authors it rather than the harness inferring it. |
| R-12 | `DONE` | Aspect-scoped corpus valuation | A tag names one or more `aspects` from the design-system foundations plus a `quality` of `finished` or `sketch`, so a rough draft is creditable for its colour alone. Replaces the old binary observed-or-omitted. |
| R-13 | `TODO` | Redraw the 62 bare-SVG previews | B-007. Mechanical but large; each needs redrawing in HTML/CSS and re-shooting. |
| R-14 | `DONE` | Judge design quality afresh | Done 2026-08-22 against `keynote-performance`. Output is not generically weak: the system is coherent and subject-specific, 27/27 shots visible, contrast 4.61:1, zero unreadable rules. B-010 closed as too vague; the real defect is B-017. Pipeline measured at 0.19s, so run cost is inference, not tooling. |
| R-26 | `TODO` | Fix the broken circular ring type | B-017. The lower arc of `cover.ring.kicker.antetitulo-arco` renders inverted, red, and overlapping. Read the comp before proposing a redraw — likely per-glyph rotation past 180° without counter-rotation. |
| R-27 | `DONE` | Let an empty cohort re-render the article | B-018. One early return in `check_round_earns_its_place`. The ROADMAP workaround snippet below is now unnecessary. |
| R-28 | `DONE` | Stop leaving Chrome profiles in the user's project | B-019. Nothing to build. The one Chrome call already uses `tempfile.mkdtemp` and removes it in a `finally`; `_chrome-profile` appears nowhere in the repo. The 184 MB is residue from an earlier version or another tool, inside the user's project, so clearing it is their call. |
| R-29 | `DONE` | Give the article a `<meta charset="utf-8">` | Verified against the exact server config that produced mojibake earlier: `text/html` with no charset now renders Spanish accents correctly. |
| R-15 | `TODO` | Split `bootstrap_harness.py` | 305KB against a 30KB budget, ~10x over. Recorded as accepted debt in `aesthetic/scripts/CONTEXT.md` and `AGENTS.md`: split before adding to it, do not widen the budget to silence the check. **R-21, R-22, and R-20 added ~5.5KB to it without splitting first** — a knowing violation of that rule, taken because splitting is this item and the fixes were scoped to the round-scope and chart bugs. The rule stands; the next addition should pay it. |
| R-18 | `TODO` | Companion live-check, every run | `bootstrap_harness.py open` can restore the last page, but nothing in `SKILL.md` gates the rest of a run on the companion actually being reachable first. Needs a hard precondition: verify the companion is live before any other Loop step, not just an `open` call that may go unchecked. |
| R-19 | `DONE` | Wire the manifesto brief into the Loop | B-016. `ensure_brief` in `open_board` creates the brief the first time the companion opens, and `adopt` folds its inbox in. Zero SKILL.md bytes, which mattered at 7250/7250. The module was always complete; nothing had ever created a brief for it to render. The existing one-question-at-a-time textarea is the deliverable; a rich-text editor did not earn its place. |
| R-20 | `DONE` | Corpus relational tagging, embedded in the article | B-016. Tags are authored per reference FOLDER, because the user already curated their inspiration into named folders — 8 decisions on the real project, not 135. `POST /corpus` queues, `corpus_tags.py` owns the schema, and `adopt` prints the key-token digest. Measured on `keynote-performance`: records the agent must write per round fell from 135 to 5. |
| R-21 | `DONE` | Enforce Round Scope against parent items | B-011. `check_round_stays_in_scope` refuses a cohort spanning two parent items, read off the dotted id. No escape hatch: `--asks` answers the foundation-span check, not this one. |
| R-22 | `DONE` | Group the status chart by mutation lineage | B-014. `lineage_root_of` collapses a supersede chain to one bar carrying `data-variants`; the round zone's existing idea-grouping now reaches the strip. |
| R-24 | `TODO` | Cap retry cost when the golden-rule gate rejects a spec | B-013's remaining gap. `golden_rules.py` is single-shot with no memory between calls, so "fix a rejected spec; never bypass the gate" is prose only — nothing requires a retry to narrow scope instead of re-attempting the same spec. Judge against a real run now that R-21 caps breadth, rather than assuming the original symptom survived it. |
| R-25 | `TODO` | Explicit Subject field in `editorial.json` | The durable model behind R-21. The dotted-id prefix is the enforced guard and needs no migration; an explicit `subject` on `validate_editorial_spec`, cross-checked in `validate_art_direction`'s cohort gate, would say the same thing without relying on a naming convention. Not urgent while the convention holds. |
| R-30 | `TODO` | Split `server.cjs` | 42963 bytes against a 40000 budget. `POST /corpus` pushed it further over, though collapsing three duplicated body-readers into `readJsonBody`/`queueLine` paid part of the cost back. Same rule as R-15: split before adding, do not widen the budget. |
| R-23 | `DONE` | Give the companion header a live agent identity | B-015. `resolve_agent` takes URL and name whole from one source, which is the actual defect: a real `project.json` paired the name `Claude Code` with a `cursor://` link. `AGENT_HOSTS` lets a host with no deep link name itself. |

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
sessions. Since R-27, `article` with no `--cohort` re-renders the page as it
stands, so that is the check:

```bash
python3 aesthetic/scripts/bootstrap_harness.py article \
  --project-root <project> --out /tmp/check.html
```

**The installed copy does not sync itself.** Propagate `aesthetic/` to
`~/.claude/skills/aesthetic` before running a real round against it.
