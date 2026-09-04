---
type: Contract
title: Architecture decision records
description: When Genesis creates an ADR, what it contains, and which workflow boundary consumes it.
status: stable
---

# Architecture decision records

An accepted spec says **what must hold**. An architecture decision record says
**why a hard-to-reverse boundary was selected**. An ADR explains a contract; it
never overrides one.

## Trigger

Create an ADR when an accepted decision establishes, changes, or deliberately
preserves a hard-to-reverse module, dependency, data, deployment, or ownership
boundary, and meaningful alternatives existed.

Do not create one for ordinary implementation detail or to restate a promoted
spec. Unresolved choices remain questions in `GOAL.md` or raw constraints in
`docs/REQUIREMENTS.md`. Create the ADR atomically when the decision is accepted;
there are no mutable draft ADRs.

## Location and shape

Target projects store records at `docs/adr/NNNN-short-decision.md`.

Every record contains:

- a stable number, title, date, and `accepted` or `superseded` status;
- the related requirement and promoted spec;
- the affected boundary and its owner;
- the context and accepted decision;
- the meaningful alternatives rejected and why;
- consequences and accepted costs;
- verification obligations for Build and Land; and
- `supersedes` and `superseded-by` links when applicable.

An accepted record is immutable except for its supersession link. A changed
decision creates a new ADR that supersedes the old one.

## Authority and workflow

Genesis owns this doctrine, the file topology, and the lifecycle. The affected
boundary owner proposes the decision. The user or designated authority accepts
it. First records the accepted decision.

Build refuses boundary-changing work without the accepted ADR. Land checks
traceability when a release implements or supersedes that decision; releases
unrelated to an ADR do not invent one.

Precedence is explicit:

1. `docs/SPEC/` defines what must hold.
2. `docs/adr/` explains why the selected boundary exists.
3. `GOAL.md` holds unresolved questions.
4. `ROADMAP.md` tracks remaining implementation.

