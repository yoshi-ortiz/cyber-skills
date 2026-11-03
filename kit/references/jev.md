---
type: Reference
title: Jev typed judgments for Kit and Big Bang
description: Optional TypeSafe SDK use for bounded, advisory workflow decisions.
status: stable
resource: https://docs.typesafe.ai/sdk/
generated:
  by: codex/gpt-6
  at: 2026-09-23T00:00:00-06:00
sources:
  - resource: https://docs.typesafe.ai/sdk/python
    title: TypeSafe Python SDK
    author: TypeSafe AI
  - resource: https://docs.typesafe.ai/concepts/system-one
    title: System One
    author: TypeSafe AI
---

# Jev

Jev accepts text or JSON state and answers typed `Choice`, `Score`, or `Noul`
questions. It does not write plans, code, or explanations. The Python SDK uses
`TYPESAFE_API_KEY` and defaults to `jev-latest`; install `typesafe-sdk` through
the target project's stack manifest before running it. The SDK docs currently
show `TypeSafeClient().system_one(state=..., questions=...)` and answers keyed
by question name. [Python SDK](https://docs.typesafe.ai/sdk/python),
[System One](https://docs.typesafe.ai/concepts/system-one).

| Caller | State | Typed question | Use of answer |
| --- | --- | --- | --- |
| Kit | Owner-provided project description and candidate domains from the live harness catalog | `Choice`: which domain best fits? | Recommend a domain; activate only the owner's explicit choice. |
| Big Bang | Selected Item, its criteria and cited evidence | `Noul`: does evidence support a named criterion? Or `Choice`: which stated scope boundary applies? | Surface uncertainty and inspect the cited evidence; acceptance and closure keep their existing gates. |

Example for an authorized, nonsensitive Kit input:

```python
from typesafe_sdk import Choice, TypeSafeClient

with TypeSafeClient() as client:
    result = client.system_one(
        state={"project": project_summary},
        questions={"domain": Choice(
            instructions="Which catalog domain best matches this project?",
            criteria={name: description for name, description in catalog_domains.items()},
        )},
    )
candidate = result.answers["domain"].choice
```

Use the same call shape for Big Bang with a question tied to one criterion or
boundary. Record the input source, question, returned model, answer and
uncertainty. Compare the answer with deterministic checks and the actual
evidence. Jev's probability is advisory, not proof or user acceptance. If the
SDK, credential, or permission to send the chosen state is missing, continue
with local evidence and name the unavailable Jev check. Send only the minimum
state needed for the question; no secrets, private repository text, or personal
data by default. [System One](https://docs.typesafe.ai/concepts/system-one).
