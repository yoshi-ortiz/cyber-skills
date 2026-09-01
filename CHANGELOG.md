# Changelog

Notable changes to the skills in this repository, newest first. Follows
[Semantic Versioning](https://semver.org/). Dates are ISO 8601.

Fog. Lives on `dev`, never published to `main`.

## [Unreleased]

### Fixed

- **Review images rendered at phone width.** Every page comp shipped its
  mobile layout because review inherited a 510px default, so the landing
  hero's rail, rooms, and station labels sat below the fold and the user was
  asked to rank a graphic that was not in the picture. Renders at 1280 now.
- **A round could report `done` with nothing to look at.** `graphics_flow`
  had no browser render and no thumbnail anywhere in it. `verify-delivery`
  and `apply-correction` now sit ahead of `done`, and a correction the user
  already sent outranks proving a proposal nobody asked for.
- **Untracked files shipped to users.** `publish` copied the working tree, so
  two stray root files reached both published trees. It publishes what git
  tracks now, which fixes the class rather than the two filenames.
- **A removed CLI flag silently became a different one.** `--output` is an
  unambiguous prefix of `--output-manifest`, so argparse expanded it and
  parsed the user's markdown as a manifest.
- **Praise failed a Cook round.** "not bad" and "no changes needed, ship it"
  both classified as rejection.
- **A refused socket failed a round.** Cook started the companion and fetched
  immediately, so a socket not yet bound read as a broken companion.
- **Two thirds of the test suite ran in no gate.** Three tokens-qa suites and
  all of cook were invisible to `tools/check.py`.

### Changed

- **R-15 repaid.** No file in this repository is over its declared byte
  budget, and `tools/check.py` is 27/27 for the first time.

### Added

- **The rail.** `GOAL.md` (why), `SPEC.md` (the settled contract), and
  `UBIQUITOUS_LANGUAGE.md` (root-scoped, distinct from `aesthetic`'s own).
  Names two independent token-weight axes, cost and signal density, where
  before there was one conflated number. Settles a six-family command surface
  -- `kit`, `first`, `build`, `land`, `check`, `fix` -- fifteen typed names
  resolving to six skills via three alias kinds (whole, anchor, ghost
  argument), so the command count does not scale with the workflow step
  count. Corrects the benchmark to count only model-invoked descriptions;
  user-invoked skills spend human cognitive load, not permanent model context.
  `build`, `land`, `check`, `fix` are
  documented, not yet built; `ROADMAP.md`'s Rail section is the burndown.
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
