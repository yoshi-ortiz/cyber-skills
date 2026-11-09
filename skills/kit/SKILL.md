---
name: kit
description: Install only the skills a project needs from the PACK.md catalog, linked into Claude Code and Codex. Use for kit, kit-starter-pack, install skill, add skill, sync skills.
---

# Kit

Run from the project root. Install only what the user named or the project's domain needs.

1. `kit`: `python3 packages.py` verifies and installs nothing.
2. `kit <domain|skill|owner/repo:skill>...`: `python3 packages.py <names>`. Add `-g` for global.
3. `kit add owner/repo`: `python3 packages.py add owner/repo` adds a catalog row.
4. `kit remove <skill>`: `python3 packages.py remove <skill>`.

5. `kit-starter-pack`: `python3 packages.py kit-starter-pack` installs the `core` domain globally. When `kit` prints `first run`, relay that advice to the user.

6. `kit stamp`: `python3 packages.py stamp` writes `publisher`, `source` and `source-url` into each installed skill's `metadata:`. Install stamps automatically; `kit` fails on an unstamped skill.
7. `kit export <skill>`: `python3 packages.py export <skill>` zips it for ChatGPT web, which only takes uploads.

One install reaches every agent that reads `~/.agents/skills`: Codex, the ChatGPT desktop app, Cursor, Antigravity, Zed, Pi. The publisher is the catalog name in PACK.md.

`packages.py` sits next to this file. Domains and sources are in [PACK.md](PACK.md).
Every check fails closed. Read the `FAIL` lines, fix the cause, and run again.
Never pipe the output: the exit code is the result. Never raise a budget to pass.
