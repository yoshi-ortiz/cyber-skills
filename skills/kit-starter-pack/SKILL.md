---
name: kit-starter-pack
disable-model-invocation: true
description: First-run setup and refresh. Makes every kit catalog skill a command in Claude Code and Codex without loading any into the session. Use for kit-starter-pack, starter pack, first run.
---

# Kit starter pack

Run `python3 ~/.agents/skills/kit/packages.py kit-starter-pack`, then report its last line.

It indexes every catalog source into `~/.cache/kit`, installs one plugin per publisher into Claude Code
and Codex, and denies the PACK.md `# Tools`. Each skill then runs as `/publisher:skill` in Claude Code or
`$publisher:skill` in Codex, and loads only when typed. Run it again to refresh.

Read any `FAIL` line, do the fix it names, and run again. Never pipe the output.
