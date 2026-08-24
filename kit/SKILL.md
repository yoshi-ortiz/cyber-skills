---
name: kit
description: Operating guide for the agent-skills harness, the loadout of tools every agent carries. Bare kit installs. Also answers to install, setup, init, start, sync, update, refresh, upgrade, fix, doctor, repair, troubleshoot, conflict, and to starter-pack, its original name. Use when the user wants the harness set up on a machine, every agent re-armed with the current manifest, a skill or MCP server added to the collection, a broken or conflicting collection diagnosed, or a release tagged.
disable-model-invocation: true
also:
  - starter-pack :: Same skill, its original name
---

# Kit

| Say | Do |
| --- | --- |
| `kit`, `install`, `setup`, `init`, `start` | **Install.** Bare `kit` means this. |
| `sync`, `update`, `refresh`, `upgrade` | **Sync.** Re-arm every agent with the current manifest. |
| `fix`, `doctor`, `repair`, `troubleshoot`, `conflict` | **Fix.** Something installed wrong, or two things collided. |

Never ask which. Install ends in the same command Sync runs, so installing a
machine that is already set up syncs it instead of breaking it.

Everything below the three modes is reference. Read one when the task names it.

Every agent on this machine runs the same **loadout**: the skills and MCP servers that give it reach beyond its own weights. `collection.yaml` records that loadout, `install.harness.sh` arms every agent with it by calling each agent's own CLI. One collection, one harness. Source of truth for anything not here: [the harness README](https://github.com/yoshi-ortiz/harness-core).

## Report it while it runs

Both Install and Sync fan out over every source and every app. That takes
minutes. The harness prints `[i/N]` per unit, so keep the whole log:

```bash
harness --agents 2>&1 | tee /tmp/kit.log
```

**Never pipe it through `tail` or `head`.** That discards the failures and
replaces the harness exit code with the pager's, so a run that died at source
11 of 30 reads as a clean success.

If it outruns your tool timeout, background it, say so in chat, and report
position rather than going quiet:

```bash
grep '^\[' /tmp/kit.log | tail -1
```

It ends in a verdict. Either `✓ 30/30 armed`, or the list of what failed and a
non-zero exit. A failure never stops the run, so the rest is already armed and
a re-run only has to clear what it named.

## Install

```bash
brew tap yoshi-ortiz/harness-core
brew install harness-core
harness init                     # checks tools, reports secrets, lists groups
harness --agents                 # arms every agent. init alone arms nothing.
```

macOS and Homebrew for Linux. Or clone the repo and run `./install.harness.sh` in place; it needs [yq](https://github.com/mikefarah/yq) and Node, both pulled in by the formula.

`init` is read-only. Run it first so a missing secret surfaces before the fan-out, never instead of the fan-out.

## Sync

Re-running the install **is** the update. `--agents` reinstalls every source at its current version.

```bash
brew upgrade harness-core        # the harness itself, when installed that way
harness --agents                 # every skill and MCP server, every agent
```

Two things it will not touch. A skill installed by hand, outside `collection.yaml`, is invisible to the harness: add the source first or it never updates. And second names from `/silly` live in each agent's own skills folder, so they are relinked per folder, not by this.

Then tell the user to start a new chat.

## Fix

Start with `harness init`. It is read-only and reports the two things that
break most often: a missing tool and an unset secret.

| Symptom | Cause | Do |
| --- | --- | --- |
| `✗ skipped failed source` in the output | One repo failed. The rest still installed. | Re-run that one: `./install.harness.sh skills add owner/repo` |
| An MCP server never appears | Its `header_env` variable is unset, so the harness skipped it rather than arm an agent with a broken one | `export` the variable, then `harness --agents` |
| A skill is in `collection.yaml` but no agent has it | A hand edit to the manifest installs nothing | `harness --agents` |
| An agent still cannot see a new skill | Skills load at session start | Start a new chat |
| A skill behaves like an older version of itself | A stale directory survived a rename or a manual install; nothing deletes it | Remove that directory from the agent's skills folder, then `harness --agents` |
| A setting you never wrote keeps winning | `collection.local.yaml` deep-merges over the manifest and is gitignored, so it is invisible in git | Read it. It sits beside `collection.yaml`. |
| Two sources ship a skill of the same name | Both install to the same folder under `~/.agents/skills/`, so the last one wins | `npx skills add <repo> -l` on each, then name a subset in the manifest |
| `alias.py` refuses to link a name | A real skill already owns it | Rename the alias. Never delete the skill to make room. |

`--dry-run` before any fix that fans out to every agent.

Never fix by hand-editing an agent's skills folder and stopping there. The
manifest is the source of truth, and the next `--agents` undoes anything the
manifest does not know about.

## Locate the loadout

- Git checkout → the `collection.yaml` beside the harness, edited in place.
- Homebrew install → `${XDG_CONFIG_HOME:-~/.config}/agent-skills/collection.yaml`, seeded once and never overwritten by an upgrade. `AGENT_SKILLS_HOME` overrides.

`collection.local.yaml` is gitignored and deep-merged over it at read time: private sources, pinned agents, per-field overrides. Local wins on conflict. Writes from `skills add` and `mcp add` always land in `collection.yaml`, never the overlay.

## Add a skill

1. Run `./install.harness.sh skills add owner/repo [skill]`. It records the source **and** arms every agent. A hand edit to `collection.yaml` gives no agent anything; follow one with `./install.harness.sh --agents`.
2. Name skills only for a **subset**. A list that names every skill in the repo behaves like a bare entry and rots. The repo adds a skill, the list silently stops handing it out. Check the repo's set with `npx skills add <repo> -l`.
3. Never pass `--all` to `npx skills add`.
4. Tell the user to start a new Cursor chat. Skills land in `~/.agents/skills/`, symlink into `~/.cursor/skills/`, and each agent reads its loadout at session start.

A source that needs more than the CLI gets `{ install: script }` under its key and a script in `scripts/`.

## Add an MCP server

`./install.harness.sh mcp add <name> <url|command>`. Each server is a name plus one transport: `url` for http, `command` for stdio, never both.

**Secrets never live in `collection.yaml`.** `header_env` names an environment variable; the harness reads it at install time and sends `<NAME>: <value>`. An unset variable skips that server rather than arming an agent with a broken one, so export it before running.

Reach: claude-code, antigravity, codex, and cursor each get the server (codex has no custom-header flag and skips the header with a warning). `pi` and `zed` expose no add command and are skipped.

## Hand out standard or situational gear

Everything under `skills:` is standard issue: every agent gets it. A source also listed under an `optional:` group is situational, handed out only when asked for.

```bash
./install.harness.sh --agents                  # standard issue only
./install.harness.sh --agents --with apple     # plus one group
./install.harness.sh --agents --with all       # everything
```

Omit the top-level `agents:` key and every agent the CLI detects gets the loadout. Pin it only to narrow the set.

`--dry-run` on any command prints without touching anything. Reach for it before a run that fans out to every agent.

## Release

Tagging the harness and bumping the Homebrew formula is documented once, in
[the harness README](https://github.com/yoshi-ortiz/harness-core#releasing).
Copying it here is how the two drift.
