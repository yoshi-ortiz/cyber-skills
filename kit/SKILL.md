---
name: kit
description: Operating guide for the harness-core skill loadout every AI app carries. Bare kit syncs. Also answers to install, setup, init, start, sync, update, refresh, upgrade, fix, doctor, repair, troubleshoot, conflict, and starter-pack. Use to fetch the harness, re-arm apps, add a skill, or diagnose the collection.
disable-model-invocation: true
also:
  - starter-pack :: Same skill, its original name
---

# Kit

| Say | Do |
| --- | --- |
| `kit`, `sync`, `update`, `refresh`, `upgrade`, `install`, `setup`, `init`, `start`, `starter-pack`, **with no source named** | **Sync.** Re-arm every app at the latest version, cloning the harness first if it is missing. Bare `kit` means this, in every directory, a Repo-Dev checkout included. |
| any of those **followed by a source**, such as `sync cyber-skills` | **One source.** `harness.py sync <source>`, matched as a substring. Named a source, meant that source. |
| `fix`, `doctor`, `repair`, `troubleshoot`, `conflict` | **Fix.** Something installed wrong, or two things collided. |

Never ask which. Sync is idempotent, so there is no separate Install mode to
pick wrong: running it where the harness already exists syncs it instead of
breaking it. Releasing this package is Repo-Dev work and is not a mode here.

Everything below the two modes is reference. Read one when the task names it.

One collection, one harness. `collection.toml` records which skills this
machine carries. Kit fetches `harness-core` from GitHub and runs
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

**Never pipe it through `tail` or `head`.** That discards the failures and
replaces the harness exit code with the pager's, so a run that died a third of
the way through reads as a clean success.

If it outruns your tool timeout, background it, say so in chat, and report
progress rather than going quiet. The harness prints one line per repo and ends
in a count, so `tail -1 /tmp/kit.log` is the position.

## Fetch and sync

```bash
git clone --depth 1 https://github.com/yoshi-ortiz/harness-core.git ~/.harness-core 2>/dev/null \
  || git -C ~/.harness-core pull --ff-only
python3 ~/.harness-core/harness.py sync
```

The checkout must already have `git` and Node/npm. `yq` is no longer needed:
the manifest is TOML and `tomllib` is standard library. Kit does not install
them or add a PATH shim. Use the same Git fetch from Git Bash or
PowerShell on Windows. Start a new agent session after syncing because skill
lists are read at session start.

## Sync

```bash
git -C ~/.harness-core pull --ff-only
python3 ~/.harness-core/harness.py sync
```

Sync is the idempotent re-fetch. Pulling the checkout first refreshes
`collection.toml` and the harness code, so a source added upstream arrives with
it. There is no separate installer upgrade path.

**It fans out over every source in `collection.toml`.** Naming one after `sync`
filters to sources whose name contains it, so re-fetching twenty-odd repos to
update the one that was asked for never happens; see the table above.

`python3 ~/.harness-core/harness.py status` prints what is selected, what was
detected, and how many skills are installed. Read it before and after.

## Fix

Every command above starts with the same literal text, `python3
~/.harness-core/harness.py`, so one standing permission rule covers every mode. A path built from `$HARNESS_DIR` reads as a different command each time
and has to be approved again on every run. Relocate the checkout by cloning it
elsewhere and writing your own rule; the default path stays literal so the
common case is approved once.

Start with `harness status`. It is read-only and answers the two questions that
matter first, which agents were detected and which categories are on.

| Symptom | Cause | Do |
| --- | --- | --- |
| A skill in the repo never arrives | Its manifest entry names a subset, so a skill added later is not in the list | Make the entry bare, or add the new name to the list |
| A whole category is absent | `selected:` omits it | `harness onboard`, or `--all` to clear the selection |
| An app cannot see a new skill | Skill lists load at session start | Start a new chat |
| A skill behaves like an older version | A stale directory survived a rename; nothing deletes it | Remove it from that app's skills dir, then `harness sync` |
| A skill I just edited syncs without my edit | Sync clones the source from GitHub; an uncommitted or unpushed edit is not there yet | Commit and push, then sync. To test the edit itself, run it from the checkout |
| agy or Cursor sees nothing while Claude Code is fine | Those dirs are populated by `sync-skills.sh`, not the `skills` CLI | `harness sync`, which runs it after every install |
| An edit to `collection.toml` changed nothing | Editing installs nothing | `harness sync` |

`--dry-run` before any run that fans out. Never fix by hand-editing an app's
skills dir and stopping there, the manifest is the source of truth and the next
sync undoes anything it does not know about.

## Add a skill

`harness add owner/repo [skill]` records the source **and** installs it.
`--category <name>` files it, `--no-save` installs without touching the
manifest.

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
