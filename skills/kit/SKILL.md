---
name: kit
description: Call any skill from the kit catalog (Matt Pocock, pstack, ponytail, superpowers, Anthropic and more) without preloading it. Use for kit <skill>, kit use, install skill, kit-starter-pack.
---

# Kit

The catalog is indexed, not loaded. A skill enters the context only when called.
In Claude Code every catalog skill is also `/<skill>`, or `/<publisher>-<skill>` when two sources share a name. Those load nothing until typed.
Run every command with `python3 ~/.agents/skills/kit/packages.py`.

1. `kit <skill>` or `kit use <skill>`: run `use <skill>`, then follow the printed skill as if it were installed. Its files are in the printed `dir`.
2. If `use` says a name is offered twice, run `use owner/repo:<skill>` with the source the user means.
3. `kit`: no arguments verifies. On `first run`, run `kit-starter-pack` to index the catalog.
4. `kit install <skill> [-g]`: run `<skill> [-g]` to install it for good. Only when the user asks: installed skills are listed in every session.
5. `kit tools`: run `tools` to leave the PACK.md `# Tools` out of every Claude Code session. `kit` fails if one is loaded again.
6. `kit add owner/repo`: run `add owner/repo` to add a catalog row. `kit remove <skill>`: run `remove <skill>`.

Sources and domains are in [PACK.md](PACK.md). Every check fails closed: read the `FAIL` lines, fix the cause, and run again.
Never pipe the output: the exit code is the result.
