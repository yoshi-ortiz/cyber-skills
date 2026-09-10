# Tokens QA command reference

Load when recording, comparing or updating canonical Shot evidence.

## Commands

```bash
python3 <skill>/scripts/tokens_qa.py record <skill-dir> --request req.txt \
  --inline "<the output>" --scope "<one bounded task>"
python3 <skill>/scripts/tokens_qa.py record <skill-dir> --request req.txt \
  --output-manifest manifest.json
python3 <skill>/scripts/tokens_qa.py observe .audit/shots/<id>.json
python3 <skill>/scripts/tokens_qa.py compare <baseline>.json <candidate>.json
python3 <skill>/scripts/tokens_qa.py feedback .audit/shots/<id>.json --status accepted \
  --source-kind user --source-ref <turn> --source-text "<words>" --observed-at <time>
python3 <skill>/scripts/tokens_qa.py assess-feedback --evidence turns.json --json
python3 <skill>/scripts/tokens_qa.py shot-audit --evidence turns.json --json
python3 <skill>/scripts/tokens_qa.py correction .audit/shots/<id>.json
python3 <skill>/scripts/tokens_qa.py history --project-root . --item-id <id> --json
python3 <skill>/scripts/tokens_qa.py retention --project-root . --item-id <id>
```

`record` exclusively creates one version-2 Shot under `.audit/shots/` with a
fresh UUID. Give it
exactly one of `--inline` and `--output-manifest`. A manifest is
`{"adapter": ..., "artifacts": [{"role", "path", "mime"}]}`; each artifact is
sized and hashed as bytes, never decoded, so a PNG records like prose. An
inline payload over 65536 bytes is refused.

`--invocation <run-id>` optionally joins the run, artifact and feedback through
`inputs.invocation`. Preserve legacy records without it.

`observe` validates one record and prints the two-column table, optionally
against a candidate. `compare` is the same table with both records required.
Neither writes anything.

`feedback` appends a versioned event and updates the effective compatibility
view. `--operation-id` makes replay idempotent; `--expected-revision` detects a
stale writer. `--resolve <event-id>` clears only named corrections. `--status`, `--correction`,
`--sentiment` and `--rank` are independent, at least one is required, and none
is ever derived from another. A correction is not a status. Existing `evidence`
and `observed_at` survive. A record stored at version 1 is frozen history and
refuses every write; record a new shot instead. Closure accepts only a `user`
event carrying source reference, observed time, and supplied or redacted words.

`retention` previews exact Item records and a revision. Re-run with `--delete`
and that revision for explicit deletion. It retains hashed identity/status only;
artifacts remain caller-owned. Deleted evidence makes closure unverifiable.

`assess-feedback` reads an evidence bundle whose `turns` is a list of strings
and names the fields a human might want to set. It is advisory, and it writes
no record.

`shot-audit` reads the same bundle and reports complaints, corrections, repeated
corrections and advisory feedback candidates without writing a record.

`correction` emits the six-key bounded bundle for an adapter. Pass that bundle
so a repair receives only the evidence relevant to its scope.

Add `--json` to any verb for one envelope, `{ok, code, error, path, result}`,
where `path` is the failing JSON path or null.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | success |
| 1 | a present hard veto |
| 2 | schema or arguments |
| 3 | I/O |
| 4 | write conflict |
| 5 | adapter or subprocess |

