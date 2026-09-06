---
name: genesis
description: Bootstrap any folder into a scoped, spec-driven project. Use for genesis, first-work-style, roadmap, burndown, project architecture, or auditing existing project state.
disable-model-invocation: true
phase: first
arguments:
  first-work-style: work-style
---

# Genesis

First commandment: advance verified, user-accepted features with fewer corrective
attempts and tokens. Keep the project context and build clean. This prompt works
alone in any folder; package tools and deterministic Markdown chunks are optional.

## Compass

1. Inspect existing work and state the end user's outcome, criteria, exclusions
   and session budget. Selection ends with one bounded Item.
2. Run `scripts/compass.py --project-root PATH next` to resume active work or
   select ready work. Its `check` validates roadmap structure. The standalone
   selector requires only Python and the target project's ROADMAP.md.
3. Build the selected outcome, run its public acceptance path and retain the
   user's actual feedback and proof. Completion requires explicit acceptance.
4. In this repository, use `tools/repo_context.py --json next` to join selection
   with Shot observations. For reviewed fields, budget or closure, read
   [Feature compass](../../docs/SPEC/FEATURE_COMPASS.md). For compliance, read
   [QA.md](../../QA.md). Installed Genesis remains usable without Tools.

## Work style (`work-style`)

`first-work-style` makes domain context a project fact instead of a catalog the
agent must rediscover in every session. It does not install the whole
collection and it does not route to Aesthetic.

1. Read the project's requirements and the available domains from
   `collection.toml`; choose only the domains this project actually uses.
2. Run `/kit <domain...>` to make that machine selection explicit. Never infer
   `all`, and never turn a repository name into a domain by guesswork.
3. Write `docs/WORK_STYLE.md` with four short sections: **Domains**, **Required
   tools**, **Always-on constraints**, and **Excluded scope**. Link to canonical
   project documents; do not paste skill bodies or the collection catalog.
4. Add one short instruction in the project's `AGENTS.md` to read
   `docs/WORK_STYLE.md`. If the project carries `CLAUDE.md`, import the same file
   there. Do not duplicate the rail into each agent-specific file.

## 1. Interview before you architect

Use existing requirements. Ask only for missing choices that materially change
scope or acceptance; do not re-interview authorized work. Architecture guidance:
[references/architecture.md](references/architecture.md).

Raw answers land in `docs/REQUIREMENTS.md` verbatim, including the parts you
disagree with. Refining in place destroys the record of what was asked for.

## 2. Promote the requirement to a spec

Promote acceptance criteria into `docs/SPEC/`. Revise contracts explicitly
before changing their implementation.

Every domain term gets one canonical entry in `docs/GLOSSARY.md`.
If the glossary says `Subscriber`, then `User`, `Customer`, and `Account` are
forbidden in code, schema, and docs when referring to that thing.

## 3. Record accepted boundary decisions

Record accepted hard-to-reverse choices and their reasons in `docs/adr/`.
Ordinary implementation choices need no ADR.
[references/architecture-decisions.md](references/architecture-decisions.md).

## 4. Fetch what you do not know

Research the selected domain and comparable public products before claiming a
benchmark. Record source URL, date/version, test input, metric, competitor and
budget; unknown or inaccessible evidence stays unknown. Do not fetch unrelated
domain catalogs. Use deterministic parsers, arithmetic, schemas and tests for
counting, state, validation and reproducibility; do not ask an LLM to guess them.

Do not implement an unfamiliar or fast-moving dependency from recall. Pull the
current official documentation and distil it into `docs/knowledge/` with
**/knowledge**, which owns that format. Check the version you distilled against
the dependency manifest before writing a line against it.

## 5. Source before you write

Reuse maintained domain tools. Visual sourcing applies only to visual tasks.
Approved vectors and the tooling sweep:
[references/sourcing.md](references/sourcing.md).

## 6. Build inside the boundary

Keep business logic independent of views and isolate dependencies. Fix conflicts
inside the selected scope; a quick win must leave a clean build and context.

## 7. Prove it, then say it

Run the real acceptance path, not only lint or mocked logic. Record its command,
result and artifacts. Never infer user acceptance from green tests.
[references/verification.md](references/verification.md).

## 8. Update the state, immediately

These files are the project's state machine, not documentation about it. A
`ROADMAP.md` updated at the end of the week is a roadmap nobody could have
trusted on Wednesday.

| File | Holds | Rule |
| --- | --- | --- |
| `README.md` | Quickstart and the architectural overview | Written for someone with nothing installed |
| `ROADMAP.md` | The burndown | `TODO`, `IN-PROGRESS`, `BLOCKED`, `DONE`. One state per item, updated the moment it changes. |
| `BUGS.md` | Incidents | Every entry carries a one-sentence RCA before it closes |
| `CHANGELOG.md` | Chronological releases | Semantic versioning, additions, changes, deprecations |
| `docs/REQUIREMENTS.md` | Raw asks, unrefined | Append-only. Never edited to match what got built. |
| `docs/SPEC/` | Promoted contracts | Canonical. Changed deliberately, never drifted into. |
| `docs/adr/` | Accepted architecture decisions | Created for hard-to-reverse boundaries; immutable except for supersession links. |
| `docs/GLOSSARY.md` | The ubiquitous language | One term per concept, and the code obeys it |
| `docs/knowledge/` | Distilled external sources | Owned by **/knowledge**, in OKF 0.2 |

Close bugs with the root cause, fix and regression proof.

## Auditing an existing project

Inspect topology, duplicated ownership and DONE items lacking evidence. Report
findings without implementing changes unless asked.
