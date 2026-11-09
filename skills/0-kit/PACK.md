# Kit pack

Read by `packages.py`, never loaded into an agent, so this file can grow.
Nothing here installs by itself. `kit <domain>` or `kit <skill>` installs only what it names.

# Agents

The universal store `.agents/skills` serves every agent that reads it (Codex, Cursor,
Antigravity, Cline, Amp and others). Other agents listed here get symlinks into the store.
`*` is refused: it makes real copies for some agents.

1. claude-code
2. codex
3. pi
4. cursor
5. zed
6. antigravity

# Agent-owned

Entries the agents ship or manage themselves. Kit ignores these names in agent skill folders.

1. check-work
2. code-review
3. create-skill
4. docx
5. help
6. imagine
7. pptx
8. xlsx
9. synced
10. hatch-pet

# Batteries included

The catalog. One bullet per source: `* <img/> [Name](github url): skills`.
No `: skills` offers every skill in the repo; otherwise only the names listed.
A bullet here that does not parse fails the run.

* <img src="https://github.com/mattpocock.png" width="20"> [Matt Pocock](https://github.com/mattpocock/skills)
* <img src="https://github.com/addyosmani.png" width="20"> [Addy Osmani](https://github.com/addyosmani/agent-skills)
* <img src="https://github.com/backnotprop.png" width="20"> [pstack](https://github.com/backnotprop/pstack)
* <img src="https://github.com/DietrichGebert.png" width="20"> [ponytail](https://github.com/DietrichGebert/ponytail)
* <img src="https://github.com/obra.png" width="20"> [superpowers](https://github.com/obra/superpowers)
* <img src="https://github.com/google.png" width="20"> [Elephant Goldfish Model](https://github.com/google/elephant-goldfish-model)
* <img src="https://github.com/microsoft.png" width="20"> [TokenEconomizer](https://github.com/microsoft/TokenEconomizer)
* <img src="https://github.com/googlechrome.png" width="20"> [Modern Web Guidance](https://github.com/googlechrome/modern-web-guidance)
* <img src="https://github.com/tuist.png" width="20"> [Tuist](https://github.com/tuist/agent-skills)
* <img src="https://github.com/anthropics.png" width="20"> [Anthropic](https://github.com/anthropics/skills)
* <img src="https://github.com/upstash.png" width="20"> [Context7](https://github.com/upstash/context7)

# Domains

What to install per project domain. Write a skill as its name, or as `owner/repo:name`
when two sources offer it. `owner/repo` alone means every skill the catalog offers from it.

## core

1. ponytail
2. ponytail-review
3. handoff
4. diagnosing-bugs
5. codebase-design
6. mattpocock/skills:tdd
7. writing-for-agents
8. research

## architecture

1. backnotprop/pstack:architect
2. improve-codebase-architecture

## web

1. frontend-design
2. modern-web-guidance
3. frontend-ui-engineering

## docs

1. context7-mcp

## ios

1. using-tuist-generated-projects
2. debug-generated-project
3. fix-flaky-tests

# Helpers

Not installed. Read by hand.

* `okf` skill helper from source scripts: [okf-wiki QUICKSTART](https://github.com/mchu1966/okf-wiki/blob/master/QUICKSTART.md)
* `engineering:*` (system-design and others): installed locally as `engineering@inline`; no source repo known.

# Plugins (MCP drivers)

Not installed. The `skills` CLI installs skills, not MCP servers.

* context7
* [WebMCP](https://developer.chrome.com/docs/ai/webmcp?hl=es-419)
* [chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp)
* playwright
