---
name: land
description: Release and deploy work that build has already proven. Routes finishing-a-development-branch to close the branch and land-and-deploy, reached through the gstack bundle, to ship it. Use when the user says land, do, ship, burndown, land-asap-burndown, or land-deployed-release, or asks to close a branch, cut a release, or make a deployment observable.
disable-model-invocation: true
exits: build, check, fix
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

Build owns pre-release verification. Require its evidence before release; Land
owns CI/CD execution, deployment health and release observability.

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

Every deployment goes through the repository's CI/CD path. Inspect the existing
workflow and stack manifest; create or repair the pipeline when delivery setup
is in scope. Prefer versioned infrastructure as code for provisioned resources;
reuse existing IaC and review its plan before applying changes. Document a
concrete exception when the target cannot support IaC.

Push the authorized release changes, trigger the deployment pipeline, and follow
it to completion. Use manifest-defined build/package commands, environment-backed
secrets, an identifiable artifact/revision, health checks and a rollback path.
Reuse prior authorization; prepare the diff, workflow and infrastructure plan
before requesting any missing release authorization. A provider or credential
gap leaves deployment blocked with its exact next action.

Done when the requested target has a successful CI/CD run and observed health
for the shipped revision. Record the run URL, target, revision, health evidence
and rollback reference. A push or queued job alone is not a deployed release.

Publication in this repository is Repo-Dev work and belongs to `tools/`, not
here. `python3 tools/release.py --channel alpha --push` is the command, and its
doctrine lives with the tool so the two cannot drift.

After a release, evidence goes to `check`. A release that broke something goes
to `fix`, which returns it to the family that owns the break.
