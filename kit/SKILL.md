---
name: kit
description: Operating guide for the harness-core skill loadout every AI app on a machine carries. Bare kit installs. Also answers to install, setup, init, start, sync, update, refresh, upgrade, fix, doctor, repair, troubleshoot, conflict, and to starter-pack, its original name. Use when the user wants the harness fetched, every app re-armed with the current skill selection, a skill added, or a broken collection diagnosed.
disable-model-invocation: true
also:
  - starter-pack :: Same skill, its original name
---

# Kit

| Say | Do |
| --- | --- |
| `kit`, `install`, `setup`, `init`, `start` | **Install.** Bare `kit` means this. |
| `sync`, `update`, `refresh`, `upgrade` | **Sync.** Re-arm every app at the latest version. |
| `fix`, `doctor`, `repair`, `troubleshoot`, `conflict` | **Fix.** Something installed wrong, or two things collided. |

Never ask which. Every mode ends in the same idempotent re-fetch, so running
Install on a machine that already has it syncs it instead of breaking it.

Everything below the three modes is reference. Read one when the task names it.

One collection, one harness. `collection.yaml` records which skills this
machine carries. Kit fetches `harness-core` from GitHub and runs
its local script; it does not install package managers, runtimes, or shell
hooks. Source of truth for anything not here: [the harness README](https://github.com/yoshi-ortiz/harness-core).

## Report it while it runs

Install and Sync fan out over every source and every app. That takes minutes.
Keep the whole log:

```bash
HARNESS_DIR="${HARNESS_DIR:-$HOME/.harness-core}"
git -C "$HARNESS_DIR" pull --ff-only
bash "$HARNESS_DIR/pony.harness.sh" sync 2>&1 | tee /tmp/kit.log
```

**Never pipe it through `tail` or `head`.** That discards the failures and
replaces the harness exit code with the pager's, so a run that died a third of
the way through reads as a clean success.

If it outruns your tool timeout, background it, say so in chat, and report
progress rather than going quiet. The harness prints one line per repo and ends
in a count, so `tail -1 /tmp/kit.log` is the position.

## Fetch and sync

```bash
HARNESS_DIR="${HARNESS_DIR:-$HOME/.harness-core}"
if [[ -d "$HARNESS_DIR/.git" ]]; then
  git -C "$HARNESS_DIR" pull --ff-only
else
  git clone --depth 1 https://github.com/yoshi-ortiz/harness-core.git "$HARNESS_DIR"
fi
bash "$HARNESS_DIR/pony.harness.sh" sync
```

The checkout must already have `git`, `yq`, and Node/npm. Kit does
not install them or add a PATH shim. Use the same Git fetch from Git Bash or
PowerShell on Windows. Start a new agent session after syncing because skill
lists are read at session start.

## Sync

```bash
HARNESS_DIR="${HARNESS_DIR:-$HOME/.harness-core}"
git -C "$HARNESS_DIR" pull --ff-only
bash "$HARNESS_DIR/pony.harness.sh" sync
```

Sync is the idempotent re-fetch. Pulling the checkout first refreshes
`collection.yaml` and the harness code, so a source added upstream arrives with
it. There is no separate installer upgrade path.

`bash "$HARNESS_DIR/pony.harness.sh" status` prints what is selected, what was
detected, and how many skills are installed. Read it before and after.

## Fix

Start with `harness status`. It is read-only and answers the two questions that
matter first, which agents were detected and which categories are on.

| Symptom | Cause | Do |
| --- | --- | --- |
| A skill in the repo never arrives | Its manifest entry names a subset, so a skill added later is not in the list | Make the entry bare, or add the new name to the list |
| A whole category is absent | `selected:` omits it | `harness onboard`, or `--all` to clear the selection |
| An app cannot see a new skill | Skill lists load at session start | Start a new chat |
| A skill behaves like an older version | A stale directory survived a rename; nothing deletes it | Remove it from that app's skills dir, then `harness sync` |
| agy or Cursor sees nothing while Claude Code is fine | Those dirs are populated by `sync-skills.sh`, not the `skills` CLI | `harness sync`, which runs it after every install |
| An edit to `collection.yaml` changed nothing | Editing installs nothing | `harness sync` |

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
