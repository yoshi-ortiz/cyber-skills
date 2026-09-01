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

## Observe

```bash
python3 <skill>/scripts/tokens_qa.py record <skill-dir> \
  --request req.txt --output out.md --scope "<one bounded task>"
python3 <skill>/scripts/tokens_qa.py observe .audit/shots/<id>.json
```

`record` writes one canonical Shot record under `.audit/shots/`. `observe`
validates it and prints the two-column table. Pass a second record to compare a
candidate against a baseline.

Exit 0 is a clean read, 1 is a present hard veto, 2 is an invalid record with
the failing JSON path on stderr.

## The user decides

```bash
python3 <skill>/scripts/tokens_qa.py feedback .audit/shots/<id>.json "<their exact words>"
```

L3 is primary. `accepted` requires an explicit accept with no correction term in
the same breath — "good but fix X" is `failed`, because an instruction restated
is an instruction that did not land. Silence stays `pending` and never ripens
into acceptance.

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
