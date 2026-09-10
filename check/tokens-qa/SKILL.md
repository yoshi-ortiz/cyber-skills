---
name: tokens-qa
description: Compass any agent session, evaluate evidence, repair scoped contamination, and report goal progress, next actions and measured RSI gains.
disable-model-invocation: true
phase: check
---

# Tokens QA

Black box. Read the declared request, the observable output, the exposed token
counts, and what the user actually said. Never hidden reasoning, and never a
repository scan standing in for evidence: context you cannot see is
`not_observed`, not a guess.

## Feature feedback loop

`record --item-id ID --project-root PATH` links an attempt to a roadmap item.
`history --item-id ID --project-root PATH --json` returns its latest feedback and
costs grouped by tokenizer profile. `gate SHOT --project-root PATH` requires
sourced user acceptance, no unresolved correction or veto, passing L2 provenance
and hash-verified proof artifacts. Record observed
L1/L2 results with `--gates gates.json`; it never executes the declared check.
Keep acceptance pending until the user supplies a verdict.

Item-linked costs default to unknown. Supply observed `--tokens-input`,
`--tokens-output`, `--token-profile` and `--duration-ms` when available.
`--admitted-context` names reads; `--changed` names writes, not admitted context.
Preserve correction history, privacy, scope and test rigor over lower cost.

## Two phases, inferred

`OBSERVE` for evaluate, score, tokens, contamination, derail, what went wrong.
`FIX` when the user authorizes fix, repair, improve, rewrite, or a next version.
Explicit repair selects `FIX` even alongside evaluation.
Otherwise choose `OBSERVE`, which reports findings without writing project state.
Evaluate the named target; editing this skill does not authorize running it over
unrelated repository work.

## Shot tooling

When using installed Shot commands, read [Command reference](commands.md) for
recording, comparison, feedback, retention and exit codes. Without those tools,
continue the session compass using the available evidence.

## The user decides

L3 is primary. `accepted` requires an explicit accept with no correction in the
same breath. "good but fix X" is `failed`, because an instruction restated is
an instruction that did not land. Silence stays `pending` and never ripens into
acceptance.

## Compass any session

Use this loop for any agent, project or domain, including sessions without a
repository, roadmap, Python or Shot tooling. At entry and after new evidence or
user steering, bind the user's goal, acceptance criteria, exclusions, active
Item and next action. Preserve the goal across turns unless the user changes it.

1. Read the current request, existing plan and available observations. Prefer the
   project's canonical tracker; otherwise keep a compact session index in the
   conversation: Item ID, outcome, state, verified criteria/total, evidence,
   acceptance and blocker. Create project files only when authorized. Unknown
   evidence and unknown denominators stay `not_observed`.
2. Resume active authorized work. Otherwise select an unblocked Item serving the
   goal by agreed priority and dependency order. Bind scope and proof before
   acting; request only a decision that blocks progress. If nothing is eligible,
   state the blocker and its resolution rather than declaring the goal complete.
3. Use available tools to execute the next bounded action when execution is
   authorized. In `OBSERVE`, recommend it without mutation. Update the index as
   evidence arrives; retain corrections and distinguish verified output from
   accepted completion. A scope change updates the plan explicitly.
4. Where installed, use `history` for Shot evidence and the project's Compass
   integration for selection/closure. For this package's integration rules, read
   [Feature compass](../../docs/SPEC/FEATURE_COMPASS.md). These are adapters to
   this loop, not prerequisites for it. Without tools, cite conversation evidence
   and label checks that could not run.

Done when the current outcome, evidence, unresolved work and next action are
traceable. Run the closing report below at each handoff; an unfinished goal keeps
its next action. This skill guides the invoked session; it does not install
background monitoring or observe other agents' sessions automatically.

## Fix the observed cause

Bind each repair to a cited finding, owning file, permitted write scope and a
check that can establish the repair. Preserve unrelated user work. If the cause
cannot be observed, state the missing evidence and continue independent repairs.

