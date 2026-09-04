# Changelog

Notable changes to the skills in this repository, newest first. Follows
[Semantic Versioning](https://semver.org/). Dates are ISO 8601.

Fog. Lives on `dev`, never published to `main`.

## [Unreleased]

### Added

- **The rest of the rail ships.** `build`, `land`, `check`, and `fix` were four
  reserved directories holding a `CONTEXT.md` apiece. Each is now a family
  router on the `alpha` channel: `build` sequences `ponytail`, `tdd`,
  `test-driven-development`, `code-review`, `verification-before-completion`,
  and `semgrep`; `land` sequences `finishing-a-development-branch` and
  `land-and-deploy`; `check` sequences `zoom-out`, `graphify`, and `review` and
  writes nothing; `fix` sequences `diagnosing-bugs`, `systematic-debugging`,
  and `poteto-mode`. Every router owns order and handoff only, and reimplements
  none of the skills it names. R-36, R-64, R-34, R-63.
- **Bare `fix` has one owner.** `kit` answered to `fix` for a broken install at
  the same time the spec promised it to the `fix` family. `kit` keeps `doctor`,
  `repair`, `troubleshoot`, and `conflict`; bare `fix` is the family's. A name
  with two owners is the defect `check`'s Ontology section exists to catch, and
  the package was carrying one.
- **Anchor and ghost-argument aliases.** `alias.py` generated only whole
  aliases, so a name pointing at one section of a skill, or at a skill plus
  the argument it runs with, had nowhere to come from. A skill declares them
  in its own frontmatter — `anchors:` maps a name to the section it
  bookmarks, `arguments:` maps a name to the argument it bakes in — and
  `link --stubs` writes them. Opt-in like every other kind. R-45.
- **`phase` is declared and gated.** Where a skill's name does not say which
  family it sits in — `genesis` is phase `first` — the frontmatter now has to
  say so, and `manifest_gate.py` refuses the file that does not. Seven skills
  declare it; the ones whose name already answers the question do not. R-38.
- **Genesis names the four skills it drives.** `brainstorming` and `grilling`
  at the interview, `prototype` for an open question blocking a spec row, and
  `ask-matt` when the flow itself is the question. Routing only: whatever a
  driven skill produces still lands in the file its step names. R-35.

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
- **Four more test files ran in no gate, for the same reason.** The previous
  fix added rows to a hand-written list, so the list kept producing the bug:
  the companion's live security test (B-023) plus the Genesis, knowledge, and
  silly suites were executed by nothing. `check.py` finds every `test_*.py`
  now and reads each one to choose how to run it, and its own test fails if
  any test file is covered by no gate.

### Changed

- **The roadmap is one MVP release.** The six workflow families now ship in
  three explicit sprints: `kit` + `first`, `build` + `land`, then `fix` +
  `check`. Each sprint groups work by skill, with direct links from every
  item to its bug, module, and core controller. Settled topology stays in
  `SPEC.md`, completed work stays here, and detailed Design adapter
  obligations stay with their owning contract. Architecture upgrades precede
  an MVP that only routes established public skills; Aesthetic stays deferred.
- **Genesis owns the ADR doctrine.** Target projects record accepted,
  hard-to-reverse boundary decisions under `docs/adr/`; specs remain
  authoritative, Build enforces the decision gate, and Land checks release
  traceability only when the release implements or supersedes that decision.
- **R-15 repaid.** No file in this repository is over its declared byte
  budget, and `tools/check.py` is 27/27 for the first time.

### Added

- **One verification registry (R-17).** `tools/check.py` no longer keeps a
  hand-written list of test files: `test_gates()` finds every `test_*.py` in
  the repository and reads each one to decide how to run it, so a test is
  inside a gate the moment it lands. `tools/release.py` asks that same board
  before it publishes a channel, so a release proves what a local run proves
  instead of accepting `publish --check` as the whole claim. Cook's round was
  already a row on the board; there is no CI configuration in this repository
  to drive, and the one that lands calls `check.py`.
- **Canonical Genesis doctrine (R-61).** `SKILL.md`'s state-machine table is
  now the source of the file topology, read by `genesis_flow.py` rather than
  restated in it. Adding a row to the doctrine checks that file with no Python
  edit; naming a path the doctrine dropped fails `test_genesis_flow.py`
  instead of silently never firing. Ordering stays in the evaluator, because
  which gap to close first is behaviour and the table carries no order.
  `docs/adr/` is canonical topology but not a gate: the ADR contract makes a
  record conditional on a boundary decision, so its absence is not a gap.
- **Ubiquitous-language gate (R-16).** `tools/loanwords.py` now parses all 68
  canonical Repo-Dev terms and their avoided semantic aliases from the root
  glossary. Explicitly typed contract blocks get boundary-aware diagnostics
  with file, line, alias, and replacement; history, code, translations, and the
  separate Design-Inference language stay outside that semantic gate. R-16 no
  longer depends on Genesis runtime work.
- **Queryable Repo-Dev entry (R-58).** `tools/repo_context.py` returns bounded,
  deterministic slices for active states, exact roadmap items, the latest or
  exact bug, and catalog-backed module ownership. `CLAUDE.md` now routes cold
  entry through literal queries while Markdown remains the authoritative store.
- **One Skill Catalog boundary (R-54).** Immutable records now own each local
  skill's identity, family, channel, names, origin, path, doctrine body, and
  UTF-8 body size. Index, publication, and dev-install adapters consume those
  records; duplicate identities fail rather than overwrite, and publication
  matches a skill root instead of any same-named path component. The vectors
  dashboard now reports stored UTF-8 body bytes, closing B-021.
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
