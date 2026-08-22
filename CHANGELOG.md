# Changelog

Notable changes to the skills in this repository, newest first. Follows
[Semantic Versioning](https://semver.org/). Dates are ISO 8601.

Fog. Lives on `dev`, never published to `main`.

## [Unreleased]

### Added

- **Project brief.** A deliverables-first intake the user answers in their own
  prose, in its own collapsible article section, revisable at any time, with an
  append-only change history. The page asks exactly one question at a time.
  Prompts resolve into the project's language at creation, because they are
  stored into `brief.json` and would otherwise outlive the choice.
  (`aesthetic/scripts/brief_workflow.py`)
- **`POST /brief`.** The first write path for free-form user text. Queues the
  answer; `brief_workflow` validates and adopts it, mirroring how scoring
  already flows through `decisions.jsonl`.
- **Bookmark.** A fourth independent signal beside rank, sentiment and
  lifecycle, drawn as a solid ribbon with `clip-path` and leading the strip.
- **Publication guardrails.** `dev` carries development state; `main` is
  generated from it by `tools/publish.py` and carries the skill only.
  `tools/fog.py` is the single list; `tools/check_publication.py` enforces it.
- **Repo documentation.** `README.md`, `BUGS.md`, this file, and a `ROADMAP.md`
  restructured as an explicit state machine.
- CDN sources named as valid pinned origins in the asset-sourcing contract,
  with unversioned and `latest`-aliased URLs explicitly excluded.

### Fixed

- **Lightbox spacing.** The dialog is appended to `document.body`, outside
  `.dh-art` where `--s1..--s6` are declared, so every `var(--sN)` in the
  lightbox resolved to nothing and the shell computed `padding:0`. Several
  rounds of spacing fixes had been silently discarded. (B-001)
- **Cross-comp CSS collisions.** Comps sharing a class name overwrote each
  other; each now gets a scope class derived from its element id. (B-002)
- **Unbounded variants per idea.** The cap counted only the cohort, so a family
  grew a round at a time; it now counts the ledger. (B-003)
- **Status desync**, both directions: stuck "working" after an interrupted run
  (B-004), then flipping to "waiting" mid-inference once the first fix landed
  with too short a window (B-005).
- **Nothing to do during inference.** Live controls were dimmed to look
  disabled, identical republishes forced a full reload, and in-progress text
  had nowhere to survive. (B-006)
- Chrome screenshot budget split from the qlmanage fallback, so a flaky render
  costs roughly a third as much.
- Cohort size capped in code rather than in prose.

### Changed

- Rounds may now carry up to three variants of one idea, rendered grouped under
  a shared "before" instead of as separate before/after cards. Previously any
  second redraw of an incumbent was refused outright.

---

## Earlier

Before this file existed the history lived only in commit messages. The
substantive entries are `9498fd8` (refuse bare SVG previews, add `audit-svg`),
`073b13b`, `236a146`, `76cd586`, `aba8676` and `7383056`, all summarised above.
