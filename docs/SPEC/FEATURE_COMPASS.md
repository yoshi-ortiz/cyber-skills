# Feature compass

R-71 implements the bounded execution loop. Genesis owns roadmap parsing and
selection; Tokens QA owns validated observations, feedback and artifact checks;
Repo Context joins their public interfaces. No Aesthetic dependency is added.

## Contract

Managed roadmap rows have a nonempty Workstream. IDs are unique; states are
TODO, IN-PROGRESS, BLOCKED or DONE. Each workstream has at most one active item.
Dependencies resolve without cycles. Resume active work; otherwise select ready
work by numeric Priority then document order. Deferred work is never selected.
Missing Scope or Proof returns bound-task before implementation.

`python3 tools/repo_context.py --json next` returns one item plus latest feedback.
`python3 tools/repo_context.py check` is part of the full verification board.
Managed DONE rows name a Shot in the project's `.audit/shots/`; it must be the
latest attempt for that item, explicitly accepted, without veto, with passing L2
and unchanged proof-role artifacts. Hashes establish integrity, not truth: the
observer must record checks actually run and feedback actually received.

Budget tokens is an optional total item cap. At or above the cap the next action
is budget-exhausted. Unknown cost or incompatible profiles returns resolve-budget.
This preflight cannot meter a live model or reserve its future tokens. Session
budgets and permission to extend them remain explicit caller responsibilities.

The canonical record keeps changed paths separate from admitted context.
Item-linked costs default to unknown, never request/output file-size estimates.
Corrections remain evidence. Safe self-improvement changes reviewed instructions
or regression tests; it does not train model weights or infer user acceptance.

## Reviewed Item contract (Sprint 1)

An optional `Contract` column references project-owned JSON by plain relative
path. The roadmap remains the selection index. Contract version 1 contains:

```json
{
  "version": 1,
  "item_id": "F-1",
  "review_ref": "user:decision-01",
  "acceptance_criteria": ["The public acceptance check passes"],
  "exclusions": [],
  "read_paths": ["src/"],
  "write_paths": ["src/"],
  "proof_requirements": ["proof.txt"],
  "budget_tokens": 1000
}
```

Criteria and proof arrays must be nonempty. Exclusions and read/write arrays
are explicit and may be empty. Paths stay inside the project, including after
symlink resolution. Budget is a nonnegative integer or explicit null (uncapped).
Review references record the caller's assertion of review, not authentication.
Missing requirements or a missing contract file return `bound-task` with reasons.
Invalid JSON, versions, types, identities and escaping paths fail the command.

`next` returns version 1, the original selector fields, explicit reviewed fields,
contract reference/digest when present, latest Shot and effective feedback,
budget status, next action and reasons. Legacy unknown fields are null rather
than inferred from prose. An unresolved contract has unknown budget status.
Legacy rows retain Scope/Proof fallback until deliberately migrated.

Precedence: invalid roadmap/references fail; missing requirements bind; pending
feedback waits; accepted feedback checks proof and returns `verify-proof` or
`close-item`; failed feedback returns to correction. Execution and correction
are subject to cumulative budget: unknown/incompatible usage resolves the
budget, usage at the cap exhausts it. Feedback/proof actions take precedence
over budget. No eligible row returns `no-ready-item`, never project completion.
Explicit Item selection uses the same eligibility rules and never falls back.

Sprint 2 owns feedback event history, unresolved corrections across attempts,
provenance enforcement and revision-aware closure. Sprint 1's effective feedback
is the latest recorded verdict; it does not claim those later guarantees.

## Compatibility and limits

Legacy rows remain readable and are not retroactively declared accepted. Opt them
in deliberately. `genesis_flow.py` remains a legacy topology audit, not a closure
gate; use the compass for managed feature work. Markdown chunking and the optional
inference compiler are separate projects, not bootstrap dependencies.

Public command tests in `tools/test_compass_flow.py` use synthetic feedback in
temporary projects. They prove the state/feedback/proof path, not lower model
cost or real user satisfaction. R-71 stays IN-PROGRESS until user acceptance.
