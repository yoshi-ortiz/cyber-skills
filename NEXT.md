# NEXT upgrade progress

Execution checkout: `/Users/bebote-pro/Development/cyber-skills`.
Requirements: [original NEXT specification](/Users/bebote-pro/.codex/worktrees/4a88/cyber-skills/NEXT.md).
Schedule: [Shots and sprints](/Users/bebote-pro/.codex/worktrees/4a88/cyber-skills/.scratch/next/spec.md).
Decisions: [original map](/Users/bebote-pro/.codex/worktrees/4a88/cyber-skills/.scratch/next/map.md).

This file tracks execution; permanent policy belongs in the owning contracts.

| Sprint | Progress | Remaining |
| --- | --- | --- |
| 1: bounded next action | VERIFIED: S1.1–S1.3 implemented; 36 tests pass | R-71 closed through accepted Sprint 6 field evidence |
| 2: trustworthy evidence | VERIFIED: event history, provenance, revision closure and retention implemented | Actual user acceptance pending |
| 3: portable observation | VERIFIED: code/document and graphic adapters use Tokens QA | Actual prototype acceptance pending |
| 4: bounded compiler | VERIFIED: reviewed Aesthetic moodboard invocation is compiled and runtime-gated | Actual invocation acceptance pending |
| 5: package health | VERIFIED: generic contracts belong to Tools; discovery/release/publication stay unified | Full board debt remains separately tracked |
| 6: field evidence | ACCEPTED: R-71 Shot `ac2251a3eef94c5a95571bbfd3cb7fab`; integrated proof and closure passed | Complete; token usage remains unknown |
| 7: domain guard | FIELD RECORDED: developer-tooling test discovery; B-023 guard and paired fixtures pass in Shot `6fcd72a83c764de1aaabac96a0b1b1d2` | Actual user verdict required for completion |
| 8: rail graph | VERIFIED: router exits declared once and catalog-gated | Actual user acceptance pending |
| 9: optional learner | VERIFIED: reviewed pairwise evaluator and held-out gate built | Legacy corpus refused; real evaluation pending |

## Planned success audit: all upgrades

Prepared 2026-09-06. This is an audit plan, not a fresh verification result.
The historical VERIFIED rows above record implementation checks; they do not
establish architectural integration, field acceptance, or measured improvement.

Sources: [architecture review](bugs/architecture-review-20260905-030336.html)
and [evidence-loop review](bugs/cyber-skills-rl-sri-architecture-review-20260905.html),
interpreted against the original NEXT requirements. The reviews are historical
recommendations, not instructions to execute every proposed abstraction.

### Scope and success criteria

Audit all nine NEXT stages and trace every finding in both reviews to a stage
or an explicitly deferred outcome. Broader Genesis research/competitor automation
and whole-catalog compiler migration are separate outcomes; a bounded slice
cannot close them. Preserve the existing checkout changes during the audit.

