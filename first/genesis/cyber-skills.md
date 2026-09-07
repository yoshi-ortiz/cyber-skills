# Extending Genesis with the cyber-yoshi workflow

Genesis runs alone. Every step in `SKILL.md` works in a bare folder with nothing
installed but Python, and nothing on this page is a prerequisite for any of them.

Read this page only when someone asks to arm a machine with the wider workflow,
or when a project has outgrown hand-maintained domain context.

## What the extension adds

`docs/WORK_STYLE.md` names the domains a project works in. A managed collection
turns those names into installed skills on a machine, so the same domain context
arrives in every session instead of being restated in each one.

| Resource | What it is | When to fetch it |
| --- | --- | --- |
| [harness-core](https://github.com/yoshi-ortiz/harness-core) | The installer and its README | Adopting the collection on a machine |
| [collection.toml](https://raw.githubusercontent.com/yoshi-ortiz/harness-core/main/collection.toml) | The domain catalog: which domains exist and which skills each one carries | Mapping the domain names in `docs/WORK_STYLE.md` against real domains |
| [cyber-skills](https://github.com/yoshi-ortiz/cyber-skills) | The package Genesis itself ships in, alongside **/knowledge** and **/aesthetic** | Deciding whether the sibling skills are worth installing |

Fetch the catalog over HTTPS rather than reading a local path. A machine that
has never run the installer has no local copy, and a machine that has one may be
behind the published catalog.

## Adopting it

1. Install the harness by following its README. Genesis does not install it, and
   an agent should not attempt the installation unprompted.
2. `/kit <domain...>` records the domain selection for that machine, naming only
   the domains `docs/WORK_STYLE.md` already declares. Never infer `all`.
3. Leave `docs/WORK_STYLE.md` as the project's own record. The catalog says what
   a machine can install; the project file says what this project works in, and
   the second one survives the machine.

## What stays out

The catalog is a machine's loadout, not project state. Copying its rows into a
project's documents replaces one lookup with a copy that goes stale, and a
project that never adopts the harness still needs its work style written down.
