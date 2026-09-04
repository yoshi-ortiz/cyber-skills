# cyber-skills

This repository packages independent agent skills into one release. The skills
sit on a six-family rail so an agent can tell what kind of work it is doing and
which command owns it. Source work happens on `dev`. `tools/publish.py` builds
the `main` and `alpha` trees.

The repository also contains one design project used to test `aesthetic` with
real inputs and outputs. That project is evidence for a Food Product run. It is
not package doctrine. Keep Repo-Dev and Design-Inference context separate.

## Goal and contract

| Read | What it answers |
| --- | --- |
| `GOAL.md` | Why the package exists, what failures it prevents, and which questions remain open |
| `SPEC.md` | The settled package contract |
| `UBIQUITOUS_LANGUAGE.md` | The Repo-Dev vocabulary used by the goal, spec, and roadmap |
| `QA.md` | The repo-independent Shot evaluation contract |

Do not promote an open question into `SPEC.md`. Open questions stay in the
prototype backlog in `GOAL.md` until the answer is settled.

## Roadmap

| Read | What it holds |
| --- | --- |
| `ROADMAP.md` | Remaining work, grouped by epic, with one state per item |
| `BUGS.md` | Incidents and their root causes |
| `CHANGELOG.md` | Shipped changes |

<!-- vocabulary: Item -->
Query the relevant roadmap item before changing package code. The Markdown
files remain authoritative; the query returns only the bounded slice needed to
enter the work:

```bash
python3 tools/repo_context.py summary
python3 tools/repo_context.py state IN-PROGRESS
python3 tools/repo_context.py item R-43
python3 tools/repo_context.py bug --latest
python3 tools/repo_context.py module genesis
```

Use `--json` before the subcommand for an adapter-stable result. Update an
item's state when the work changes state, not at the end of a session.
<!-- /vocabulary -->

## Core modules

| Module | Responsibility | Start here |
| --- | --- | --- |
| `kit/` | Day 0 setup and installation guidance | `kit/CONTEXT.md` |
| `first/` | Planning skills that frame work before code | `first/CONTEXT.md` |
| `check/` | Read-only measurement and the return path into planning | `check/CONTEXT.md` |
| `build/` | Reserved owner for Code, Build, and Test | `build/CONTEXT.md` |
| `land/` | Reserved owner for Release and Deploy | `land/CONTEXT.md` |
| `fix/` | Reserved owner for incident response and rail repair | `fix/CONTEXT.md` |
| `tools/` | Publication, repository gates, discovery, and package measurements | `tools/CONTEXT.md` |
| `cook/` | Food Product runs against scratch projects | `cook/CONTEXT.md` |

`CONTEXT.md` maps the families, release channels, and the boundary between
Repo-Dev and Design-Inference work.

## Submodules

| Parent | Submodule | Responsibility |
| --- | --- | --- |
| `kit/` | `starter-pack/` | Original-name alias for Kit |
| `kit/` | `silly/` | Skill aliases and translated names |
| `kit/` | `spanish/ora/` | Spanish response voice |
| `first/` | `genesis/` | Interview, spec promotion, glossary, proof, and project state |
| `first/` | `knowledge/` | Current sources compiled into cited OKF bundles |
| `first/` | `aesthetic/` | Evidence-backed design decisions and user ranking |
| `check/` | `build-context-token-vectors/` | Peer discovery over installed skill text |

Inside a skill, read its `CONTEXT.md` before its implementation. Each nested
directory declares what belongs there and what it refuses. Under `aesthetic`,
`scripts/` holds executable checks and generators, `references/` holds
on-demand doctrine, and `companion/` holds the local review server.

## The in-repo design project

These paths are one Design-Inference run, not reusable skill source.

| Path | Contents |
| --- | --- |
| `moodboards/` | User-owned reference images |
| `spec/design-harness/` | Recorded design decisions, evidence, and project state |
| `design/` | Rendered HTML comps |
| `shots/` | Generated SVG and screenshot output |

Read `spec/CONTEXT.md` before entering this project state. Repo-Dev records in
`ROADMAP.md`, `BUGS.md`, `CHANGELOG.md`, and `.audit/` are not design evidence.

## Useful reference knowledge

| Need | Index |
| --- | --- |
| Settled cross-skill contracts | `docs/SPEC/CONTEXT.md` |
| Genesis architecture and verification doctrine | `first/genesis/SKILL.md` |
| Aesthetic doctrine for a specific branch of work | `first/aesthetic/references/index.md` |
| Design-Inference vocabulary | `first/aesthetic/UBIQUITOUS_LANGUAGE.md` |
| Publication and repository checks | `tools/CONTEXT.md` |

Load only the reference needed for the current branch. Do not read the
Aesthetic glossary during Repo-Dev work or the Repo-Dev glossary during a
design round.

## Before editing

1. Decide whether the task is Repo-Dev or Design-Inference.
2. Read the target directory's `CONTEXT.md`.
3. Query the item and follow the owner returned by its roadmap or catalog map.
4. Run `python3 tools/check.py` for the repository gate set.

Generated publication trees are outputs. Change source on `dev`, then rebuild
them with `tools/publish.py`.