| Stage | Audit must demonstrate | Required evidence |
| --- | --- | --- |
| 1: bounded action | One selection authority; deterministic priority/dependencies; typed scope, proof and budget; no legacy closure caller or caller-side reconstruction | Public next/check/close scenarios, caller inventory, refusal cases for blocked/deferred work and incomplete contracts |
| 2: trustworthy evidence | Explicit verdict authority; corrections survive attempts; replay and concurrency are safe; stale or changed proof cannot close; privacy behavior matches its claims | Public negative cases for unsupported acceptance, vetoes, revisions, operation replay, escaped paths and proof changes; scratch redaction/retention/deletion checks; tracked-file and both-channel exclusions |
| 3: portable observation | Code/document and graphic outputs use the same verdict/cost owner; host knowledge stays in adapters | Both public adapter paths, including binary artifacts, absent telemetry and vetoes; a code/document run without Aesthetic state or Claude files |
| 4: bounded compiler | Reviewed structured intent yields reproducible bundles/traces; required constraints survive; overflow and missing proof block the actual runner | Identical-input replay, source/budget/profile changes, required overflow, context contamination and runner refusal tests; narrowly scoped exception test |
| 5: package health | Tools owns generic checks; optional Aesthetic absence works; present adapters and new tests remain discoverable; release propagates failures | Minimal-package fixture, present-skill fixture, registry and release checks, main/alpha generated-tree checks, full gate report |
| 6: field evidence | A real Item has every attempt recorded through an explicit final verdict; incomplete telemetry is labeled; observations are separated from improvement claims | Replayable Shot/artifact/proof chain and actual verdict; pending/abandoned outcomes retained; correction-driven change only when a real correction exists |
| 7: domain guard | Evidence trigger is met before implementation; one declared domain and documented failure are checked deterministically | Trigger record plus failing/valid fixtures; locality traced through input, rules, persistence, output and proof. Otherwise report CONDITIONAL with the missing trigger |
| 8: rail graph | At least two operational routers consume one authoritative exit declaration; illegal handoffs are rejected and conditions remain local | Consumer trace, prose/declaration consistency, illegal known-target and unknown-target cases, missing/duplicate/self-edge cases, bounded owner-return behavior, no cross-Family doctrine load |
| 9: optional learner | Reviewed comparable attempts support an advisory evaluation with honest cumulative costs and isolated held-out tasks | Rejected/restarted attempt accounting, disjoint train/held-out tasks, fixed candidate and criteria, controls/provenance checks, recall/cost regressions, legacy refusal, no source mutation; separate real-corpus evaluation |

Cross-cutting review findings: audit ownership and duplicate-policy removal in
Stages 1–4; terminology and mutation authority in Stages 6/9; privacy in Stage 2;
small-model entry usability in Stages 1/4. Verify one normative owner per rule
and show callers consume it. A new facade or a folder layout alone is not proof.
Record caller identity and telemetry authenticity as trust boundaries unless
the implementation actually verifies them.

### Execution order

1. Capture commit, dirty diff, environment and artifact hashes. Inventory each
   claimed requirement, owning contract, consumer, test and field record. Mark
   historical evidence separately from newly reproduced evidence.
2. Audit Stages 8/9 first because their recent VERIFIED labels have unresolved
   semantic questions. Then audit selection/evidence (1/2), adapters/compiler
   (3/4), and package ownership (5), following the public interfaces.
3. Reproduce relevant owner tests and negative scenarios in scratch fixtures.
   For every failure record expected behavior, actual behavior, minimal repro,
   owner and affected requirement. Audit work reports defects; remediation is
   a subsequent build, not an implicit change to the acceptance criteria.
4. Run the full `python3 -B tools/check.py` board on the audited state. Recheck
   environment-blocked server gates where binding is permitted. Classify actual
   regressions, existing debt and environment blocks from evidence; do not
   assume the historical 26/31 result still applies or waive failing gates.
5. Inspect the real Sprint 6 Shot and learner corpus, then assess Stage 7's
   trigger. Separate code readiness, demonstrated field use and cohort-level
   improvement. Predeclare cohort size, assignment, unchanged requirements,
   controls and uncertainty analysis before claiming improvement.
6. Publish the audit matrix and prioritized findings with reproduction evidence.
   Update stage statuses here only to the level the evidence supports; record
   technical verification and user acceptance independently. Split R-50's
   one-path compiler, wider migration and learner conclusions in the report.

### Priority questions already visible in source

- Stage 9's `median_tokens_per_accepted` currently uses only accepted attempt
  rows, omitting rejected-attempt cost from that metric. Audit cumulative cost
  per accepted Item, including all attempts, and report never-accepted Items.
- Stage 9 partitions by split without rejecting the same task in both splits.
  Audit data leakage, frozen candidate identity, criteria and provenance before
  treating `heldout_passed` as independent evidence.
- Stage 9 permits an accepted candidate to win against an unaccepted baseline
  without a lower-token comparison. Distinguish acceptance recovery from token
  improvement; audit that report language matches the implemented predicate.
- Stage 8 declarations and helper tests exist. Prove real router consumption
  and rejection of semantically illegal known targets; field presence and
  unknown/self-edge validation alone cannot establish that integration.

These are source-inspection observations and audit targets, not newly executed
test results. No actual acceptance or learner improvement has been inferred.

