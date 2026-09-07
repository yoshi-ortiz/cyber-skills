# Build the complete Compass and SRI architecture report

Label: wayfinder:map
Status: open

## Destination

A reviewable specification and ordered build plan for all three candidates in
[the architecture report](../../bugs/compass-sri-architecture-review-20260907.html),
with explicit acceptance checks and a clear route to measured first-attempt success.

## Notes

The user requested the complete report as a spec plan, under Ponytail Ultra.
[Build specification and plan](../../roadmap/sri-compass.md) is the implementation handoff.
This map tracks decisions; implementation stages live only in that handoff.
Planning is authorized. No runtime implementation or promotion is performed here.

Use `ponytail ultra`, `wayfinder`, and the project vocabulary. For live decision
work use `grilling` and `domain-modeling`. Read `docs/WORK_STYLE.md` before
implementation and preserve the existing dirty worktree. Refine its currently
selected test-discovery scope explicitly when binding this new work.

The destination and coverage come from the user's current request. Open questions
are proposals, not accepted decisions. No research ticket is needed: the present
questions concern product choices and local evidence.

## Decisions so far

- [Define positive feedback for first-attempt success](issues/01-first-attempt-outcome.md): the user requires acceptance and separately recorded positive sentiment.

## Not yet specified

Any further invocation-specific evidence gaps exposed when the selected field
cohort is inventoried. Graduate concrete gaps into tickets only when observed.

## Out of scope

Gaussian fitting, model-weight training, automatic prompt mutation, a universal
compiler rewrite, new storage systems, publication, and harness-core changes.
These are not needed to build the three report candidates. Universal applicability
is an extensibility goal; a finite experiment cannot prove success for all prompts.

## Wayfinding operations

This effort uses the local-Markdown tracker, following the existing NEXT effort's
convention. `/setup-matt-pocock-skills` can configure a different tracker later;
it is not needed to use these files.

Child issues live in `issues/`; filenames are local identities. Read their titles
when referring to them. `Status: open` plus `Assignee: unassigned` is unclaimed.
Claim by setting the assignee before work. Blocking uses the `Blocked by` field
because local Markdown has no native dependency relation. The frontier comprises
open, unassigned children whose blockers are all resolved, sorted by filename.

On resolution, append a dated `Resolution comment` with the actual decision and
its source, set status to resolved, and index its title here with a one-line gist.
Do not replace the original question. This charting session recorded one actual
user answer received while drafting. Later sessions resolve at most one
non-research ticket. Do not overwrite another session's claim.
