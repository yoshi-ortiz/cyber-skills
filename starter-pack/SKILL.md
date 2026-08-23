---
name: starter-pack
description: Operating guide for the agent-skills harness. The loadout of powerful tools every agent carries, and how to install, extend, and ship it.
disable-model-invocation: true
---

# Starter Pack

Every agent on this machine runs the same **loadout**: the skills and MCP servers that give it reach beyond its own weights. `collection.yaml` records that loadout, `install.harness.sh` arms every agent with it by calling each agent's own CLI. One collection, one harness. Source of truth for anything not here: [the harness README](https://github.com/yoshi-ortiz/harness-core).

## Install

```bash
brew tap yoshi-ortiz/harness-core
brew install harness-core
harness init
```

macOS and Homebrew for Linux. Or clone the repo and run `./install.harness.sh init` in place; it needs [yq](https://github.com/mikefarah/yq) and Node, both pulled in by the formula. `init` checks the tools, reports which `header_env` secrets are set, and lists the optional groups. Always start there.

## Where the loadout lives

- Git checkout → the `collection.yaml` beside the harness, edited in place.
- Homebrew install → `${XDG_CONFIG_HOME:-~/.config}/agent-skills/collection.yaml`, seeded once and never overwritten by an upgrade. `AGENT_SKILLS_HOME` overrides.

`collection.local.yaml` is gitignored and deep-merged over it at read time: private sources, pinned agents, per-field overrides. Local wins on conflict. Writes from `skills add` and `mcp add` always land in `collection.yaml`, never the overlay.

## Adding a skill

1. Run `./install.harness.sh skills add owner/repo [skill]`. It records the source **and** arms every agent. A hand edit to `collection.yaml` gives no agent anything; follow one with `./install.harness.sh --agents`.
2. Name skills only for a **subset**. A list that names every skill in the repo behaves like a bare entry and rots. The repo adds a skill, the list silently stops handing it out. Check the repo's set with `npx skills add <repo> -l`.
3. Never pass `--all` to `npx skills add`.
4. Tell the user to start a new Cursor chat. Skills land in `~/.agents/skills/`, symlink into `~/.cursor/skills/`, and each agent reads its loadout at session start.

A source that needs more than the CLI gets `{ install: script }` under its key and a script in `scripts/`.

## Adding an MCP server

`./install.harness.sh mcp add <name> <url|command>`. Each server is a name plus one transport: `url` for http, `command` for stdio, never both.

**Secrets never live in `collection.yaml`.** `header_env` names an environment variable; the harness reads it at install time and sends `<NAME>: <value>`. An unset variable skips that server rather than arming an agent with a broken one, so export it before running.

Reach: claude-code, antigravity, codex, and cursor each get the server (codex has no custom-header flag and skips the header with a warning). `pi` and `zed` expose no add command and are skipped.

## Standard issue and situational gear

Everything under `skills:` is standard issue: every agent gets it. A source also listed under an `optional:` group is situational, handed out only when asked for.

```bash
./install.harness.sh --agents                  # standard issue only
./install.harness.sh --agents --with apple     # plus one group
./install.harness.sh --agents --with all       # everything
```

Omit the top-level `agents:` key and every agent the CLI detects gets the loadout. Pin it only to narrow the set.

`--dry-run` on any command prints without touching anything. Reach for it before a run that fans out to every agent.

## Releasing

Tag here, bump the formula in [yoshi-ortiz/homebrew-harness-core](https://github.com/yoshi-ortiz/homebrew-harness-core). One tag here, one commit there.

```bash
git tag v0.1.0 && git push --tags
curl -sL https://github.com/yoshi-ortiz/harness-core/archive/refs/tags/v0.1.0.tar.gz | shasum -a 256
```

The digest goes in `sha256`, the tag in `url`, both in `Formula/harness-core.rb`.

Windows is not packaged. The harness is bash and writes POSIX config paths, so it runs under WSL as a Linux install.
