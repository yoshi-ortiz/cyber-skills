---
type: Policy
title: KPI benchmarks and false-positive mitigation
description: What counts as evidence that a task is done, and the four ways a green check lies.
status: stable
generated:
  by: claude/opus-5
  at: 2026-08-23T12:30:00-05:00
---

# KPI benchmarks and false-positive mitigation

The characteristic agentic failure is not being wrong. It is being wrong and
reporting success, because something green was mistaken for the thing being
built. Apply the same skepticism to your own output that you would to a pull
request from someone you had never met.

## Runtime over static validation

A task is not `DONE` because the linter is happy, the types check, or the unit
tests pass. Every one of those can hold while the feature does nothing.

| Claim | Evidence that settles it |
| --- | --- |
| The endpoint works | The actual JSON payload, printed |
| The build is clean | The build run, warnings included, not just its exit code |
| The flow works | The end-to-end path executed, not a test that stands in for it |
| The fix landed | The original failing reproduction, now passing |
| The page renders | The rendered page, seen |

When you cannot produce the evidence, say the work is unverified. That is a
useful sentence. "Done" without it is not.

## Tests that test something

A unit test that mocks the exact logic under test asserts that the code does
what the code does. It passes forever, including through the regression it was
written to catch.

Test the output state against the contract the spec set, from outside the
implementation. The input is what the caller supplies, the assertion is what
the caller was promised, and everything in between is free to change.

## Root cause, not symptom

Before closing anything in `BUGS.md`, write one sentence of root-cause
analysis, and read it back honestly.

| Symptom fix | Root cause fix |
| --- | --- |
| Added a null check at the crash site | Fixed the pipeline that emitted null |
| Retried the flaky call | Found the race the retry was hiding |
| Widened the type to accept both shapes | Established which shape the contract promises |

A symptom fix is sometimes the correct call under time pressure. When it is,
say so in the entry and leave the incident open with the real cause named,
rather than closing it and losing the finding.

## KPI benchmarks

Functional is not the same as finished. Each feature carries a measurable goal,
set in `ROADMAP.md` before the build and checked after it. Compare against
something real: the incumbent solution, a competitor's product, or a fixed
number the interview produced.

| Kind | Example |
| --- | --- |
| Latency | Load under 200ms at the stated payload size |
| Stability | Zero cumulative layout shift |
| Complexity | Search stays logarithmic at the target row count |
| Cost | Under the per-request budget on the intended tier |
| Parity | Matches the incumbent on the three flows users actually run |

A feature that fails its benchmark is incomplete, not merely slow. Move it back
to `IN-PROGRESS` and record the measured number, so the next attempt starts
from evidence instead of from the same guess.
