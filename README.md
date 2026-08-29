<div align="center">

![Cyber Skills · Intelligent + Easy Prompts](assets/cover.png)

**Tested prompts created by a silly deterministic nerd**

[![release](https://img.shields.io/badge/release-0.9--beta-8b5cf6?style=flat-square&labelColor=1e1b4b)](https://github.com/yoshi-ortiz/cyber-skills/releases)
[![repo](https://img.shields.io/badge/repo-yoshi--ortiz%2Fcyber--skills-0ea5e9?style=flat-square&labelColor=1e1b4b)](https://github.com/yoshi-ortiz/cyber-skills)
[![prompts](https://img.shields.io/badge/prompts-2%20stable%20%C2%B7%204%20experiments-6366f1?style=flat-square&labelColor=1e1b4b)](#-collection)
[![python](https://img.shields.io/badge/python-stdlib%20only-16213e?style=flat-square&labelColor=1e1b4b)](#-experiments)
[![cybersecurity tested](https://img.shields.io/badge/cybersecurity%20tested-pending-f59e0b?style=flat-square&labelColor=44403c)](#-experiments)
[![publish](https://img.shields.io/badge/publish-main%20%C2%B7%20alpha%20%E2%86%90%20dev-312e81?style=flat-square&labelColor=1e1b4b)](tools/CONTEXT.md)

🇬🇧 **English** | 🇪🇸 [Spanish](README.es.md) | 🇯🇵 日本語 (coming soon)

</div>

---

## 🤔 Should you install this?

Ask the thing you would be installing it into. Paste this into Claude Code,
Cursor, or whichever AI app you use. It reads the repo, tells you what each
prompt actually does, and walks you through installing the ones you want.

```
What's this plugin for? Should I install it?
https://github.com/yoshi-ortiz/cyber-skills
```

A **skill prompt** is a set of written instructions your AI agent reads before
it answers you. Same agent, different specialist: one that already knows how
you like to work and does not need to be re-briefed every morning.

You do not write code to use one. You install a folder, start a new chat, and say
its name. Everything after the install is optional reading.

- [Index and main workflow](#-collection)
- [Skill-surface index](SKILL_SPEC.md)
- [Installation](#-install)
- [Skills](#-skill-prompts)
- [Coming soon](#-experiments)

## 📒 COLLECTION

Grouped by when you need one, not by how finished it is. The collection is
organized around one rail: `kit` is Day 0, `first`, `build`, and `land` move
work forward, and `check` and `fix` are return arcs. The **Family** column says
which stop of that rail a prompt belongs to.

<table>
  <colgroup>
    <col width="220">
    <col>
    <col width="230">
  </colgroup>
  <tr><td colspan="3" align="center"><h3><a href="#-kit">📀 Setup once</a><br><small>Install it once, every AI app carries it</small></h3></td></tr>
  <tr><td nowrap>📦 <a href="#-kit"><strong>/kit</strong></a></td><td>One toolkit across every AI app you use</td><td><code>kit</code> · <strong>Day 0</strong>, outside the loop</td></tr>
  <tr><td nowrap>📦 <a href="#-kit"><strong>/starter-pack</strong></a></td><td>Same skill, its original name</td><td><code>kit</code> · <strong>Day 0</strong>, outside the loop</td></tr>
  <tr><td colspan="3" align="center"><h3><a href="#-genesis">💼 Planning</a><br><small>Before you start building</small></h3></td></tr>
  <tr><td nowrap>📁 <a href="#-genesis"><strong>/genesis</strong></a></td><td>Plans before it builds, and proves the thing runs</td><td><code>first</code> · <strong>Plan</strong></td></tr>
  <tr><td nowrap>📚 <a href="#-knowledge"><strong>/knowledge</strong></a></td><td>Reads the real docs and keeps a short cited note</td><td><code>first</code> · <strong>Plan</strong></td></tr>
  <tr><td colspan="3" align="center"><h3><a href="#-aesthetic">🤖 Token sessions</a><br><small>Where you spend a working session</small></h3></td></tr>
  <tr><td nowrap>🧑‍🎨 <a href="#-aesthetic"><strong>/aesthetic</strong></a></td><td>Draws design options, you rank them, it learns what you like</td><td><code>first</code> · <strong>Plan</strong></td></tr>
  <tr><td nowrap>🔬 <a href="#-build-context-token-vectors"><strong>/build-context-token-vectors</strong></a></td><td>Shows which other skills yours actually resemble, and which resemble nothing</td><td><code>build</code> · <strong>Measure</strong></td></tr>
  <tr><td colspan="3" align="center"><h3><a href="#-silly">🤡 Silly</a><br><small>Call by fun names</small></h3></td></tr>
  <tr><td nowrap>😆 <a href="#-silly"><strong>/silly</strong></a></td><td>Lets a skill answer to a second name, in your language or just a nicer one</td><td>No family. Works anywhere on the rail.</td></tr>
  <tr><td nowrap>🇪🇸 <a href="#-silly"><strong>/silly</strong></a> español</td><td>Add commands in Spanish</td><td>No family. Works anywhere on the rail.</td></tr>
  <tr><td nowrap>🇪🇸 <a href="#-ora"><strong>/ora</strong></a></td><td>Rewrites your agent's conclusions in plain Spanish</td><td>No family. Works anywhere on the rail.</td></tr>
  <tr><td colspan="3" align="center"><h3>🛤️ Rest of the rail<br><small>Planned families. No installed command answers to these yet.</small></h3></td></tr>
  <tr><td nowrap>🔨 <code>build-*</code></td><td>Implement and verify the approved contract</td><td><code>build</code> · <strong>Code · Build · Test</strong></td></tr>
  <tr><td nowrap>🚢 <code>land-*</code></td><td>Ship selected outputs and make deployment observable</td><td><code>land</code> · <strong>Release · Deploy</strong></td></tr>
  <tr><td nowrap>🔍 <code>check-*</code></td><td>Read progress and production evidence back into planning</td><td><code>check</code> · <strong>Monitor</strong> → Plan</td></tr>
  <tr><td nowrap>🩹 <code>fix</code></td><td>Restore safe operation, then return to the affected family</td><td><code>fix</code> · <strong>Operate</strong>, incident response</td></tr>
</table>

Stable prompts sit under [SKILL PROMPTS](#-skill-prompts). The rest are
[EXPERIMENTS](#-experiments), installed by hand.

The [skill-surface index](SKILL_SPEC.md) maps every family, alias, owner,
status, and roadmap item. The design-specific epics and their PASS evidence live
in the development [roadmap](ROADMAP.md). Planned names are not installed
commands.

---

# 📦 INSTALL

One command. It finds every AI app you have and installs into each one. No
clone, no folders, nothing to configure.

**Everything, experiments included:**

```bash
npx skills add https://github.com/yoshi-ortiz/cyber-skills/tree/dev -g --all
```

**Only the stable ones:**

```bash
npx skills add yoshi-ortiz/cyber-skills -g --all
```

Then **start a new chat**. AI apps read their skills when a conversation
begins, never in the middle of one. That is the whole install.

<details>
<summary><b>Installing less than everything</b></summary>

`--all` is shorthand for `--skill '*' --agent '*' -y`, meaning every skill into
every app with no prompts. It does **not** imply `-g`, so without it the skills
install into whatever folder your terminal happens to be sitting in and no app
finds them. Keep the `-g`. Each flag below narrows one part of that.

| Flag | What it does |
| --- | --- |
| `-s`, `--skill <name>` | One skill, by its folder name. Repeatable. |
| `-a`, `--agent <id>` | One AI app: `claude-code`, `cursor`, `codex`, `opencode`, `zed`, `pi`, or `antigravity`. Repeatable. |
| `-g`, `--global` | Install for your user, not one project |
| `-l`, `--list` | Print what is here, install nothing |
| `-y`, `--yes` | Skip the confirmation prompt on its own |

A plain `yoshi-ortiz/cyber-skills` reads the `main` branch, which carries the
stable prompts only. The `/tree/dev` URL reads the development branch, which
carries those plus everything under EXPERIMENTS.

Skills land in `~/.agents/skills/`. Claude Code and Pi are linked from there
by the CLI itself. **Cursor, Codex, and Antigravity are not**, so if you use
one of those and the skills do not show up, that is why. `/kit` fetches
`harness-core` and runs its local sync script after installation.

To remove one later: `npx skills remove <name>`.

</details>

---

# ✨ SKILL PROMPTS

Stable. Installed by path B, supported, safe to rely on.

## 🔬 /build-context-token-vectors

Answers one question: **which other skills is yours actually like?** It reads
every skill installed on your machine, groups them by what they say, and shows
you where yours land. Some land next to obvious neighbours. Some land nowhere,
which is worth knowing before you decide yours is unique.

| | |
| --- | --- |
| **Package** | [build-context-token-vectors/](build-context-token-vectors/) · entry [build-context-token-vectors/SKILL.md](build-context-token-vectors/SKILL.md) |
| **Invoke** | You only. Say `build-context-token-vectors`. |
| **Needs** | Python, and three packages in a throwaway environment you create: `evoc`, `model2vec`, `matplotlib` |
| **Runs on** | Your installed skills folder, read only |
| **Channel** | `main` |

<details>
<summary><b>Full spec: what it measures, and the one thing it refuses to say</b></summary>

`tools/token_bench.py` compares a skill flow against a reference flow, and a
human picks the reference. This derives it instead: every `SKILL.md` becomes a
vector, the vectors are clustered, and the nearest neighbours are the skills a
benchmark should actually run against.

| Output | Means |
| --- | --- |
| Cosine similarity | How close two skills' doctrine sits. Above 0.80 a real peer, 0.65 to 0.80 a loose one, below 0.65 no peer at all. |
| A cluster | The skill was placed, and that cluster's other members are its neighbourhood. |
| `noise` | It was placed nowhere. |
| The scatter plot | Two principal components, for orientation. Clustering ran in full dimensionality, so two adjacent looking points may not be. |

**It never says whether a skill is good.** `noise` means the corpus holds no
peer, and novelty and dilution look identical from here. The judgement stays
yours.

**The seed is part of the result.** The clustering algorithm is stochastic, so
the script declares a fixed `random_state`. Without one, two runs over the same
skills return different groups, and a comparison set that moves is not one.

**Dependencies stay outside.** Nothing in this package imports them except this
skill's own script, and it ships none of them.

</details>

## 📦 /kit

One toolkit, every AI app. If you use more than one, this keeps them
equipped the same way, from one list instead of app by app.

| | |
| --- | --- |
| **Package** | [kit/](kit/) · entry [kit/SKILL.md](kit/SKILL.md) |
| **Invoke** | You only. Say `kit` to set it up, `kit sync` to update it, `kit fix` when something broke. |
| **Also answers to** | `starter-pack`, its original name. Ships as an alias, nothing to install. |
| **Needs** | Git plus the [harness](https://github.com/yoshi-ortiz/harness-core) checkout it fetches |
| **Channel** | `main` |

<details>
<summary><b>Full spec</b></summary>

A reference skill: no scripts, no state. It teaches an agent to operate
`yoshi-ortiz/harness-core`, whose `collection.yaml` lists the skills every AI
app on your machine should carry.

| Argument | What it does |
| --- | --- |
| `kit`, `install`, `setup`, `init`, `start` | Sets the harness up and arms every AI app. Bare `kit` means this. |
| `sync`, `update`, `refresh`, `upgrade` | Re-arms every AI app with the current list. This is the update. |
| `fix`, `doctor`, `repair`, `troubleshoot`, `conflict` | Works out why something installed wrong, or why two things collided. |

Installing a machine that is already set up syncs it, so it never has to ask
you which one you meant.

| Covers | What it holds |
| --- | --- |
| Fetch | Clone or fast-forward `harness-core` from GitHub, then run its local sync script |
| Where the list lives | The `harness-core` checkout and the local overlay that wins on conflict |
| Adding a skill | Why a hand edit installs nothing, why a full name list rots, why `--all` is banned |
| Standard versus situational | What every AI app gets, against opt-in groups behind `--with` |
| Fixing | A symptom table: failed source, stale copy after a rename, two skills of one name |
| Releasing | Read the [harness README](https://github.com/yoshi-ortiz/harness-core) for the release procedure |

</details>

## 🇪🇸 /ora

Rewrites your agent's conclusions into plain Latin American Spanish: short
bullets, light humour, no hedging. Facts, code, and file paths stay exactly as
written.

| | |
| --- | --- |
| **Package** | [ora/](ora/) · entry [ora/SKILL.md](ora/SKILL.md) |
| **Invoke** | You only. Say `ora` to start, `modo normal` to stop. |
| **Needs** | Nothing. One file, no scripts. |
| **Channel** | `main` |

<details>
<summary><b>Full spec</b></summary>

| Trigger | Effect |
| --- | --- |
| `ora` | Rewrites the next reply |
| `ora on` | Holds for the session |
| `ora full` | Translates the whole reply, not just the conclusions |
| `ora off` · `modo normal` · `stop ora` | Back to the default voice |

| Goal | Claim |
| --- | --- |
| Comprehension | A non-expert understands the conclusion on first read |
| Scan time | Whole reply scannable in about 10 seconds |
| Fidelity | No invented facts for humour. Code, paths, and errors stay verbatim. |
| Locale | Natural Latin American Spanish, no unsolicited English drift |
| Exit | Stops cleanly on `off` |

</details>

---

# 🧪 EXPERIMENTS

Not on the stable branch. Real work, real tests, unfinished edges. Install by
hand from `dev` (path A). Links in this section resolve on `dev`.

## 📁 /genesis

Builds like an engineer who writes things down. It asks what you actually want
before it touches code, keeps a live list of what is done and what is stuck, and
**will not call anything finished until it has watched it run**.

| | |
| --- | --- |
| **Package** | [genesis/](genesis/) · entry [genesis/SKILL.md](genesis/SKILL.md) |
| **Invoke** | You only. Say `genesis`. |
| **Needs** | Nothing. It writes plain Markdown into your project. |
| **Runs on** | **Your** project folder, never this repo |
| **Channel** | `alpha` |

<details>
<summary><b>Full spec: seven steps, the files they write, and the promotion gate</b></summary>

Run at the start of a project, at the start of a feature, or backwards as an
audit of work already underway.

| Step | What it refuses |
| --- | --- |
| Interview before you architect | A boundary drawn from a one-line request |
| Promote the requirement to a spec | A contract that changes while you build against it |
| Fetch what you do not know | Implementing a fast-moving dependency from memory |
| Source before you write | Hand-drawn SVG, hand-rolled boilerplate, blind layout |
| Build inside the boundary | Hacking through a module wall to force a quick fix |
| Prove it, then say it | A passing linter reported as a working feature |
| Update the state, immediately | A roadmap that was only true the day it was written |

**Files, in your project.** `ROADMAP.md` the burndown, `BUGS.md` incidents each
closed with a root cause, `CHANGELOG.md` semver, `docs/REQUIREMENTS.md` raw and
append-only, `docs/SPEC/` the promoted contracts, `docs/GLOSSARY.md` one
immutable term per concept, `docs/knowledge/` owned by [/knowledge](#-knowledge).

**Doctrine**, loaded only when a step names it:
[references/index.md](genesis/references/index.md) covers the scope interview
and modular architecture, the sourcing contract, and what counts as evidence.

**Promotion gate.** The doctrine is written and untested.

| Goal | Claim |
| --- | --- |
| Interview discipline | It asks before it architects, on a request short enough to guess at |
| Topology | A cold project ends the first run with every file above populated |
| State fidelity | An item reaches `DONE` only with runtime evidence quoted in the same turn |
| Root cause | No `BUGS.md` entry closes on a null check where the pipeline was the cause |
| Sourcing | It reaches for a component library before writing a component, and says why when it does not |
| Audit mode | Pointed at an existing project, it reports drift and changes nothing |

</details>

## 📚 /knowledge

Reads the manual so it stops guessing. When your agent needs to know how
some tool or product works, it looks it up, saves a short **cited** note in your
project, and reads that note next time instead of inventing an answer.

| | |
| --- | --- |
| **Package** | [knowledge/](knowledge/) · entry [knowledge/SKILL.md](knowledge/SKILL.md) |
| **Invoke** | Your agent starts it when research needs keeping. You can also name it. |
| **Also answers to** | `enciclopedia`, once [/silly](#-silly) installs it |
| **Needs** | Python 3 (stdlib only) |
| **Runs on** | **Your** project folder, never this repo |
| **Channel** | `alpha` |

<details>
<summary><b>Full spec: format, script, and the promotion gate</b></summary>

Notes use **Open Knowledge Format 0.2**: one concept per file, YAML
frontmatter, `index.md` at the door. The spec is cached in
[references/okf-0.2.md](knowledge/references/okf-0.2.md) so the skill never
refetches it. Output lands in `docs/knowledge/` in **your** project.

```bash
python3 knowledge/scripts/okf.py new <url> --root docs/knowledge --by claude/opus-5
python3 knowledge/scripts/okf.py check --root docs/knowledge
```

`new` fetches, writes the stub with `resource`, `generated`, and `sources`
filled in, and prints the extract. `check` refuses a file with no frontmatter,
a file with no `type`, a concept missing from `index.md`, and an index link
that resolves to nothing.

The script stops short of summarising on purpose. A script that condensed a
page would be writing the one part of a note that has to be produced by
something that understood the source. Rules for the human half:
[distilling.md](knowledge/references/distilling.md).

**Promotion gate.**

| Goal | Claim |
| --- | --- |
| Conformance | Every note it writes passes `okf.py check` without a hand edit |
| Traceability | No sentence in a note lacks support in the `sources` it declares |
| Compression | A note is shorter than a careful reading of its source, and still answers the question |
| Version fidelity | The version a claim held for is named, and checked against the dependency manifest |
| Scope | Notes describe sources. Project decisions stay out of them. |

</details>

## 🧑‍🎨 /aesthetic

![Aesthetic ranking companion](assets/aesthetic-companion.svg)

Design that reads as **intentional, not templated**. Your agent draws 3 to 6
versions of a screen and publishes them to a page in your browser. **You rank
them and leave notes, in your own words.** It reads that back and draws the next
round against it. Nothing is scored by vibes.

| | |
| --- | --- |
| **Package** | [aesthetic/](aesthetic/) · entry [aesthetic/SKILL.md](aesthetic/SKILL.md) |
| **Invoke** | Your agent starts it when the work is visual. You can also name it. |
| **Needs** | Python 3 (stdlib only) · Node for the local ranking page |
| **Runs on** | **Your** project folder, never this repo |
| **Channel** | `alpha` |

First reply you should get: a URL, a session key, and one question. If it opens
with setup chatter instead, that is a bug.

<details>
<summary><b>Full spec: modes, scripts, doctrine, and the promotion gate</b></summary>

**Modes**, said in chat, not typed as flags.

| Mode | When |
| --- | --- |
| `continue` | Resume from the ledger. One new round of 3 to 6 elements. |
| `critique` | Report mismatches without changing ranks or scope |
| `prototype` | Draw and publish comps for ranking |
| `observe` | Ingest a reference folder as corpus evidence |

```bash
python3 aesthetic/scripts/bootstrap_harness.py init --project-root <project>
python3 aesthetic/scripts/bootstrap_harness.py open --project-root <project>
```

`bootstrap_harness.py` runs the companion, ledger, article, and publish.
`editorial_workflow.py` runs corpus, preferences, direction, and burndown. Six
more scripts cover rules, delivery, briefs, and diagnostics. Every one answers
`--help`, and the full flag reference is
[references/commands.md](aesthetic/references/commands.md).

**Doctrine.** Self-contained, OKF 0.2, indexed at
[references/index.md](aesthetic/references/index.md): golden rules and design
fundamentals, inference and critique, production contracts, and the capability
model. Vocabulary:
[UBIQUITOUS_LANGUAGE.md](aesthetic/UBIQUITOUS_LANGUAGE.md). Companion server,
vendored Node: [companion/](aesthetic/companion/).

**Promotion gate.** The badges above read **pending** until these hold under
regression tests.

| Goal | Claim |
| --- | --- |
| Round-trip feedback | Your rank, then `adopt`, then `preferences` reflects it without signal collapse |
| Cohort discipline | Published rounds stay within 3 to 6 rankable elements |
| Independence | Stars, likes, lifecycle, and missing feedback never merge into one score |
| Accessibility | Text at 4.5:1 and controls at 3:1 contrast before publish |
| Honest delivery | `review_delivery.py` rejects generic, explanatory-only, or hash-drifted proposals |
| Subject fidelity | A comp reads as *this* product with the logo removed |
| Handoff clarity | First reply is URL, key, and a question. No setup preamble. |

</details>

## 😆 /silly

Lets a skill answer to a second name: `knowledge` in Spanish is
`/enciclopedia`. **Only the name is translated**, never the skill, so there is
no second copy to drift. Nothing is installed until you ask for a language.

| | |
| --- | --- |
| **Package** | [silly/](silly/) · entry [silly/SKILL.md](silly/SKILL.md) |
| **Invoke** | You only. Say `silly`, or `comandos en espanol`. |
| **Needs** | Python 3 (stdlib only) |
| **Runs on** | Your installed skills folder, never this repo |
| **Channel** | `alpha` |

<details>
<summary><b>Full spec: the manifest, the tool, and the promotion gate</b></summary>

A skill answers to the name in its own `SKILL.md` and to nothing else, so a
second name means a second file declaring it. A directory symlink cannot do
this: the `SKILL.md` inside still names the original, and the new command never
appears. The alias is therefore a one-file stub pointing at the real skill.

Declared on the skill being renamed, never in a central registry:

```yaml
translations:
  es: enciclopedia
aliases:
  - nerd-mode
```

Both blocks are optional. A declared name must be lower case, unique across the
package, and **present in that skill's own description**, or the agent has
never heard the word and the alias file changes nothing. The index gate refuses
all three failures.

```bash
python3 silly/scripts/alias.py list   --root ~/.cursor/skills
python3 silly/scripts/alias.py link   --root ~/.cursor/skills --lang es
python3 silly/scripts/alias.py unlink --root ~/.cursor/skills
```

`link --fun` installs the playful names instead. `--dry-run` prints without
touching anything. It refuses to write over a directory it did not create, and
`unlink` removes only its own stubs.

**Declared today:** `knowledge` answers to `enciclopedia` in Spanish.

**Promotion gate.**

| Goal | Claim |
| --- | --- |
| Trigger | An installed alias fires the real skill from a cold chat, by name alone |
| Safety | No run ever overwrites or removes a skill it did not write |
| Opt-in | Nothing lands in a skills folder that was not asked for by language or by `--fun` |
| Reversibility | `unlink` leaves the folder exactly as it was found |
| Locality | The manifest stays on the skill being renamed. This never becomes a registry. |

</details>

---

<div align="center">

Please consider CC attribution if you build on this work.

Contributors: [CONTEXT.md](CONTEXT.md) · [ROADMAP.md](ROADMAP.md) · [aesthetic/AGENTS.md](aesthetic/AGENTS.md)

</div>
