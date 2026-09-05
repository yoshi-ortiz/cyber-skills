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

## Compatibility and limits

Legacy rows remain readable and are not retroactively declared accepted. Opt them
in deliberately. `genesis_flow.py` remains a legacy topology audit, not a closure
gate; use the compass for managed feature work. Markdown chunking and the optional
inference compiler are separate projects, not bootstrap dependencies.

Public command tests in `tools/test_compass_flow.py` use synthetic feedback in
temporary projects. They prove the state/feedback/proof path, not lower model
cost or real user satisfaction. R-71 stays IN-PROGRESS until user acceptance.
