---
name: land
description: Release and deploy work that build has already proven. Routes finishing-a-development-branch to close the branch and land-and-deploy, reached through the gstack bundle, to ship it. Use when the user says land, do, ship, burndown, land-asap-burndown, or land-deployed-release, or asks to close a branch, cut a release, or make a deployment observable.
disable-model-invocation: true
arguments:
  land-asap-burndown: asap
  land-deployed-release: deploy
aliases:
  - do
  - ship
  - burndown
---

# Land

The irreversible stop. Everything before it can be redone by editing a file.
This one reaches other people.

| Say | Do |
| --- | --- |
| `land`, `do`, `ship` | Burndown, then Release |
| `land asap`, `land-asap-burndown`, `burndown` | Burndown only. What is left, and what is actually blocked |
| `land deploy`, `land-deployed-release` | Release only. The branch is already burned down |

`asap` and `deploy` are the two arguments. The prefixed names are the same two
with the argument already chosen, so nobody has to remember which word goes
after `land`.

Land does not verify. `build`'s Pre-release section owns that, and a branch that
arrives here without it goes back rather than forward. Green is not the same as
verified, and a stack reported green by its own author is neither.

## Burndown

Burndown is a read of remaining work, then a decision about it. It is not a
status report.

| Reach for | For |
| --- | --- |
| **finishing-a-development-branch** | Deciding how completed work integrates: merge, stack, split, or abandon |

Every open item ends this section in one of three states. Done, with the
evidence. Cut, with the reason. Carried, with the item it now belongs to. An
item left in none of those is the one that turns up after the release.

Write the result where the project keeps it. In this repository that is
`ROADMAP.md` for remaining work and `CHANGELOG.md` for what shipped, and the
state changes when the work changes state, not at the end of a session.

## Release

| Reach for | For |
| --- | --- |
| **land-and-deploy** | Cutting the release and making the deployment observable. Reached through the `gstack` bundle, which is what the collection installs |

Pause before anything that cannot be undone: a force push to a shared branch, a
deploy, a data deletion, a message to a customer. Reversible steps proceed.
Irreversible ones get confirmed first, every time, however routine the run felt.

Publication in this repository is Repo-Dev work and belongs to `tools/`, not
here. `python3 tools/release.py --channel alpha --push` is the command, and its
doctrine lives with the tool so the two cannot drift.

After a release, evidence goes to `check`. A release that broke something goes
to `fix`, which returns it to the family that owns the break.
