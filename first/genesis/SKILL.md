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
attempts and tokens. This prompt works alone in any folder; every package tool
it names is optional.

Compass selects one Item. Sections 1 to 8 build it.

## Compass

0. **No `ROADMAP.md` is a cold start.** Compass has nothing to select: run
   sections 1 to 8, which write the state it needs. Compass owns every session
   after that one.
1. Inspect existing work and state the end user's outcome, criteria, exclusions
   and session budget. Selection ends with one bounded Item.
2. Run `python3 scripts/compass.py --project-root PATH next` from this skill's
   directory to resume or select work; `check` validates the roadmap. It needs
   only Python and a `ROADMAP.md` whose table carries `ID` and `State` headers
   and a nonempty `Workstream` on every selectable row. Without the script,
   apply those rules by reading the table. `no-ready-item` authorizes no work
   and never means done: report it and stop.
3. Build the selected outcome, run its public acceptance path and retain the
   user's actual feedback and proof. Completion requires explicit acceptance.
4. In this repository, use `tools/repo_context.py --json next` to join selection
   with Shot observations; where that script is absent, step 2 is the whole
   selection. For reviewed fields, budget or closure, read
   [Feature compass](../../docs/SPEC/FEATURE_COMPASS.md). For compliance, read
   [QA.md](../../QA.md).

## Work style (`work-style`)

`first-work-style` makes domain context a project fact instead of a catalog the
agent must rediscover in every session. It installs nothing and it does not
route to Aesthetic.

1. Name the domains this project actually works in, from its own requirements.
   Never infer `all`, and never turn a repository name into a domain.
2. Write `docs/WORK_STYLE.md` with four short sections: **Domains**, **Required
   tools**, **Always-on constraints**, and **Excluded scope**. Link to canonical
   project documents; do not paste skill bodies or a catalog.
3. Add one short instruction in the project's `AGENTS.md` to read
   `docs/WORK_STYLE.md`. If the project carries `CLAUDE.md`, import the same file
   there. Do not duplicate the rail into each agent-specific file.

Those three steps need nothing installed. Arming a machine with a managed skill
collection is an optional extension, never a precondition: when someone asks for
it, read [Extending Genesis with the cyber-yoshi workflow](cyber-skills.md).

## 1. Interview before you architect

Use existing requirements. Ask only for missing choices that materially change
scope or acceptance; do not re-interview authorized work. For the questions that
precede a boundary, and for the paradigm a software, editorial, or media package
each implies, read [Scope interviewing and modular architecture](references/architecture.md).

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
Ordinary implementation choices need no ADR. For which boundaries earn one, the
minimum shape of the record, and who may accept it, read
[Architecture decision records](references/architecture-decisions.md).

## 4. Fetch what you do not know

Research the selected domain and comparable public products before claiming a
benchmark. Record source URL, date/version, test input, metric, competitor and
budget; unknown or inaccessible evidence stays unknown. Do not fetch unrelated
domain catalogs. Use deterministic parsers, arithmetic, schemas and tests for
counting, state, validation and reproducibility; do not ask an LLM to guess them.

Do not implement an unfamiliar or fast-moving dependency from recall. Pull the
current official documentation and distil it into `docs/knowledge/` with
**/knowledge**. Where that skill is not installed, fetch the Open Knowledge
Format specification and follow it directly:
`https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md`.
Check the version you distilled against the dependency manifest before writing a
line against it.

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

A feature that misses the benchmark `ROADMAP.md` set for it is incomplete rather
than merely slow: record the measured number and leave the Item `IN-PROGRESS`.
For the benchmark kinds, the false positives a green check produces, and the
root-cause test a bug closes on, read
[KPI benchmarks and false-positive mitigation](references/verification.md).

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
