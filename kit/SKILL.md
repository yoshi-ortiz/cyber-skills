---
name: kit
description: Install and sync the default skill loadout and MCP tools from GitHub through harness-core, the collection every AI app carries. Bare kit syncs the default rows; kit followed by a domain uncomments that domain on the owner's say-so. Also answers to install, setup, init, start, starter, sync, update, refresh, upgrade, doctor, repair, troubleshoot, conflict, and starter-pack. Use to fetch the harness, re-arm apps, add a skill, or diagnose the collection.
also:
  - starter-pack :: Same skill, its original name
---

# Kit

| Say | Do |
| --- | --- |
| `kit`, `sync`, `update`, `refresh`, `upgrade`, `install`, `setup`, `init`, `start`, `starter`, `starter-pack`, **with no source named** | **Sync.** `harness.py sync` installs the default loadout: every uncommented row in `collection.toml`, plus its `[mcp]` servers, cloning the harness first if it is missing. |
| `kit <domain>`, such as `kit design`; more than one may be named | **Domain.** A domain is a `[skills.<domain>]` table. Show its commented rows, uncomment only the ones the owner names, then Sync. Never infer `all`, and never pass `--all`. |
| any of those **followed by a source**, such as `sync cyber-skills` | **One source.** `harness.py sync <source>`, matched as a substring. Named a source, meant that source. |
| `sync dev`, `dev install`, or any attempt to run your own unpushed work | **Dev install.** Sync clones channels from GitHub, so it can never serve `dev`. `python3 tools/dev_install.py` symlinks this checkout over the installed copies instead, and your edits are live with no sync at all. Re-run it after any sync, which puts copies back. To reach your *other* machines there is no shortcut: publish first, `python3 tools/release.py --channel alpha --push`, then sync. |
| `doctor`, `repair`, `troubleshoot`, `conflict` | **Fix.** Something installed wrong, or two things collided. Bare `fix` owns code, context and tool recovery; it uses Kit for managed collection setup and returns to verify recovery. |

Never ask which. Sync is idempotent, so there is no separate Install mode to
pick wrong: running it where the harness already exists syncs it instead of
breaking it. Releasing this package is Repo-Dev work and is not a mode here.

For ambiguous domains, use [Jev](references/jev.md) when configured. Show its
candidate; activate only the owner's explicit choice.

Everything below the two modes is reference. Read one when the task names it.

One collection, one harness. `collection.toml` is the install: an uncommented
row is installed by default, a commented row is offered but not installed.
`selected` names the categories sync walks, and `add` appends rows to the
same file, so commit local rows in `~/.harness-core` before pulling. Kit fetches `harness-core` from GitHub and runs
its local script; it does not install package managers, runtimes, or shell
hooks. Source of truth for anything not here: [the harness README](https://github.com/yoshi-ortiz/harness-core).

## Report it while it runs

Install and Sync fan out over every source and every app. That takes minutes.
Keep the whole log:

```bash
set -o pipefail
git -C ~/.harness-core pull --ff-only
python3 ~/.harness-core/harness.py sync 2>&1 | tee /tmp/kit.log
```

**Never pipe it through `tail` or `head`.** It drops the failures and swaps
the harness exit code for the pager's, so a run that died partway reads as a
clean success.

If it outruns your tool timeout, background it, say so in chat, and report
progress rather than going quiet. The harness prints one line per repo and ends
in a count, so `tail -1 /tmp/kit.log` is the position.

## Fetch and sync

```bash
git clone --depth 1 https://github.com/yoshi-ortiz/harness-core.git ~/.harness-core 2>/dev/null \
  || git -C ~/.harness-core pull --ff-only
python3 ~/.harness-core/harness.py sync
```

The checkout needs `git` and Node/npm; Kit installs neither and adds no PATH
shim. On Windows, run the same fetch from Git Bash or PowerShell.

## Sync

Sync is the idempotent re-fetch. Pulling the checkout first refreshes
`collection.toml` and the harness code, so a source added upstream arrives with
it. There is no separate installer upgrade path.

It fans out over every uncommented source in the `selected` categories.
Naming a source after `sync` filters by repository name. Sync never deletes:
a skill whose row was commented stays installed until removed from
`~/.agents/skills` and each app's skills dir.

`python3 ~/.harness-core/harness.py status` prints what is selected, what was
detected, and how many skills are installed. Read it before and after.

## Fix

Every command above starts with the same literal text, `python3
~/.harness-core/harness.py`, so one standing permission rule covers every mode. A path built from `$HARNESS_DIR` reads as a different command each time
and has to be approved again on every run. Relocate the checkout by cloning it
elsewhere and writing your own rule; the default path stays literal so the
common case is approved once.

Start with `harness.py status`. It is read-only and answers the two questions that
matter first, which agents were detected and which categories are on.

| Symptom | Cause | Do |
| --- | --- | --- |
| A skill in the repo never arrives | Its manifest entry names a subset, so a skill added later is not in the list | Make the entry bare, or add the new name to the list |
| A whole domain is absent | Its rows are commented, or `selected` omits it | Uncomment the rows the owner names, or `harness.py onboard`, then `harness.py sync` |
| `git pull` refuses in `~/.harness-core` | `add` or a hand edit left `collection.toml` dirty | Commit the rows locally, then pull |
| An app cannot see a new skill | Skill lists load at session start | Start a new chat |
| A skill behaves like an older version | A stale directory survived a rename; nothing deletes it | Remove it from that app's skills dir, then `harness.py sync` |
| A skill I just edited syncs without my edit | Sync clones the source from GitHub; an uncommitted or unpushed edit is not there yet | Commit and push, then sync. To test the edit itself, run it from the checkout |
| agy or Cursor sees nothing while Claude Code is fine | Those dirs are populated by `sync-skills.sh`, not the `skills` CLI | `harness.py sync`, which runs it after every install |
| A built-in such as `/resume` runs a skill | A skill folder named after a built-in shadows it ([B-036](../BUGS.md)) | Follow [B-036](../BUGS.md); `harness.py status` must exit 0 |
| An edit to `collection.toml` changed nothing | Editing installs nothing | `harness.py sync` |

`--dry-run` before any run that fans out. Never fix by hand-editing an app's
skills dir and stopping there, the manifest is the source of truth and the next
sync undoes anything it does not know about.

## Add a skill

`harness.py add owner/repo [skill] --category <name>` appends the row to
`collection.toml` **and** installs it. `--no-save` installs without
recording. Sources belong in `collection.toml` once they are worth sharing;
`add` is for this machine.

Name skills only for a **subset**. A list naming every skill in a repo behaves
like a bare entry and then rots, because the repo adds a skill and the list
silently stops handing it out. Check a repo's set with `npx skills add <repo> -l`.

Never pass `--all` to `npx skills add`.

## Where skills land

`npx skills add` writes the canonical copy to `~/.agents/skills/`, then
symlinks it per agent. Claude Code and Pi are handled by the `skills` CLI.
agy, Codex, and Cursor are not, and `scripts/sync-skills.sh` closes that gap
after every install. Agents on a mounted OS partition are synced too, with
relative symlinks that survive the remount, and anything without a
`.harness-managed` marker is left alone.

## Release

Tagging the harness is documented once, in
[the harness README](https://github.com/yoshi-ortiz/harness-core).
Copying it here is how the two drift.