### Audit exit

Every requirement gets PASS, FAIL, BLOCKED, or CONDITIONAL, with evidence and
an owner. PASS means the audited behavior meets its contract on the recorded
state. BLOCKED and CONDITIONAL remain visible and do not count as passes.
The audit is complete when coverage and findings are complete, even if upgrades
fail. All upgrades may be called successful only when their applicable criteria
pass and required field verdicts exist. Release readiness additionally requires
the full release board to pass. No release is part of this audit plan.

## Current execution

R-71, Sprints 1–5 technically verified. Approved seams: Genesis selector, Repo
Context next/check/close, Tokens QA CLI, Cook proof adapter and Aesthetic delivery
adapter. Decision 01 uses a referenced versioned JSON contract; Decision 02 uses
the existing Shot store with append-only events, revisions and a local lock;
Decision 03 uses Cook as the first code/document adapter. The user approved these
seams with “yes, everything is approved.” No result acceptance is inferred.
Usage telemetry remains unknown where callers do not supply it; no token savings
are claimed.

Entry baseline: [first slice evidence](.audit/proofs/next-s1-contract-20260905.md).
Unrelated changes in Knowledge and Kit belong to other work and are preserved.

## Exit briefing: Sprint 1

- S1.1: public flow characterization remains green and regressions exposed
  missing contract loading, empty write scope at zero cap, absent Shot summary,
  missing contract files and malformed false-valued criteria before their fixes.
- S1.2: referenced reviewed fields, contract digest, latest Shot/feedback,
  budget state and decision reasons are returned. Public checks cover explicit
  selection parity, blocked/deferred/dependency refusal, pending feedback before
  budget, incompatible usage, changed proof and deterministic results. Legacy
  unknown fields remain null, and legacy Scope/Proof behavior remains readable.
- S1.3: root and Genesis entry recipes point to FEATURE_COMPASS.md for detailed
  policy. Genesis remains standalone. Caller search found no production
  `genesis_flow` closure caller to migrate; its topology tests remain.
- Publication: NEXT.md is development Fog on both channels, proven by the
  existing public Fog check. No publication was performed.

Verification (2026-09-05):

```text
python3 -B tools/test_compass_flow.py                                10 pass
python3 -B -m unittest discover -s tools -p test_repo_context.py       5 pass
python3 -B -m unittest discover -s first/genesis/scripts -p 'test_*.py' 21 pass
python3 -B tools/test_fog.py                                         OK
python3 -B tools/repo_context.py check                               OK
git diff --check                                                    clean
```

These are owner checks, not a full release board. Synthetic feedback proves
interface behavior only. Sprint 2 must add provenance, append-only events,
cross-attempt unresolved corrections and revision-aware closure before claiming
those guarantees. Next: S2.1, preserve feedback events using existing Shot storage.

## Exit briefing: Sprints 2 and 3

Sprint 2 keeps each immutable attempt as one Shot and appends feedback events
inside it. Operation IDs make replay idempotent; one local lock and expected
revisions serialize writes and reject stale changes. History reduces events
across every Item Shot, retaining corrections until a user-sourced event resolves
their exact IDs. Legacy feedback remains readable with unknown provenance.

Closure now requires the latest Shot and Item revision, user-sourced acceptance,
no unresolved correction, deletion, veto, changed artifact or proof-coverage gap,
plus an observed L2 result naming its check, observer, time and artifacts. Stored
commands are never executed. ISO timestamps are validated before lexical ordering.

Evidence files use private POSIX modes. Requests and user words may be replaced
by source/redaction references. Retention previews exact paths and revision;
explicit deletion leaves a non-sensitive identity/status tombstone and makes
closure unverifiable. `.audit/` is ignored and excluded from both publication
channels. Existing tracked audit records were removed from the Git index while
their local files and repository history were preserved.

Sprint 3 adds a concrete code/document path in `cook/prove.py`: the caller
supplies request, artifact manifest, Item/run IDs, proof destination, usage and
one check command. Cook executes it once, records its observable output and L2
evidence through Tokens QA, and leaves missing telemetry unknown. The Aesthetic
graphic adapter now records binary deliverables, optional Item/L2/proof inputs
and uses the same gate. Claude transcript parsing lives in `cook/claude.py`;
Tokens QA remains host-agnostic. A second host-format adapter waits for a real
second format and caller.

