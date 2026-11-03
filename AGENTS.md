# cyber-skills

The root prompt for every agent. Claude Code (Opus 5.5) and Antigravity
(Gemini 4 Argon) reach it through `CLAUDE.md` and `GEMINI.md`; GPT desktop
(Sol 6.1) reads it directly. No rule here is model-specific.

## Zero tolerance

Deal-breakers: breaking one ends the task; report it. See B-036 in `BUGS.md`.

- Never disable, overwrite, rename, or remove an installed skill, plugin, or
  built-in command without naming each one to the user and getting a yes.
  A bulk "turn off unused skills" pass is never implied consent.
- Never install a skill whose folder or `name` is a built-in command such as
  `resume`, `status`, or `review`. After any sync, `python3
  ~/.harness-core/harness.py status` must exit 0.
- Never treat a skill this repo ships (`skill_discovery.names()` in `tools/`)
  as unused because one app's counters are low; other harnesses use it too.
  `harness.py status` fails while any of them is switched off.

## Entry

Burndown first. Before package changes, after user corrections, and when
resuming work, read [Feature burndown](CONTEXT.md#feature-burndown) and follow
its selection, scope, evidence, and completion rules.
Read [the project work style](docs/WORK_STYLE.md) for the declared domain and
always-on constraints.

Changes under `first/aesthetic/` are Repo-Dev work. Read
[`first/aesthetic/AGENTS.md`](first/aesthetic/AGENTS.md) before loading its
runtime skill instructions.

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

For query syntax, run `python3 tools/repo_context.py --help`.
For NEXT upgrade work, brief [NEXT.md](NEXT.md) at entry and update its progress
and verification evidence before the final briefing.

## Map

[Module map](CONTEXT.md#module-map) lists modules, submodules, the in-repo
design project, and reference indexes. Read the row you are about to enter.

## Verification and publication

Run checks appropriate to the changed files. Run `python3 tools/check.py` when
verifying the whole repository or preparing publication; report failed checks.

Generated publication trees are outputs. Change source on `dev`, then rebuild
them with `tools/publish.py`.
