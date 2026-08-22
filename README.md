<div align="center">

![Cyber Skills — Intelligent + Easy Prompts](assets/cover.png)

**Tested prompts created by a silly deterministic nerd**

[![release](https://img.shields.io/badge/release-0.9--beta-8b5cf6?style=flat-square&labelColor=1e1b4b)](https://github.com/yoshi-ortiz/cyber-skills/releases)
[![repo](https://img.shields.io/badge/repo-yoshi--ortiz%2Fcyber--skills-0ea5e9?style=flat-square&labelColor=1e1b4b)](https://github.com/yoshi-ortiz/cyber-skills)
[![skills](https://img.shields.io/badge/skills-2-6366f1?style=flat-square&labelColor=1e1b4b)](https://github.com/yoshi-ortiz/cyber-skills#-skills)
[![python](https://img.shields.io/badge/python-stdlib%20only-16213e?style=flat-square&labelColor=1e1b4b)](aesthetic/SKILL.md)
[![token tested](https://img.shields.io/badge/token%20tested-pending-f59e0b?style=flat-square&labelColor=44403c)](#goals)
[![cybersecurity tested](https://img.shields.io/badge/cybersecurity%20tested-pending-f59e0b?style=flat-square&labelColor=44403c)](#goals)
[![publish](https://img.shields.io/badge/publish-main%20%E2%86%90%20dev-312e81?style=flat-square&labelColor=1e1b4b)](tools/CONTEXT.md)

Python stdlib only · Plug and play

</div>

---

## What is this?

**cyber-skills** is a collection of [Agent SKILLS](https://github.com/vercel-labs/skills) — expert prompts a coding agent runs when `/inserted` during chat or loaded on tool context search. The main skill is **Aesthetic**: a local design-review loop with a browser ranking companion. Everything else here is optional misc.

---

## 🖨️ Install

Pick **one** path. All end with skill files on disk and a **new chat** in your agent (skills load at session start, not mid-conversation).

**A)** Add as an app plugin (manual path)  
**B)** Add and sync with [Vercel Skills CLI](https://github.com/vercel-labs/skills) *(recommended)*  
**C)** Clone this repository *(same as step 1 in A)*

### A — Add as a plugin

Register the skill folder with your agent — each app has its own skills directory.

1. **Get the files** — clone or submodule:

   ```bash
   git clone https://github.com/yoshi-ortiz/cyber-skills.git
   ```

2. **Link the skill** into the agent path:

   | Agent | Typical skills path | What to link or copy |
   | --- | --- | --- |
   | Cursor | `~/.cursor/skills/aesthetic` | `cyber-skills/aesthetic/` |
   | Claude Code | `~/.claude/skills/aesthetic` | same |
   | Codex / others | see agent docs | same folder contents |

   Symlink example (Cursor):

   ```bash
   ln -s "$(pwd)/cyber-skills/aesthetic" ~/.cursor/skills/aesthetic
   ```

3. **Open a new chat** and invoke the skill by name or with a prompt like: *“Use aesthetic — give me the ranking URL first.”*

> **Note:** Path A does not run the Vercel installer’s agent detection. You place the folder where *your* agent reads skills. Path B does that for you.

### B — Vercel sync script (recommended)

Uses [`npx skills add`](https://github.com/vercel-labs/skills). Works from any terminal; no clone required.

```bash
# List skills in this repo
npx skills add yoshi-ortiz/cyber-skills --list

# Install Aesthetic globally → Cursor
npx skills add yoshi-ortiz/cyber-skills --skill aesthetic -g -a cursor -y

# Same skill → multiple agents
npx skills add yoshi-ortiz/cyber-skills --skill aesthetic -g \
  -a cursor -a claude-code -a codex -y

# Optional misc skill (Spanish voice)
npx skills add yoshi-ortiz/cyber-skills --skill ora -g -a cursor -y
```

| Flag | What it does |
| --- | --- |
| `-g`, `--global` | User-level install (`~/.cursor/skills/`, `~/.claude/skills/`, …) — not tied to one project |
| `-a`, `--agent <id>` | **Target agent.** Repeat per agent. Files land only where that agent looks for skills. |
| `-s`, `--skill <name>` | Folder in this repo: `aesthetic`, `ora` |
| `-y`, `--yes` | Non-interactive; skip prompts |

Common `-a` values: `cursor`, `claude-code`, `codex`, `opencode`, `zed`, `pi`, `antigravity`.

---

## Index

1. [Aesthetic](#aesthetic) — design ranking companion (main skill)
2. [Ora](#ora) — Spanish conclusion voice (misc)

---

# 📚 Skills

## /Aesthetic

![Aesthetic ranking companion — screenshot placeholder](assets/aesthetic-companion.svg)

*Ranking article in the local companion — replace `assets/aesthetic-companion.svg` with a real capture.*

| | |
| --- | --- |
| **Package** | [aesthetic/](aesthetic/) |
| **Entry** | [aesthetic/SKILL.md](aesthetic/SKILL.md) |
| **Invoke** | Agent-auto · also via agent UI default prompt in [agents/openai.yaml](aesthetic/agents/openai.yaml) |
| **Runs on** | Your **project** directory (never this repo) |

#### Description

Design and art direction that reads as **intentional, not templated**. The agent proposes HTML/CSS comps, renders PNGs, publishes a ranking page in a local browser companion, and reads stars / likes back into a durable ledger that shapes the next cohort. Grounded in design fundamentals, optional multimodal corpus, and element-level user feedback — not a single vibes score.

**You:** open the companion URL, rank 3–6 proposals, leave notes.  
**Agent:** infer direction, publish the next testable cohort, repeat.

#### Arguments

Natural-language modes (context clues in chat — not CLI flags):

| Mode | When |
| --- | --- |
| `continue` | Resume from latest ledger state; one new 3–6 element cohort |
| `critique` | Report mismatches without changing ranks or scope |
| `prototype` | Draw and publish comps for ranking |
| `observe` | Ingest a reference folder as corpus evidence |

Project paths (every script also accepts `--help`):

| Argument | Used by | Meaning |
| --- | --- | --- |
| `--project-root` | all harness scripts | Root of the **target project** (where `project.json`, ledger, and comps live) |
| `--source-root` | `init`, `observe` | Absolute path to read-only inspiration / corpus folder |
| `--cohort` | `article`, `review_delivery` | Comma-separated element ids for this round (max 6) |
| `--companion-ledger` | `adopt` | Path to companion click log (usually `.superpowers/brainstorm/decisions.jsonl`) |

Agent handoff shape (first reply, no preamble): URL · session key · project-language review ask — see [user-communication.md](aesthetic/references/user-communication.md).

#### Scripts

Runtime entry points (stdlib Python 3). Full flag lists: [references/commands.md](aesthetic/references/commands.md).

| Script | Role |
| --- | --- |
| [bootstrap_harness.py](aesthetic/scripts/bootstrap_harness.py) | Companion, ledger, article, publish |
| [editorial_workflow.py](aesthetic/scripts/editorial_workflow.py) | Corpus, preferences, direction, burndown |
| [golden_rules.py](aesthetic/scripts/golden_rules.py) | Rule coverage gate on a design spec |
| [review_delivery.py](aesthetic/scripts/review_delivery.py) | Staged review PNGs; rejects generic / drifted comps |
| [brief_workflow.py](aesthetic/scripts/brief_workflow.py) | Element brief generation |
| [burndown_view.py](aesthetic/scripts/burndown_view.py) | Burndown inspection |
| [companion_doctor.py](aesthetic/scripts/companion_doctor.py) | Companion health diagnostics |
| [asset_contract.py](aesthetic/scripts/asset_contract.py) | Asset provenance checks |

`bootstrap_harness.py` **subcommands:** `open` · `init` · `validate` · `decide` · `describe` · `retire` · `adopt` · `shoot` · `article` · `embed` · `publish` · `status` · `controls` · `preflight` · `doctor` · `stats` · `audit-svg` · `self-test`

`editorial_workflow.py` **subcommands:** `observe` · `seed` · `preferences` · `direction` · `scope` · `advance` · `status`

**Companion (Node, vendored):** [companion/](aesthetic/companion/) — `install.sh`, `start-server.sh`, `server.cjs` · contract: [companion-contract.md](aesthetic/references/companion-contract.md)

Minimal first run:

```bash
python3 <skill>/scripts/bootstrap_harness.py init --project-root <project>
python3 <skill>/scripts/bootstrap_harness.py open --project-root <project>
```

#### References

Self-contained doctrine under [aesthetic/references/](aesthetic/references/) (OKF 0.2). Index: [references/index.md](aesthetic/references/index.md).

| Group | Docs |
| --- | --- |
| Golden rules | [golden-rules.md](aesthetic/references/golden-rules.md), [graphic-design-fundamentals.md](aesthetic/references/graphic-design-fundamentals.md), [aesthetics-philosophy.md](aesthetic/references/aesthetics-philosophy.md), [art-history.md](aesthetic/references/art-history.md) |
| Inference | [sentiment-analysis.md](aesthetic/references/sentiment-analysis.md), [interpret-art.md](aesthetic/references/interpret-art.md), [loop.md](aesthetic/references/loop.md), [anti-slop.md](aesthetic/references/anti-slop.md), [stats.md](aesthetic/references/stats.md) |
| Contracts | [commands.md](aesthetic/references/commands.md), [companion-contract.md](aesthetic/references/companion-contract.md), [editorial-workflow.md](aesthetic/references/editorial-workflow.md), [asset-sourcing.md](aesthetic/references/asset-sourcing.md), [verification.md](aesthetic/references/verification.md) |
| Capability | [domain-profiles.md](aesthetic/references/domain-profiles.md), [design-tools.md](aesthetic/references/design-tools.md), [implementation-spec.md](aesthetic/references/implementation-spec.md) |
| Comms | [user-communication.md](aesthetic/references/user-communication.md) |

Vocabulary: [UBIQUITOUS_LANGUAGE.md](aesthetic/UBIQUITOUS_LANGUAGE.md)

#### Goals

Targets for a first public publish — aspirational until backed by hard regression tests. Token and cybersecurity audit badges above stay **pending** until those suites exist.

| Goal | Claim |
| --- | --- |
| Round-trip feedback | User rank in companion → `adopt` → `preferences` reflects it without signal collapse |
| Cohort discipline | Published rounds stay within 3–6 rankable elements |
| Independence | Stars, likes, lifecycle, and missing feedback never merge into one score |
| Golden-rule coverage | Direction spec passes `golden_rules.py --min-coverage 0.8` before build |
| Accessibility | Text ≥ 4.5:1 and controls ≥ 3:1 contrast before publish |
| Honest delivery | `review_delivery.py` rejects generic, explanatory-only, or hash-drifted proposals |
| Subject fidelity | Comp reads as *this* product with logo removed; fails on unrelated-product swap |
| Article fidelity | Hero, graph, TOC, four sections, slideshow, and burndown survive every publish |
| Handoff clarity | First reply delivers URL + key + project-language ask with no setup preamble |

---

## /ora 🇪🇸

| | |
| --- | --- |
| **Package** | [ora/](ora/) |
| **Entry** | [ora/SKILL.md](ora/SKILL.md) |
| **Invoke** | **User-only** (`disable-model-invocation: true`) — say `ora` to start |
| **Locale** | Spanish (Latino) sessions only |

#### Description

Rewrites agent conclusions into simple Latino Spanish: short bullets, light comic tone, a few meaning-carrying emojis. Cuts hedges and process chatter; keeps facts, code, and paths exact. Not part of the design harness — optional voice for Spanish-speaking users.

#### Arguments

| Trigger | Effect |
| --- | --- |
| `ora` (or user invokes skill) | Active for every user-facing reply until stopped |
| `stop ora` · `modo normal` · `normal mode` | Return to default voice |

No CLI scripts. No project-root. No companion.

#### Scripts

None.

#### References

None — single-file skill (`SKILL.md` only).

#### Goals

| Goal | Claim |
| --- | --- |
| Comprehension | Non-expert understands the conclusion on first read |
| Scan time | Whole reply scannable in under ~10 seconds |
| Fidelity | No invented facts for humor; code/paths/errors stay verbatim |
| Locale | Natural Latino American Spanish; no unsolicited English drift |
| Exit | Stops cleanly on `stop ora` / `modo normal` |

```bash
npx skills add yoshi-ortiz/cyber-skills --skill ora -g -a cursor -y
```

---

# License and development

Please consider CC attribution if you build on this work.

| Branch | Contents |
| --- | --- |
| `dev` | Full tree — tests, burndown, ADRs, publication tooling |
| `main` | Fog-free skill payload agents load |

```bash
python3 tools/publish.py --out /tmp/published --check
```

Skill development: [aesthetic/AGENTS.md](aesthetic/AGENTS.md) · traps: [ROADMAP.md](ROADMAP.md)
