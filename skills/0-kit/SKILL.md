---
name: 0-kit
description: Goal only, not yet implemented. Kit is the one small skill that syncs a chosen set of skills across agents, devices and environments, on top of the Vercel `skills` npm CLI.
---

# 0-kit: goal

Status: **goal only.** No behavior is specified or implemented here yet.

## Goal

Kit syncs skills to every agent, device and environment I use, with one command, and loads nothing into an agent that the agent does not need.

## Shape

1. **Kit is a script skill.** It runs a sync; it does not carry the skills it syncs.
2. **Transport is the Vercel `skills` npm CLI.** Kit does not reimplement install, copy or symlink logic.
3. **`harness-core` is the manifest plus the script.** It holds the list of what to sync and the one script that syncs it.
4. **The manifest is Markdown with ordered lists, not TOML.** One list per scope, in install order, readable by a human and by an agent without a parser.
5. **A starter kit is the default list.** Bare `kit` installs it.
6. **Domain packages are opt-in lists.** `kit <domain>` adds one on the owner's say-so. Nothing is inferred and there is no `all`.
7. **Sync is idempotent.** Running it twice changes nothing the second time.

## Budget rule

The failure this skill must not repeat: the kit grew into a large always-loaded surface and bloated every agent's context, which derailed sessions.

1. **Kit's own `SKILL.md` stays small.** It is a router. Procedure lives in the script and in files read only when named.
2. **Syncing a skill is not enabling it.** A synced skill costs only its listing line until it is invoked.
3. **The starter kit is short.** Each entry earns its place by use, not by availability.
4. **Domain packages stay off by default.**
5. **Size is checked before a run.** A byte cap on `SKILL.md`, every skill description and the manifest fails the sync when exceeded. The cap is never raised to make a run pass.
6. **Nothing is added to agent config without being listed.** No hooks, agent types or MCP servers are installed as a side effect of sync.

## Out of scope

1. Writing the skill. This file only records the goal.
2. Package managers, runtimes and shell hooks. Kit does not install them.
3. Releasing the `harness-core` repo.

## Open questions

1. Manifest filename and list syntax.
2. Which entries make the starter kit.
3. How per-agent and per-device differences are expressed in a list.
