---
type: Index
title: Genesis reference index
description: The contracts SKILL.md points at, loaded only when a step names one.
status: stable
---

# Genesis reference index

| Concept | Purpose | Trust boundary |
| --- | --- | --- |
| [Scope interviewing and modular architecture](architecture.md) | What to ask before drawing a boundary, and the paradigm each package implies | This skill's doctrine, not an external standard |
| [Architecture decision records](architecture-decisions.md) | When an accepted boundary needs an ADR, its minimum shape, and who may accept it | This skill's doctrine; the target project's spec remains authoritative |
| [The sourcing contract](sourcing.md) | Where to look before writing from scratch, and how to validate what you find | This skill's doctrine, plus ordinary dependency hygiene |
| [KPI benchmarks and false-positive mitigation](verification.md) | What counts as evidence, and the four ways a green check lies | This skill's doctrine, not an external standard |

| [Reproducible development environment](environment.md) | Runnable setup for software projects | Project requirements determine applicable components |
| [Focused cleanup and improvement](improvement.md) | Scoped cleanup and evidence-driven workflow improvement | Reviewed artifacts; no model-training or universal-performance claim |

External facts do not live here. Anything distilled from a real source belongs
in the target project's `docs/knowledge/`, owned by **/knowledge**.
