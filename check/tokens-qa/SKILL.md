---
name: tokens-qa
description: Observe one Shot, measure what it cost, and say what it broke. Black-box QA over the declared request, the observable output, the token counts and the user's own words.
disable-model-invocation: true
---

# Tokens QA

Black box. Read the declared request, the observable output, the exposed token
counts, and what the user actually said. Never hidden reasoning, and never a
repository scan standing in for evidence: context you cannot see is
`not_observed`, not a guess.

## Two phases, inferred

`OBSERVE` for evaluate, score, tokens, contamination, derail, what went wrong.
`FIX` for fix, repair, improve, rewrite, next version. Both match, or neither
matches, choose `OBSERVE` — it writes nothing, so a wrong guess costs a read.

## Five verbs

```bash
python3 <skill>/scripts/tokens_qa.py record <skill-dir> --request req.txt \
  --inline "<the output>" --scope "<one bounded task>"
python3 <skill>/scripts/tokens_qa.py record <skill-dir> --request req.txt \
  --output-manifest manifest.json
python3 <skill>/scripts/tokens_qa.py observe .audit/shots/<id>.json
python3 <skill>/scripts/tokens_qa.py compare <baseline>.json <candidate>.json
python3 <skill>/scripts/tokens_qa.py feedback .audit/shots/<id>.json --status accepted
python3 <skill>/scripts/tokens_qa.py assess-feedback --evidence turns.json --json
python3 <skill>/scripts/tokens_qa.py correction .audit/shots/<id>.json
```

`record` writes one canonical Shot record under `.audit/shots/` at version 2,
under a fresh UUID, created exclusively so a second writer never wins. Give it
exactly one of `--inline` and `--output-manifest`. A manifest is
`{"adapter": ..., "artifacts": [{"role", "path", "mime"}]}`; each artifact is
sized and hashed as bytes, never decoded, so a PNG records like prose. An
inline payload over 65536 bytes is refused.

`observe` validates one record and prints the two-column table, optionally
against a candidate. `compare` is the same table with both records required.
Neither writes anything.

`feedback` is authority, not inference. `--status`, `--correction`,
`--sentiment` and `--rank` are independent, at least one is required, and none
is ever derived from another. A correction is not a status. Existing `evidence`
and `observed_at` survive. A record stored at version 1 is frozen history and
refuses every write; record a new shot instead.

`assess-feedback` reads an evidence bundle whose `turns` is a list of strings
and names the fields a human might want to set. It is advisory, and it writes
no record.

`correction` emits the bounded bundle an adapter may act on. Six keys, and
nothing else from the record travels. Handing an adapter the whole Shot is how
one rejected round becomes a rewrite of the skill that produced it.

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

## The user decides

L3 is primary. `accepted` requires an explicit accept with no correction in the
same breath. "good but fix X" is `failed`, because an instruction restated is
an instruction that did not land. Silence stays `pending` and never ripens into
acceptance.

## Fix

Read the target `SKILL.md`, the baseline request, and the present findings.
Write the complete rewrite to `<target>/SKILL.next.md`. Never touch `SKILL.md`,
never overwrite an existing `SKILL.next.md`, and put no QA metadata in it —
narrow only what a finding cites, and leave the rest alone. Then run it and
`record` the result as the candidate.

## Hard vetoes

Exactly four, from [QA.md](../../QA.md): `scope_breach`,
`missing_observation_log`, `context_derail`, `ungrounded_corpus_claim`. An
undeclared source with no matching text in the output is `context_contamination`
— real, reportable, and not a veto.

Compare token totals only when both records share a profile.
