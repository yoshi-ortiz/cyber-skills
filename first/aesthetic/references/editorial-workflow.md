---
type: Contract
title: Editorial burndown contract
description: Append-only epic and element scope rendered in the ranking article.
status: stable
generated:
  by: codex/gpt-5
  at: 2026-08-20T23:57:30-05:00
---

# Editorial burndown contract

The burndown is project management data rendered inside the established Aesthetic ranking article. It is not a second website and it does not rank art direction.

## Project scope

Save `spec/design-harness/editorial.json`:

```json
{
  "version": 1,
  "baselineAt": "2026-08-20T12:00:00Z",
  "epics": [
    {"id": "identity", "title": "Recognizable identity", "critical": true},
    {"id": "motion", "title": "Motion language", "critical": false}
  ],
  "elements": {
    "core.thesis": "identity",
    "motion.transition.enter": "motion"
  }
}
```

Epics are explicitly named by the project. They can represent foundations, surfaces, accessibility, deployment, motion, content, or another real concern. `critical` is priority only. Each scoped element maps to exactly one primary epic; cross-cutting relationships belong in evidence, not duplicate ownership.

## Append-only events

Append one state transition per line to `editorial-events.jsonl`:

```json
{"eventId":"motion-enter-resolved-1","at":"2026-08-20T13:00:00Z","kind":"element","id":"motion.transition.enter","to":"resolved"}
```

`kind` is `epic` or `element`. `to` is `unresolved`, `resolved`, or `discarded`. Event ids are stable and unique; replaying the same id changes nothing. Never derive historical scope from the latest decision snapshot.

## Article behavior

The article plots unresolved epics and unresolved elements as independent series. The current point names both counts in text. The existing ranking graph, TOC, zones, controls, and slideshow remain unchanged.

When no editorial spec exists, omit the burndown. Never fabricate history from file mtimes or current completion counts.
