---
name: genesis
description: Bootstrap projects and first-work-style, or advance scoped features with Compass, reproducible setup, and evidence-driven improvement.
disable-model-invocation: true
phase: first
arguments:
  first-work-style: work-style
---

# Genesis

Advance verified, user-accepted outcomes with fewer corrective attempts and
less unnecessary context. Apply this workflow to the target project's actual
domain: software, research, content, media, or a combination. Select tools and
structure from its requirements and existing conventions.

Use the tools available in the current model environment. Named skills and
package scripts are optional helpers; their absence leaves the underlying work
required. With no file or execution access, provide proposed artifacts and exact
verification steps, and mark execution unverified. All generated project files
belong in the target project; preserve existing work and canonical locations.

## Compass

1. Bind one bounded Item: user outcome, acceptance criteria, scope, exclusions,
   proof and any agreed budget. On a cold start, create its `ROADMAP.md` row
   before implementation; then follow sections 1 to 8.
2. When available, run `python3 scripts/compass.py --project-root PATH next`
   from this skill's directory; `check` validates the roadmap. Otherwise read
   the table: require unique `ID`, valid `State`, nonempty `Workstream`, resolved
   acyclic dependencies and at most one active Item per workstream. Resume active
   work; otherwise select ready, non-deferred work by numeric Priority then row
   order. `no-ready-item` means report the selection blocker, not completion.
3. Build, verify and retain actual feedback. Completion requires explicit user
   acceptance. Preserve correction history and respect the agreed budget.
4. In this repository, `python3 tools/repo_context.py --json next` joins Compass
   with Shot observations. For reviewed fields, budget or closure, read
   [Feature compass](../../docs/SPEC/FEATURE_COMPASS.md); for repository compliance,
   read [QA.md](../../QA.md). Standalone projects use step 2 without these tools.

## Work style (`work-style`)

For `first-work-style`, derive the project's domains from its requirements.
Write `docs/WORK_STYLE.md` with **Domains**, **Required tools**, **Always-on
constraints**, and **Excluded scope**. Link canonical sources. Add a pointer
in `AGENTS.md` and, if present, `CLAUDE.md`, both reading that same file.
Done when domains and constraints are explicit.
For an explicitly requested managed skill collection, read
[Extending Genesis with the cyber-yoshi workflow](cyber-skills.md).

## 1. Interview before you architect

Use existing requirements; ask only for missing choices that change scope or
acceptance. For unresolved scope or package structure, read [Scope interviewing and modular architecture](references/architecture.md).

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

Fetch current official documentation for unfamiliar or changing dependencies;
match it to the project's versions. Use **/knowledge** when available to distil
sources into `docs/knowledge/`; otherwise record URL, version, retrieval date
and applicable facts in a concise source note. Use deterministic tools for
counting, parsing and validation.

Research comparable products only when the Item needs a comparison. Record the
source, date/version, input, metric and budget behind each benchmark claim.
Done when implementation-critical facts have evidence and unknowns are explicit.

## 5. Source before you write

Reuse maintained domain tools. Visual sourcing applies only to visual tasks.
Read [references/sourcing.md](references/sourcing.md).

## 6. Build inside the boundary

For software bootstrap or an incomplete development setup, read
[Reproducible development environment](references/environment.md) and establish
the applicable environment before building the first feature. For other domains,
verify the equivalent authoring, validation and delivery path.

Load the selected Item's contract, owning modules, direct dependencies and
relevant checks. Expand context only to answer a named unresolved question.
Implement one end-to-end slice; isolate external dependencies behind the owning
module. Clean up code that obstructs this Item and record unrelated debt for
separate selection. For cleanup or recurring delivery failures, read
[Focused cleanup and improvement](references/improvement.md).

Done when the scoped outcome is implemented, affected checks pass, and the
changes contain no unexplained scope expansion.

## 7. Prove it, then say it

Run the public acceptance path and record commands, results and artifacts.
Tests establish technical verification; explicit user feedback establishes
acceptance. A missed benchmark leaves the Item `IN-PROGRESS` with its measured
result. For benchmark selection and bug regression proof, read
[KPI benchmarks and false-positive mitigation](references/verification.md).
Done when each acceptance criterion has passing evidence or a stated blocker.

## 8. Update the state, immediately

Update state when it changes. Reuse existing canonical documents; create the
applicable records below as their contents become necessary. Record ADRs only
for qualifying decisions and releases only when a release exists.

| File | Holds | Rule |
| --- | --- | --- |
| `README.md` | Quickstart and the architectural overview | Reproducible setup |
| `ROADMAP.md` | The burndown | `TODO`, `IN-PROGRESS`, `BLOCKED`, `DONE`. Update immediately. |
| `BUGS.md` | Incidents | Root cause before closure |
| `CHANGELOG.md` | Chronological releases | Actual release changes |
| `docs/REQUIREMENTS.md` | Raw asks, unrefined | Append-only |
| `docs/SPEC/` | Promoted contracts | Canonical contracts |
| `docs/adr/` | Accepted architecture decisions | Supersede accepted decisions explicitly |
| `docs/GLOSSARY.md` | The ubiquitous language | Consistent names |
| `docs/knowledge/` | External evidence | Source and version recorded |

Close bugs with the root cause, fix and regression proof. Done when state agrees
with evidence. Report the outcome, checks actually run, unresolved blockers and
next action. Pending user acceptance stays pending; continue independent
authorized work when available.

## Auditing an existing project

Inspect topology, duplicated ownership and DONE items lacking evidence. Report
findings without implementing changes unless asked.
