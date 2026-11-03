---
name: big-bang
description: Bootstrap projects and first-work-style, or advance scoped features with Compass, reproducible setup, and evidence-driven improvement.
disable-model-invocation: true
phase: first
arguments:
  first-work-style: work-style
---

# Big Bang

Bootstrap or advance a bounded outcome in its domain. When execution is
unavailable, propose artifacts and mark checks unverified. Write artifacts
in the target project, preserving existing work.

**Big Bang plans; it does not build.** It reads, interviews, specifies and writes
`ROADMAP.md` rows, then stops with the owner's open decisions. No product code,
tests or branch until the user names one Item to build (sections 6 and 7).

## Compass

1. Bind one bounded Item: user outcome, acceptance criteria, scope, exclusions,
   proof and any agreed budget. On a cold start, create its `ROADMAP.md` row
   before implementation; then follow sections 1 to 5 and 8.
2. When available, run `python3 scripts/compass.py --project-root PATH next`
   from this skill's directory; `check` validates the roadmap. Otherwise read
   the table: require unique `ID`, valid `State`, nonempty `Workstream`, resolved
   acyclic dependencies and at most one active Item per workstream. Resume active
   work; otherwise select ready, non-deferred work by numeric Priority then row
   order. `no-ready-item` means report the selection blocker, not completion.
   `next_action` describes state; it is not a build request.
3. Stop after the plan. Only for an Item the user names, follow sections 6 and
   7 and retain actual feedback. Completion requires explicit user acceptance.
   Preserve correction history and respect the budget.
4. In this repository, `python3 tools/repo_context.py --json next` joins Compass
   with Shot observations; for reviewed fields, budget or closure read
   [Feature compass](../../docs/SPEC/FEATURE_COMPASS.md), for compliance
   [QA.md](../../QA.md). Standalone projects use step 2.

## Work style (`work-style`)

For `first-work-style`, derive the project's domains from its requirements.
Write `docs/WORK_STYLE.md` with **Domains**, **Required tools**, **Always-on
constraints**, and **Excluded scope**. Link canonical sources. Add a pointer
in `AGENTS.md` and, if present, `CLAUDE.md`, both reading that same file.
Done when domains and constraints are explicit. For an explicitly requested
managed skill collection, read
[the cyber-yoshi workflow](cyber-skills.md).

## Bootstrap contract

On bootstrap, follow [First's Bootstrap and index](../SKILL.md#bootstrap-and-index)
and [Manifest and agent contract](references/packaging.md). Finish manifest-first
setup, the agent contract and tidy packaging in one invocation, including in a
populated directory.
A note-only request uses these rules as planning reference.

## 1. Interview before you architect

Use existing requirements; ask only for missing choices that change scope or
acceptance. For unresolved scope or package structure, read [Scope interviewing](references/architecture.md).

Done when the outcome, acceptance criteria, exclusions and blocking unknowns
are explicit. Label assumptions separately from user statements.

Append raw asks verbatim to `docs/REQUIREMENTS.md`; preserve their history.

## 2. Promote the requirement to a spec

Promote acceptance criteria into `docs/SPEC/`. Revise contracts before implementation.

Define ambiguous domain concepts in `docs/GLOSSARY.md`; use their canonical
names consistently. Done when the selected Item has a testable contract and
each criterion names observable proof.

## 3. Record accepted boundary decisions

For hard-to-reverse choices, read
[Architecture decision records](references/architecture-decisions.md).
Done when qualifying accepted decisions and reasons are recorded in `docs/adr/`,
or the Item has no such decision.

## 4. Resolve implementation uncertainty

Fetch current official docs for unfamiliar or changing dependencies;
match it to the project's versions. Use **/knowledge** when available to distil
sources into `docs/knowledge/`; otherwise record URL, version, date
and applicable facts in a source note. Use deterministic tools for
counting, parsing and validation.

For needed comparisons, record each benchmark's source, date/version, input,
metric and budget. Done when critical facts have evidence and unknowns are explicit.

For ambiguous scope or evidence, use [Jev](../../kit/references/jev.md) if
configured. Its typed answer is advisory; the Item contract controls.

## 5. Source before you write

Reuse maintained domain tools. Visual sourcing applies only to visual tasks.
Read [sourcing](references/sourcing.md).

## 6. Build inside the boundary

**Gate.** Do nothing here unless the user named the Item to build in this
request. A ready Item or a found bug is not that request: add a row and stop.

For software bootstrap or an incomplete setup, read
[Reproducible development environment](references/environment.md) and establish
it first. For other domains, verify the equivalent authoring, validation and
delivery path.

Load the Item contract, owning modules, dependencies and checks. Expand context
only for a named unresolved question.
For each software feature, follow the [feature branch contract](references/feature-branch.md).
Implement one end-to-end slice; isolate external dependencies. Clean up
obstructions and record unrelated debt separately. For recurring failures, read
[Focused cleanup and improvement](references/improvement.md).

Done when the scoped outcome is implemented, checks pass and scope did not grow.

## 7. Prove it, then say it

Run the public acceptance path and record commands, results and artifacts.
Tests establish technical verification; explicit user feedback establishes
acceptance. A missed benchmark leaves the Item `IN-PROGRESS` with its measured
result. For benchmark selection and bug regression proof, read
[KPI benchmarks](references/verification.md).
Done when each acceptance criterion has passing evidence or a stated blocker.

## 8. Update the state, immediately

Update state when it changes. Reuse canonical documents; create the
records below as needed: ADRs only for qualifying decisions, releases only
when one exists.

| File | Holds | Rule |
| --- | --- | --- |
| `README.md` | Quickstart, architecture overview | Reproducible setup |
| `ROADMAP.md` | The burndown | `TODO`, `IN-PROGRESS`, `BLOCKED`, `DONE`. Update immediately. |
| `BUGS.md` | Incidents | Root cause before closure |
| `CHANGELOG.md` | Chronological releases | Actual release changes |
| `docs/REQUIREMENTS.md` | Raw asks, unrefined | Append-only |
| `docs/SPEC/` | Promoted contracts | Canonical contracts |
| `docs/adr/` | Accepted architecture decisions | Supersede explicitly |
| `docs/GLOSSARY.md` | The ubiquitous language | Consistent names |
| `docs/knowledge/` | External evidence | Source and version recorded |

Close bugs with the root cause, fix and regression proof. Done when state agrees
with evidence. Report the outcome, checks actually run, unresolved blockers and
next action.

## Auditing an existing project

Inspect topology, duplicated ownership and DONE items lacking evidence. Report
findings without implementing changes unless asked.