Verification (2026-09-05):

```text
python3 -B tools/test_compass_flow.py                                      17 pass
python3 -B -m unittest discover -s check/tokens-qa/scripts -p 'test_*.py' 108 pass
python3 -B -m unittest discover -s cook -p 'test_*.py'                     61 pass
python3 -B -m unittest discover -s first/aesthetic/scripts -p 'test_*.py' 597 pass
python3 -B -m unittest discover -s tools -p 'test_*.py'                    44 pass
python3 -B tools/test_fog.py                                               OK
git diff --check                                                          clean
```

The full 31-gate board reports 26 passing. Unrelated failures: undeclared
untracked `kit/domains/` directories; existing Tools file-budget debt; local
server bind/start restrictions in vectors and Cook; and the existing loanword
context failure. Publication generation and fog checks pass. Technical proof is
complete; fixture verdicts do not assert real user satisfaction or token savings.

Next: Sprint 6, record one real field Item through the integrated path.

## Exit briefing: Sprints 4 and 5

Sprint 4 selects `aesthetic/moodboard-generation`. A versioned reviewed-intent
record binds user source, digest, review time, prioritized constraints, estimated
`bytes/4` profile and budget into a stable compiler identity. Required overflow
is machine-readable and names required/available counts plus the offending source.
The moodboard runner consumes that bundle and stops immediately before `agy`
unless observed proof matches the identity or a timestamped user exception is
scoped to the invocation. Stored commands remain inert.

Sprint 5 moves generic `CONTEXT.md` declaration and byte-budget checks from
Aesthetic into `tools/contracts.py`, with their tests. `tools/check.py` remains the
one test/gate registry, discovers new tests from an explicit package root, and
loads the Aesthetic harness adapter only when present. Release calls that same
board; publication shares one Fog policy. No release or branch mutation occurred.

Focused proof (2026-09-05):

```text
python3 -B -m unittest discover -s first/aesthetic/scripts -p 'test_direction_context.py' 18 pass
python3 -B -m unittest discover -s first/aesthetic/scripts -p 'test_text_to_graphics.py'  36 pass
python3 -B -m unittest discover -s tools -p 'test_contracts.py'                         13 pass
python3 -B tools/test_check.py                                                          OK
python3 -B tools/test_fog.py                                                            OK
git diff --check                                                                       clean
```

Technical fixtures do not assert real user acceptance or cost savings.

The full board remains 26/31: unrelated untracked `kit/domains/` contracts,
existing Tools file-budget debt, sandbox-blocked vector/Cook local servers, and
the existing loanword context failure. Both publication channels and their Fog
checks pass.

## Exit briefing: Sprint 6

S6.1 uses real Item R-71 in measurement-only scope. Its fixed criterion is the
roadmap proof: the public selection, correction, rejection and verified-acceptance
flow passes in a scratch project. The actual request is stored privately at
`.audit/proofs/r71-sprint6-request.txt`; usage profile and counts are `unknown`
because the host supplied no telemetry. No cost or improvement claim is made.

Cook executed the public compass proof and recorded Shot
`ac2251a3eef94c5a95571bbfd3cb7fab` with hashes for Repo Context, the bounded
compiler, the unified gate board and the proof output. The check passed; the
Shot verdict remains pending. Earlier pending attempts remain preserved.

S6.2 made no change: no actual rejection or correction exists, so an
“evidence-driven improvement” would be invented. S6.3 is technically verified:
the focused integrated proof passes, migrated contract callers are absent, both
publication channels pass Fog checks, and the full board remains 26/31 with the
same unrelated debt/sandbox failures recorded above.

Verification and acceptance (2026-09-06):

```text
python3 -B tools/test_compass_flow.py                                      17 pass
python3 -B check/tokens-qa/scripts/tokens_qa.py gate \
  .audit/shots/ac2251a3eef94c5a95571bbfd3cb7fab.json --project-root . --json  ready: true
python3 -B tools/test_fog.py                                               OK
python3 -B tools/check.py                                                  25/30 reported
git diff --check                                                          clean
```

