# NEXT upgrade progress

Execution checkout: `/Users/bebote-pro/Development/cyber-skills`.
Requirements: [original NEXT specification](/Users/bebote-pro/.codex/worktrees/4a88/cyber-skills/NEXT.md).
Schedule: [Shots and sprints](/Users/bebote-pro/.codex/worktrees/4a88/cyber-skills/.scratch/next/spec.md).
Decisions: [original map](/Users/bebote-pro/.codex/worktrees/4a88/cyber-skills/.scratch/next/map.md).

This file tracks execution; permanent policy belongs in the owning contracts.

| Sprint | Progress | Remaining |
| --- | --- | --- |
| 1: bounded next action | VERIFIED: S1.1–S1.3 implemented; 36 tests pass | Actual result acceptance pending; R-71 remains IN-PROGRESS |
| 2: trustworthy evidence | VERIFIED: event history, provenance, revision closure and retention implemented | Actual user acceptance pending |
| 3: portable observation | VERIFIED: code/document and graphic adapters use Tokens QA | Actual prototype acceptance pending |
| 4: bounded compiler | VERIFIED: reviewed Aesthetic moodboard invocation is compiled and runtime-gated | Actual invocation acceptance pending |
| 5: package health | VERIFIED: generic contracts belong to Tools; discovery/release/publication stay unified | Full board debt remains separately tracked |
| 6: field evidence | FIELD RECORDED: R-71 Shot `ac2251a3eef94c5a95571bbfd3cb7fab`; integrated proof passed | Actual user verdict required for completion |
| 7–8 and learner | CONDITIONAL | Require the original spec's evidence triggers |

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
tools/test_compass_flow.py                         17 pass
check/tokens-qa/scripts test suite                108 pass
cook test suite                                    61 pass
first/aesthetic/scripts test suite                597 pass
tools test suite                                   44 pass
tools/test_fog.py                                  OK
git diff --check                                  clean
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

Focused proof (2026-09-05): 18 compiler tests, 36 graphics tests, 13 contract
tests, and the 31-gate registry self-test pass; `git diff --check` is clean.
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

Sprint 6 is technically built but cannot be marked accepted or DONE until the
user supplies an actual verdict on this result.
