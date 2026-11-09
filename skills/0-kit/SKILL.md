---
name: 0-kit
description: Install only the skills a project needs from the PACK.md catalog, linked into Claude Code and Codex. Use for kit, install skill, add skill, sync skills.
---

# Kit

Run from the project root. Install only what the user named or the project's domain needs.

1. `kit`: `python3 packages.py` verifies and installs nothing.
2. `kit <domain|skill|owner/repo:skill>...`: `python3 packages.py <names>`. Add `-g` for global.
3. `kit add owner/repo`: `python3 packages.py add owner/repo` adds a catalog row.
4. `kit remove <skill>`: `python3 packages.py remove <skill>`.

`packages.py` sits next to this file. Domains and sources are in [PACK.md](PACK.md).
Every check fails closed. Read the `FAIL` lines, fix the cause, and run again.
Never pipe the output: the exit code is the result. Never raise a budget to pass.
