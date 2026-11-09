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
11. imagegen
12. openai-docs
13. review-agent
14. skill-creator
15. skill-installer

# Tools

Tools no Claude Code session loads. `kit tools` and `kit-starter-pack` write them as bare-name deny
rules in `~/.claude/settings.json`, which leave a tool out of context entirely. Bare names and globs only.
Evidence: TokenEconomizer found each unused across 42 sessions and 604 prompts in this repo. The desktop
app's own tools (`ccd_*`, terminal, browser, computer use) are left alone.

1. `mcp__Blender__*`
2. `mcp__Figma__*`
3. `mcp__092ad12a-3008-41b0-a890-65b381d8104c__*`
4. `mcp__Shadcn_UI__*`
5. `mcp__cmux-cua__*`
6. `NotebookEdit`
7. `CronCreate`
8. `CronDelete`
9. `CronList`
10. `RemoteTrigger`
11. `PushNotification`

# Batteries included

The catalog. One bullet per source: `* <img/> [Name](github url): skills`.
No `: skills` offers every skill in the repo; otherwise only the names listed.
The bullet's name is the publisher stamped into each installed skill's `metadata:`.
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
* <img src="https://github.com/hashicorp.png" width="20"> [HashiCorp](https://github.com/hashicorp/agent-skills)

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

## cloud

1. hashicorp/agent-skills:terraform-style-guide
2. hashicorp/agent-skills:terraform-test
3. hashicorp/agent-skills:terraform-stacks
4. hashicorp/agent-skills:terraform-policy
5. hashicorp/agent-skills:aws-ami-builder
6. hashicorp/agent-skills:azure-image-builder
7. hashicorp/agent-skills:azure-verified-modules

## ios

1. using-tuist-generated-projects
2. debug-generated-project
3. fix-flaky-tests

# Helpers

Not installed. Read by hand.

* `okf` skill helper from source scripts: [okf-wiki QUICKSTART](https://github.com/mchu1966/okf-wiki/blob/master/QUICKSTART.md)
* `engineering:*` (system-design and others): installed locally as `engineering@inline`; no source repo known.
* Cloudflare MCP guide (not a skill): [cloudflare/mcp AGENTS.md](https://github.com/cloudflare/mcp/blob/main/AGENTS.md)
* HashiCorp Terraform MCP prompt (not a skill): [developer.hashicorp.com](https://developer.hashicorp.com/terraform/mcp-server/prompt)

# Plugins (MCP drivers)

Not installed. The `skills` CLI installs skills, not MCP servers.

* context7
* [WebMCP](https://developer.chrome.com/docs/ai/webmcp?hl=es-419)
* [chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp)
* playwright
