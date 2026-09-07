# Work style

## Domains

Developer tooling, specifically test discovery and release verification. The
selected Stage 7 failure is [B-023](../BUGS.md#b-023--the-companions-live-test-runs-in-no-gate--closed).

## Required tools

Python's standard library, `unittest`, and the package gate registry documented
in [Tools context](../tools/CONTEXT.md).

## Always-on constraints

Every repository `test_*.py` must be scheduled by the package gate registry.
The guard must reject an omitted test and permit a scheduled test.

## Excluded scope

No generalized domain framework, external domain catalog, or `harness-core`
change. Server behavior and test correctness are separate from discovery.
