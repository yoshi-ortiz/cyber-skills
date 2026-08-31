---
type: Playbook
title: Scope interviewing and modular architecture
description: What to ask before a boundary is drawn, and which paradigm the answers imply.
status: stable
generated:
  by: claude/opus-5
  at: 2026-08-23T12:30:00-05:00
---

# Scope interviewing and modular architecture

## The interview

A one-line request underdetermines the architecture. Ask until each of these
has an answer you could quote back, and record the answers in
`docs/REQUIREMENTS.md` in the words they were given in.

| Ask | Because a wrong guess here |
| --- | --- |
| Who uses this, and what do they already know? | Sets the entire surface, not just the copy |
| Is this a prototype to be thrown away, or the thing? | Decides how much boundary is worth paying for now |
| What must it look like? Reference, screenshot, or existing screen? | "Make it nice" is not a visual requirement |
| What already exists that this has to live beside? | Determines whether you are adding a module or editing one |
| What is explicitly out of scope? | The most useful sentence in the interview |
| What does done mean, in a number? | Feeds the KPI, without which done is a feeling |

Say back what you heard before writing anything. A misheard requirement caught
in a sentence costs a sentence.

## Paradigm by package

The right structure depends on what the package is. Enforce the one that fits;
do not apply a software layering scheme to a content repository.

| Package | Enforce |
| --- | --- |
| Software and SaaS | Strict separation of concerns. Domain-Driven Design or Feature-Sliced Design. Business logic decoupled from the UI. |
| Editorial and content | Rigorous taxonomy, structured content schemas in the headless-CMS sense, clean markdown processing |
| Media and assets | Deterministic asset pipelines, compression policy, CDN-ready directory structure |
| Libraries and tooling | A public surface small enough to document in one screen, everything else private |

## Directory modularization

Isolate domains, encapsulate dependencies, prevent cross-domain contamination.
The test is mechanical: name the module that owns a responsibility. If two
modules own it, or none does, the boundary is wrong and no amount of tidy code
inside them fixes it.

A directory with no declared purpose accumulates whatever lands in it. Give
each one a stated purpose, what it admits, and what it refuses, even if that
statement lives in a comment at the top of the folder's entry file.

## Pivoting without degrading

An approach that hits a dependency conflict gets replaced. The boundary does
not. In practice that is the difference between:

- **Pivot:** the chosen library cannot do server-side rendering, so swap the
  library behind the same module interface.
- **Degrade:** the chosen library cannot do server-side rendering, so reach
  into the view layer from the data layer and special-case it.

The second is faster today and is the reason the third feature takes a week.
When only the degrading option exists, the boundary was wrong: say so, and
change the boundary deliberately rather than tunnelling through it.

## Naming: the ubiquitous language

Ambiguity in naming is where hallucination enters a codebase. One concept, one
term, recorded in `docs/GLOSSARY.md` and immutable once written. Every state,
every core entity, every user persona.

The glossary binds the code, the database schema, the API, and the
documentation equally. A concept named `Subscriber` in the glossary is never a
`User` in a variable, a `customer_id` in a column, or an "account" in a
sentence. When the term turns out to be wrong, change the glossary first and
the code in the same commit; a term that means two things in two places is
worse than a term that was always awkward.
