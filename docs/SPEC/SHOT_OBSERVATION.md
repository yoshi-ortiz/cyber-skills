# Shot observation schema

Status: promoted contract for [QA.md](../../QA.md). Dev fog until the schema
stabilizes; `QA.md` on `main` links here.

JSON is canonical. The current schema is version 2. Example:

```json
{
  "version": 2,
  "shot_id": "2026-08-31T18:00:00Z-landing-hero-03",
  "scope": "Render landing hero SVG from current scene spec",
  "inputs": {
    "corpus_refs": [
      { "path": "moodboards/llm-shots/good room space, wrong roads.png" }
    ],
    "prompt_hash": "sha256:abc…",
    "tools": ["text_to_graphics.py", "iso_svg"],
    "stack": ["python3", "stdlib"]
  },
  "compute": {
    "model": "claude-opus-5",
    "harness": "cursor",
    "started_at": "2026-08-31T18:00:00Z",
    "duration_ms": 4200,
    "tokens": {
      "input": 12000,
      "output": 800,
      "profile": "estimated"
    },
    "passes": [
      {
        "name": "compile",
        "prompt_hash": "sha256:def…",
        "tokens_input": 4000,
        "tokens_output": 200
      }
    ]
  },
  "output": {
    "adapter": "graphic",
    "artifacts": [
      {
        "role": "deliverable",
        "path": "shots/landing.hero.flow.svg",
        "mime": "image/svg+xml",
        "bytes": 18432
      }
    ]
  },
  "provenance": "procedural",
  "gates": {
    "l1": { "status": "pass", "name": "graphics_flow.status" },
    "l2": { "status": "skip", "reason": "no browser verification this pass" }
  },
  "user_feedback": {
    "status": "pending"
  }
}
```

## Required top-level keys

| Key | Type | Rule |
| --- | --- | --- |
| `version` | number | `2`. A `1` record is migrated on read |
| `shot_id` | string | Unique per attempt |
| `scope` | string | One bounded task |
| `inputs` | object | See below |
| `compute` | object | See below |
| `output` | object | See below |
| `provenance` | enum | `corpus`, `procedural`, `fetched`, `inference` |
| `user_feedback` | object | See below |

## `inputs`

| Key | Required | Type |
| --- | --- | --- |
| `corpus_refs` | no | descriptor[] |
| `prompt_hash` | yes | string |
| `tools` | yes | string[] |
| `stack` | no | string[] |
| `request` | no | string |
| `target_skill` | no | string |

A corpus descriptor is an object with a required `path`. Version 1 wrote bare
strings. Each string becomes `{ "path": "<the string>" }` on migration.

## `compute`

| Key | Required | Type |
| --- | --- | --- |
| `model` | yes | string |
| `harness` | yes | string |
| `started_at` | yes | ISO-8601 string |
| `duration_ms` | yes | number |
| `tokens` | yes | `{ input, output, profile }` |
| `passes` | no | array of per-pass objects |

`profile` is `exact` when the target tokenizer ran; otherwise `estimated`.

## `output`

| Key | Required | Type |
| --- | --- | --- |
| `adapter` | yes | string (e.g. `graphic`, `document`, `bundle`) |
| `artifacts` | no | non-empty array of artifact objects |
| `inline` | no | object |

Exactly one of `artifacts` and `inline` is present. An artifact carries a
required `role` and `path`, and an optional `mime` and `bytes`. Version 1 put a
single `path`, `mime`, and `bytes` directly on `output`. That shape migrates to
one artifact whose `role` is `deliverable`. Absent keys stay absent. Nothing is
filled in with null.

## `user_feedback`

| Key | Required | Type |
| --- | --- | --- |
| `status` | yes | `pending`, `accepted`, `corrected`, `rejected` |
| `sentiment` | no | `positive`, `neutral`, `negative` |
| `correction` | no | string |
| `rank` | no | number |
| `evidence` | no | string, the user message the status was read from |
| `observed_at` | no | ISO-8601 string |

**Primary verdict:** `status`, `sentiment`, and `correction` from user chat.
Negative sentiment or any correction means the shot did not succeed at L3.

## `gates` (optional)

```json
{
  "l1": { "status": "pass|fail|skip", "name": "…", "reason": "…" },
  "l2": { "status": "pass|fail|skip", "name": "…", "reason": "…" }
}
```

Gates inform risk; they do not override L3 except where [QA.md](../../QA.md)
names a **hard veto**.

## Unknown fields

Validation is strict at every object level. A field this document does not name
is refused, and the error names its exact JSON path. A stray key under
`compute.tokens` reports `$.compute.tokens.surprise`. A stray key on the first
artifact reports `$.output.artifacts[0].surprise`.

Strictness is what makes migration safe. A record that quietly carries an
unnamed field is a record whose meaning nobody agreed on.

## Reading a record

`shot_contract.migrate` is the only entry. It deep copies, so it never mutates
what it was handed. It returns a version 2 record unchanged, migrates a version
1 record, and refuses anything else with `$.version: unsupported version`.
`shot_contract.validate` is `validate_v2` over `migrate`, so every version 1
record already on disk still reads.

## File placement

Convention: `<project-root>/.audit/shots/<shot_id>.json`.

Project fog in this repository; not skill payload. Other repos may relocate the
directory; the schema stays the same.
