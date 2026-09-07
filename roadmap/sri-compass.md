# Compass and SRI: complete build specification and plan

Status: build plan; outcome rule confirmed by the user; field experiment pending.
Owner map: [Build the complete Compass and SRI architecture report](../.scratch/compass-sri/map.md).
Source: [full architecture report](../bugs/compass-sri-architecture-review-20260907.html).
Incident: [B-032](../BUGS.md#b-032--context-learner-understates-retry-cost-and-permits-held-out-task-overlap--open).

## Outcome and scope

Build all three report candidates in the existing modules. Make evaluator costs
and held-out claims honest; preserve first-attempt feedback evidence for reviewed
calibration; concentrate repeated Item evidence preparation within Repo Context.

The product target is the first delivered attempt receiving positive user
feedback with zero corrections. SRI means an observed result informs one reviewed
instruction or regression-fixture change, then a comparable experiment checks
whether that change helps. Runtime declarations change only through review.

“Zero-shot” in this effort means no corrective retry before the accepted delivery.
“Peak” names the desired user outcome; it introduces no Gaussian assumption.
The user confirmed that qualification requires explicit acceptance AND separately
recorded positive sentiment, each with user provenance. Acceptance alone is
insufficient; absent sentiment is unknown and neutral sentiment does not qualify.
Decision source: [Define positive feedback for first-attempt success](../.scratch/compass-sri/issues/01-first-attempt-outcome.md).

## Existing ownership

| Module | Owns after the build | Existing interface and consumers |
| --- | --- | --- |
| Genesis Compass | Item eligibility, active-item resumption, priority/document order | Standalone `next`/`check`; Repo Context |
| Tokens QA | Shot history, sourced feedback, corrections, proof and veto judgment | Existing Shot CLI; Cook and graphic output adapters; Repo Context |
| Repo Context | Reviewed Item contract plus evidence join, action and budget precedence | Existing `next`/`check`/`close` commands |
| Context Learner | Reviewed experiment validation, cumulative aggregates and advisory comparison | Existing JSONL evaluator and report |
| Context compiler | Deterministic context admission and runtime proof gate | Existing Aesthetic invocation; future invocation only when demonstrated |

The interface is the test surface. Prefer internal consolidation to new modules.
Keep output-specific details in the existing adapter. No new facade, universal
router, storage engine, neural dependency or runtime calibration selector.

## Candidate one: deepen experiment evaluation

Target `tools/context_learner.py` and its existing test file.

1. Validate the full experiment before split aggregation. Reject a task that
   appears in both train and heldout, incomplete arms, invalid values and
   incompatible controls. Reject booleans where integer counts are required and
   non-finite numbers. Diagnostics identify the offending task or field.
2. Aggregate each task/arm once: all attempts, cumulative observed tokens,
   acceptance state and required-context recall. Reuse these aggregates for
   recommendation and report. Missing usage cannot become zero.
3. Report median cumulative tokens per accepted task/arm, including failed and
   mixed attempts in that task/arm. Report never-accepted task counts and their
   spent tokens separately. Do not silently drop them from cohort outcomes.
4. Separate acceptance recovery from cost improvement. An accepted candidate
   against an unaccepted baseline can establish recovery; it cannot by itself
   establish lower cost. Preserve acceptance, cost and recall as distinct facts.
5. Freeze the candidate instruction/declaration revision and acceptance-criteria
   identity for an experiment. Bundle hashes may legitimately differ by task;
   do not mistake a task-specific bundle hash for candidate identity. Bind each
   paired task to the same task input and repository state unless an explicitly
   reviewed change is itself the experimental variable.
6. Keep old version-1 input readable for its existing evaluation purpose. Any
   added evidence requirements use an explicit versioned format. Legacy input
   lacking those fields cannot certify the new first-attempt objective. Document
   the corrected median meaning and report-version compatibility deliberately.

Acceptance examples:

| Input | Required result |
| --- | --- |
| Baseline rejected 900 + accepted 100 | Cumulative accepted-task cost 1,000 |
| Same task in both splits | Refuse before recommendation |
| Baseline rejected 100; candidate accepted 200 | Recovery recorded; no cost-improvement claim |
| Candidate rejected 10 + accepted 50 | Cost 60; not first-attempt success |
| Never-accepted task | Count and cost retained |
| Missing usage or conflicting controls | Explicitly unevaluable/refused, no success claim |

## Candidate two: preserve first-attempt outcome evidence

Target the existing Tokens QA history reduction and Shot contract, with the
smallest reviewed connection into learner input. Extend existing projections
rather than creating a second authoritative ledger.

The projection must distinguish chronological first attempt, attempt count,
effective verdict, sourced acceptance, observed sentiment, all correction events,
unresolved corrections, rejection/restart history where recorded, deleted evidence,
proof status, and the evidence revision from which these facts were derived.
Retain legacy uncertainty and current redaction/source-reference behavior.

Use stable Shot/event identities to avoid counting replayed operations twice.
Resolving an event changes unresolved status but does not remove its contribution
to correction history. Do not claim a recorded history is complete merely because
one Shot exists: calibration input must explicitly bind the reviewed attempt set
and first-attempt provenance. Deletion or missing history invalidates that claim.

A task's first-attempt result is qualified only when its first delivered attempt
meets the resolved feedback rule, contains zero corrections, has no earlier
rejection/restart for that delivery, and passes applicable proof/veto checks.
Unknown provenance, pending feedback and incomplete histories stay distinguishable
from both a qualified result and an observed negative outcome.

Reviewed learner input references the source Shot/event identities and evidence
revision, plus its task, invocation and experimental controls. Validate the
connection through the existing evidence owner; free-text `verdict_source` alone
does not verify it. A minimal development-only export or reviewed conversion is
acceptable; choose within the current module structure and avoid a new framework.

Do not change current Item closure semantics: an accepted repaired Item may close
while still failing the stricter first-attempt metric. Synthetic fixtures prove
these distinctions, never real user satisfaction.

Acceptance cases: qualified first attempt; neutral or missing sentiment according
to the settled rule; praise without acceptance; accepted retry; resolved correction;
rejection followed by acceptance; replayed event; fixture-sourced acceptance;
deleted evidence; stale evidence revision; redacted source; unknown token usage.
Exercise code/document and graphic records through the shared evidence interface.

## Candidate three: concentrate the Item evidence join

Target `tools/repo_context.py`. Consolidate repeated contract/history/proof-argument
preparation used by `next_feature`, `check_compass` and `close_item` into internal
implementation with the existing public commands unchanged.

Keep Tokens QA authoritative for latest Shot, sourced acceptance, unresolved
corrections, vetoes and proof integrity. Remove redundant reconstruction only
after tests show that the owning judgment is consumed in each command. Preserve
each command's distinct eligibility and error behavior; sharing preparation does
not make their actions identical.

Preserve existing revision checks across reads. Do not call separate observations
a consistent snapshot without verifying revisions. Keep errors explicit and all
query/closure commands read-only. Do not remove the standalone Genesis seam.

Acceptance: existing output and exit-code parity for deterministic fixtures;
active work precedence; missing contract binds; pending feedback waits; acceptance
with changed proof returns verification; stale closure refuses; unresolved
correction refuses closure; unknown/exhausted budget retains current precedence;
explicit selection still refuses ineligible work; no-ready-item never means done.

## Build sequence

| Stage | Deliverable | Proof and exit |
| --- | --- | --- |
| Bind | Re-read dirty state and report; bind a new scoped Item, contract and work style when execution starts | Preserve existing R-72 state and feedback; do not silently repurpose it |
| Evaluator correctness | One aggregate, split validation, honest cost/recovery reporting | Reproduce B-032 with failing cases, then make them pass through existing evaluator |
| Evidence semantics | Promote the confirmed feedback rule into owning contracts | Actual decision reference; examples above have explicit expected outcomes |
| Shot history | Evidence projection and its smallest learner connection | Existing Shot CLI tests plus public adapter cases; current closure behavior preserved |
| Item join | Internal consolidation in Repo Context | Public next/check/close parity, revision and proof refusal cases |
| Integrated calibration | Versioned reviewed experiment input; first-attempt metric alongside cost/recall | Synthetic full-path baseline/candidate test; complete, invalid and legacy evidence cases |
| Field evaluation | Frozen experiment using real attempts and actual verdicts | Predeclared cohort and promotion rule; qualified, negative and unknown outcomes retained |
| Handoff | Updated report, incident evidence and execution briefing | Technical completion and field evidence reported separately; no fabricated improvement |

Evaluator correctness can be built independently of the field decision ticket.
The first-attempt predicate uses the confirmed feedback decision. Real promotion waits
for the field-experiment decision and available evidence. Candidate-three work is
included even though its recommendation strength was lower; stop at concentrating
actual repetition rather than expanding its scope.

## Verification and closure

Use current test discovery and add cases to existing owner test files where
possible. Every new `test_*.py` must be discovered by the package gate registry.
Do not introduce a separate testing convention.

```sh
python3 -B tools/test_context_learner.py
python3 -B -m unittest discover -s check/tokens-qa/scripts -p 'test_*.py'
python3 -B -m unittest discover -s first/genesis/scripts -p 'test_*.py'
python3 -B tools/test_compass_flow.py
python3 -B -m unittest discover -s tools -p 'test_repo_context.py'
python3 -B tools/test_fog.py
python3 -B tools/repo_context.py check
git diff --check
```

Run touched output-adapter suites when their implementation changes. At final
integration, run `python3 -B tools/check.py`; classify actual unrelated debt and
environment blocks using fresh evidence. Do not claim the full board passed
because scoped tests passed. Retain the standalone Compass-copy regression and
publication exclusion of learning records on both channels.

For B-032 closure, retain both reproductions as regression checks and record the
root-cause repair. For the overall Item, follow existing explicit user acceptance
and proof requirements. Implementation may be technically complete while field
calibration remains unevaluated; neither a fixture nor an absent verdict closes
that evidence gap.

## SRI evaluation and claims

The exact cohort and promotion rule belong to
[Choose the field cohort and promotion rule](../.scratch/compass-sri/issues/02-field-experiment.md).
Freeze the baseline and candidate before held-out evaluation, keep required
context recall, and report observed counts as well as any rate. Report feedback
coverage and pending/abandoned outcomes to prevent favorable-response filtering.

A single cohort cannot establish universal prompt success. Extend by real
invocation with comparable evidence, preserving domain-specific output adapters.
Use existing compiler declarations to apply a reviewed improvement. No Gaussian
calibration artifact is needed for these deterministic repairs and outcome facts.
