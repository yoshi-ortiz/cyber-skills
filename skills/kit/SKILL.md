---
name: kit
disable-model-invocation: true
description: Call any skill from the kit catalog without preloading it, add a domain's MCP servers, or add a source. Use for kit, kit <skill>, kit <domain>, kit add, kit-starter-pack.
---

# Kit

Do exactly what the table says. Do not guess other commands.
`K` means `python3 ~/.agents/skills/kit/packages.py`.

| The user says | Run | Then |
| --- | --- | --- |
| `kit` | `K` | Report the `ok` or `FAIL` lines. On `first run`, run `K kit-starter-pack`. |
| `kit-starter-pack` | `K kit-starter-pack` | Report the last line. |
| `kit <skill>` or `/kit <skill>` | `K use <skill>` | Follow the printed skill. Its files are in the printed `dir`. |
| `kit <domain>`, such as `kit cloud` | `K domain <domain>` | Run it from the project root. Report the MCP servers and the `/publisher:skill` lines. |
| `kit add <github url or owner/repo>` | `K add <url>` | Then run `K kit-starter-pack`. |
| `kit install <skill>` | `K <skill>` | Only when the user asks: it loads in every session. |
| `kit remove <skill>` | `K remove <skill>` | |
| `kit tools` | `K tools` | |

Rules:

1. `use` says a name is offered twice: run `K use owner/repo:<skill>` with the source the user means.
2. A `FAIL` line names the cause and the fix. Do the fix, then run the same command again.
3. Never pipe the output. The exit code is the result.
4. A URL that is not a GitHub repo, or an MCP server, is not a source: add it to [PACK.md](PACK.md) `# MCP servers` as `1. name url-or-command`, and list it in a domain as `mcp:name`.
5. Every catalog skill is already a command: `/publisher:skill` in Claude Code, `$publisher:skill` in Codex.
