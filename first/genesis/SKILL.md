---
name: genesis
description: Spec-driven development discipline. Establishes the file topology a project's state lives in, interviews scope before architecture, sources before it writes, and refuses to call work done on a green linter alone. Use when starting a project or a feature and the user says genesis, spec-driven, deterministic build, or asks for a roadmap, burndown, spec, or architecture set up. Also use to audit a project already underway against the same contract.
disable-model-invocation: true
---

# Genesis

Goal-centric execution is not an excuse for spaghetti. The end state includes
an **elegant, modular architecture**, or the feature is not finished. Speed
comes from not rewriting, and not rewriting comes from the boundary being right
the first time.

Run this at the start of a project, at the start of a feature, or against work
already underway to find where it drifted.

## 1. Interview before you architect

Never derive a boundary from a one-line request. Ask until the prototype's
expectations, constraints, and visual requirements are explicit, then say back
what you heard before writing anything. Questions worth asking, and how to
choose the paradigm the answers imply:
[references/architecture.md](references/architecture.md).

Raw answers land in `docs/REQUIREMENTS.md` verbatim, including the parts you
disagree with. Refining in place destroys the record of what was asked for.

## 2. Promote the requirement to a spec

A requirement becomes a contract when it moves to `docs/SPEC/`. Treat what is
in there as fixed for the duration of the build: a spec that changes while you
build against it is a conversation, not a contract. Change it deliberately, in
its own commit, before the code moves.

Every term the spec introduces gets one immutable entry in `docs/GLOSSARY.md`.
If the glossary says `Subscriber`, then `User`, `Customer`, and `Account` are
forbidden in code, schema, and docs when referring to that thing.

## 3. Fetch what you do not know

Do not implement an unfamiliar or fast-moving dependency from recall. Pull the
current official documentation and distil it into `docs/knowledge/` with
**/knowledge**, which owns that format. Check the version you distilled against
the dependency manifest before writing a line against it.

## 4. Source before you write

You are bad at boilerplate, raw SVG, and blind layout, and the ecosystem is
good at all three. Search for the production-ready solution first: component
libraries, icon packs, official starters, established chart wrappers. Reaching
for a from-scratch implementation is a decision that needs a reason.
Approved vectors and the tooling sweep:
[references/sourcing.md](references/sourcing.md).

## 5. Build inside the boundary

Isolate domains, encapsulate dependencies, keep business logic out of the view
layer. When an approach hits a dependency conflict, **pivot on the approach,
never on the modularity**. A hack that forces a quick fix through a boundary
costs more than the pivot it avoided.

## 6. Prove it, then say it

A passing linter is not evidence. A unit test that mocks the logic you just
wrote is not evidence either, it is the same claim twice. Confirm the thing
actually ran: the real payload, the real build, the real end-to-end path, and
the KPI the roadmap set. Full contract:
[references/verification.md](references/verification.md).

## 7. Update the state, immediately

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
| `docs/GLOSSARY.md` | The ubiquitous language | One term per concept, and the code obeys it |
| `docs/knowledge/` | Distilled external sources | Owned by **/knowledge**, in OKF 0.2 |

Closing a bug means naming the root cause you fixed. "Added a null check" is a
symptom. "The pipeline emitted null because the upstream join was optional"
is the bug.

## Auditing an existing project

Same order, read instead of write. Which of these files exist, which of them
lie, which module owns a responsibility twice, and which item is `DONE` with
no runtime evidence behind it. Report the drift; do not silently fix it.
