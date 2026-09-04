---
name: build
description: Code, build, and test against an accepted contract. Routes ponytail for the smallest change that works, tdd and test-driven-development for the red-green loop, code-review before a branch closes, verification-before-completion to prove the thing ran, and semgrep for the security pass. Use when the user says build, to, make, build-clean-code, build-qa-tests, or build-pre-release, or asks to implement, refactor, or test work that first already framed.
disable-model-invocation: true
anchors:
  build-clean-code: Clean code
  build-qa-tests: QA tests
  build-pre-release: Pre-release
aliases:
  - to
  - make
---

# Build

The stop on the rail where code exists. It arrives with a contract already
accepted by `first` and leaves with evidence that the contract holds.

Build owns the order and the handoff. It does not reimplement the public skills
that do the work; reach for the one the step names, then come back.

| Say | Do |
| --- | --- |
| `build`, `to`, `make` | The whole sequence, in the order the sections below stand |
| `build-clean-code` | Clean code only |
| `build-qa-tests` | QA tests only |
| `build-pre-release` | Pre-release only |

An accepted decision from `first` is an input, not a suggestion. Reopening it
here is how a spec becomes a conversation. If it is wrong, go back to `first`
and change it there.

## Clean code

Write the smallest change that solves the stated problem.

| Reach for | For |
| --- | --- |
| **ponytail** | Any change. Question whether the code needs to exist, prefer the standard library, one line before fifty |
| **code-review** | A diff you are about to hand to someone, or one handed to you |

Run `ponytail` before you write, not after. It is cheapest as a constraint on
the design and most expensive as a rewrite of finished work.

Two things this stop refuses. Abstractions with one caller, added because a
second is imagined. Compatibility shims for a state the migration passes
through and never returns to.

## QA tests

A test that was written after the code passes for the wrong reason: it encodes
what the code does rather than what the contract said.

| Reach for | For |
| --- | --- |
| **tdd** | The red-green-refactor loop on a single unit |
| **test-driven-development** | The same discipline carried across a feature and its integration seams |

Write the failing test first and watch it fail. A test that has never been red
has never been shown to test anything.

## Pre-release

The gate between a green local run and handing the branch to `land`.

| Reach for | For |
| --- | --- |
| **verification-before-completion** | Any claim that work is done, fixed, or passing |
| **semgrep** | The static pass over user input, auth, file and network paths, and infrastructure config |

"It compiles" is not evidence. Run the real artifact, read the real output, and
quote it. A failing check reported as passing costs more than the failure.

Hand to `land` only after this section has actually run. A broken code path
found later belongs to `fix`, which returns it here when the path is restored.