- **Prompt repair:** read the target `SKILL.md`, baseline request and findings.
  Write the complete candidate to `<target>/SKILL.next.md`; preserve the active
  skill until promotion is authorized. If that candidate exists, use a fresh
  revision filename. Keep QA metadata in the Shot record. Change only instructions
  implicated by the finding. If the user explicitly requests editing the active
  skill, apply the scoped edit directly and retain its diff for review.
- **Repository repair:** inspect the cited paths, their owners and relevant
  callers. Correct misplaced task artifacts, duplicated instructions, stale
  context pointers or scope leaks at their source within authorized scope.
  Establish ownership and references before moving or deleting content. Repository
  inspection can prove a repository defect; it cannot prove what a past model
  read. Keep that distinction in the finding and the report.
- **Context repair:** change the owning context declaration or compiler input so
  the next invocation admits the required sources. Keep project maintenance
  records in their declared role. Verify the resulting admitted-context evidence;
  moving a file alone does not establish that inference context is clean.

Run the relevant acceptance and regression paths and record a candidate Shot
when the recording tools are available. Compare with the baseline under the
same criteria. With no execution access, deliver the proposed change and mark
its verification pending. Done when each repair has evidence or an explicit
blocker, and the authorized diff stays within its bound scope.

In `FIX`, update the existing progress index with verified evidence and actual
state transitions. Acceptance and closure follow the owning gate; green checks
alone leave user acceptance pending. Record unrelated cleanup as separately
scoped work rather than expanding the current Item.

## Conclude with direction and RSI gains

Every evaluation or repair response ends with the progress result, a concrete
next action, and the ASCII table below. Name the next action's Item, owning path,
required change or check, and completion condition. If waiting on the user, name
exactly which verdict or decision is missing. If no eligible Item exists, report
that blocker; if the declared goal is complete, cite its closure evidence.

RSI means evidence-driven improvement of instructions or regression fixtures,
called SRI in this repository. It does not train model weights. Promote a lesson
only within authorized scope and the project's review process. One before/after
pair is a local observation, not proof of general improvement across models.

Identify baseline/candidate Shot IDs and the compared attempt range immediately
before the table. Compare the same task, acceptance criteria, model, harness,
budget and token profile, or mark the affected gain `not_comparable`. Include
failed attempts and corrections in cumulative costs; label a single-Shot
comparison as per-attempt. Preserve required-context coverage and quality alongside
cost. Unknown counts and missing feedback stay `not_observed`, never zero.

Render this as a fenced `text` block using ASCII borders. Replace placeholders
with observed values, widen columns as needed, and retain unavailable rows.
For numeric lower-is-better metrics, gain is baseline minus candidate; negative
values show regression. For criteria coverage, gain is candidate minus baseline
with the same denominator. Show status transitions for nonnumeric rows. Report
percent savings only with a known, positive baseline and comparable measurements.

```text
RSI gains
+------------------------+--------------+--------------+----------------+
| Metric                 | Baseline     | Candidate    | Gain / status  |
+------------------------+--------------+--------------+----------------+
| Verified criteria      | <n/total>    | <n/total>    | <delta>        |
| Acceptance             | <status>     | <status>     | <transition>   |
| Corrections, all       | <count>      | <count>      | <delta>        |
| Cumulative tokens      | <count>      | <count>      | <delta>        |
| Duration, same scope   | <duration>   | <duration>   | <delta>        |
| Contamination findings | <count>      | <count>      | <delta>        |
| Required context       | <coverage>   | <coverage>   | <transition>   |
+------------------------+--------------+--------------+----------------+
```

Count contamination findings only over the same declared inspection surface and
finding rules. Report repository repairs separately from observed inference
contamination. With no comparable baseline, the table reports current evidence
and unknown gains. This is the agent's closing summary; existing CLI output and
the canonical Shot schema remain authoritative and unchanged.

## Hard vetoes

Exactly four, from [QA.md](../../QA.md): `scope_breach`,
`missing_observation_log`, `context_derail`, `ungrounded_corpus_claim`. An
undeclared source with no matching text in the output is `context_contamination`
— real, reportable, and not a veto.
