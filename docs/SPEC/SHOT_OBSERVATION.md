# Shot observation schema

Status: promoted contract for [QA.md](../../QA.md). Dev fog until the schema
stabilizes; `QA.md` on `main` links here.

JSON is canonical. Example:

```json
{
  "shot_id": "2026-08-31T18:00:00Z-landing-hero-03",
  "scope": "Render landing hero SVG from current scene spec",
  "inputs": {
    "corpus_refs": ["moodboards/llm-shots/good room space, wrong roads.png"],
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
    "path": "shots/landing.hero.flow.svg",
    "mime": "image/svg+xml",
    "bytes": 18432
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
| `corpus_refs` | no | string[] |
| `prompt_hash` | yes | string |
| `tools` | yes | string[] |
| `stack` | no | string[] |

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
| `path` | no | string |
| `mime` | no | string |
| `bytes` | no | number |
| `inline` | no | object (only when no path) |

## `user_feedback`

| Key | Required | Type |
| --- | --- | --- |
| `status` | yes | `pending`, `accepted`, `corrected`, `rejected` |
| `sentiment` | no | `positive`, `neutral`, `negative` |
| `correction` | no | string |
| `rank` | no | number |

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

## File placement

Convention: `<project-root>/.audit/shots/<shot_id>.json`.

Project fog in this repository; not skill payload. Other repos may relocate the
directory; the schema stays the same.