The user supplied “6 is ok” as the explicit verdict. The event was recorded with
user provenance; the gate and deterministic closure both passed. R-71 is DONE.

## Exit briefing: Stages 8 and 9

Stage 8 treats model-executed router doctrine as operational policy. Build,
Land, Check and Fix declare legal exits in frontmatter; the existing catalog
projects the graph and the manifest/index gate rejects missing, duplicate,
unknown and self edges. Conditions stay local. Fix's `owner` target is a typed
return, not an all-Family wildcard. No dispatcher or dependency was added.

Stage 9 adds a standard-library, development-only evaluator for reviewed paired
baseline/candidate attempts. It counts every attempt, refuses changed controls,
learns only from train pairs, and requires every held-out pair to improve token
cost without required-context recall loss. It reports only and mutates nothing.

Focused verification (2026-09-06):

```text
python3 -B -m unittest discover -s tools -p 'test_skill_catalog.py'    5 pass
python3 -B tools/test_index_gate.py                                   OK
python3 -B -m unittest discover -s tools -p 'test_context_learner.py'  3 pass
python3 -B tools/context_learner.py \
  spec/design-harness/inference-attempts.jsonl                        expected refusal
python3 -B -m py_compile tools/context_learner.py \
  tools/skill_catalog.py tools/manifest_gate.py                       clean
git diff --check                                                      clean
```

The 16 historical inference attempts are correctly refused because they predate
the reviewed schema. Synthetic train/held-out fixtures prove the evaluator; they
are not a real improvement claim.

## Exit briefing: Stage 7

The user selected the proposed developer-tooling/test-discovery domain after
accepting Sprint 6. `docs/WORK_STYLE.md` records that project fact, its required
standard-library tooling, always-on B-023 constraint and excluded scope. Root
agent entry files point to the declaration; publication treats it as Repo-Dev
fog.

The existing `tools/check.py` discovery mechanism remains the guard. Its existing
coverage assertion refuses any repository `test_*.py` omitted by the planned
gate commands. Paired scratch fixtures create the B-023 script-style shape and a
valid unittest shape, then prove both enter the generated plan without a
hand-edited list. This keeps the guard at its existing owner and adds no domain
framework or `harness-core` dependency.

Feature locality: repository test files are input; discovery and coverage rules
live in Tools; no persistence is required; the gate plan and exit status are
output; paired fixtures and the recorded command are proof. Shot
`6fcd72a83c764de1aaabac96a0b1b1d2` records the passing public path with unknown
token usage. Technical construction is complete; actual result acceptance is
still pending.

Verification (2026-09-06):

```text
python3 -B tools/test_check.py                                           OK
python3 -B -m unittest discover -s tools -p 'test_*.py'                 61 pass
python3 -B tools/test_fog.py                                            OK
python3 -B tools/index_gate.py                                          OK
python3 -B check/tokens-qa/scripts/tokens_qa.py gate \
  .audit/shots/6fcd72a83c764de1aaabac96a0b1b1d2.json \
  --project-root . --json                                               pending acceptance only
python3 -B tools/check.py                                               25/30 reported
git diff --check                                                        clean
```

The 61 Tools tests include rail projection, illegal/missing exit rejection,
Stage 7's two discovery shapes, all-attempt accounting, changed-control refusal,
legacy-corpus refusal and held-out recall protection. The current full board is
25/30: existing Tools and
user-owned Genesis byte debt, missing `kit/domains/` contracts, sandbox-blocked
vector/Cook local servers, and the existing loanword context failure. These
failures are outside R-72's declared scope and remain visible.

Full command replay (2026-09-06): every focused and owner test command above
passed. The current Aesthetic discovery run contains 588 tests rather than the
597 recorded on 2026-09-05; no test failed. R-71's Shot gate remains accepted
and ready. R-72's Shot gate reports only its pending user acceptance. The legacy
learner corpus returns the documented schema refusal. The package board remains
25/30 with the same five classified failures, and `git diff --check` is clean.
