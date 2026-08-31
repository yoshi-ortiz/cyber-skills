---
type: Policy
title: The sourcing contract
description: Where to look before writing something from scratch, and what to check before trusting what you find.
status: stable
generated:
  by: claude/opus-5
  at: 2026-08-23T12:30:00-05:00
---

# The sourcing contract

Generating extensive boilerplate, drawing raw SVG paths, and laying out a
complex screen blind are the three things a model is worst at and the ecosystem
is best at. Sourcing is the default; writing from zero is the exception that
needs a reason.

## Where to look first

| Need | Look at |
| --- | --- |
| UI components | Established libraries: shadcn/ui, Radix, the framework's own primitives |
| Icons and vectors | Icon packs such as Lucide or Phosphor. Never hallucinate a path. |
| Type | Hosted font services with a real fallback stack declared |
| Charts and dashboards | Established wrappers rather than custom render functions |
| Data and analysis | Existing notebooks and boilerplate for the shape of the problem |
| A new domain or app | The official starter kit or template for that stack |

The reason is not laziness. A sourced component carries accessibility work,
browser quirks, and edge cases that a from-scratch version silently drops and
that nobody notices until a user does.

## When from-scratch is right

Reach for it when the requirement is genuinely specific to this product, when
the sourced option would drag in a dependency far larger than the need, or when
the surface is small enough that the dependency costs more than the code. Say
which of the three applies. "I preferred to write it" is not one of them.

## Tooling discovery

Before solving a problem by hand, check whether the environment already solves
it. A connected MCP server, an API connector, a CLI already installed, or a
skill already loaded beats a bespoke implementation, and the check costs one
sweep at the start of the task.

Documentation is part of this. For any unfamiliar or fast-moving dependency,
pull the current official docs rather than answering from training data, and
distil them with **/knowledge** so the next task does not pay for the fetch.

## Version pin validation

A sourced snippet is a claim about a version. Before it goes in:

1. Find the version in the dependency manifest, not in the snippet's prose.
2. Confirm the snippet, answer, or scraped doc targets that version.
3. When it does not, either upgrade deliberately or find the version-correct
   form. Do not adapt it by guessing what changed.

An API that existed in the version the snippet was written for and not in
yours is the most common way a confident implementation fails at runtime while
passing every static check.
