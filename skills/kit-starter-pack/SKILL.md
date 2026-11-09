---
name: kit-starter-pack
description: First-run setup. Indexes every kit catalog skill so any of them can be called with kit, without loading any into the session. Use for kit-starter-pack, starter pack, first run.
---

# Kit starter pack

Run `python3 ~/.agents/skills/kit/packages.py kit-starter-pack`. It needs the `kit` skill.

It clones and indexes every catalog source into `~/.cache/kit` and installs nothing.
It also writes a Claude Code `/command` for each skill that loads nothing until typed.
Afterwards, call any skill with `/<skill>` in Claude Code, or `kit <skill>` in any agent. Run it again to refresh the index.
Read any `FAIL` line, fix the cause, and run again. Never pipe the output.
