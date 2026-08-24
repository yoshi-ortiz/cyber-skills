---
purpose: one release package indexing several independent skills
admits: skill directories that carry their own contract, the README that indexes them and its translations, publication tooling
refuses: doctrine of its own -- every skill's conventions live inside that skill, never here
---

<!-- No `max_file_bytes`. A byte budget is for a file an agent pays for on
     every load, which is why `aesthetic/` carries one. What sits here is
     append-only history -- an incident log and a burndown -- whose growth is
     the point and which no running skill ever loads. A budget here would only
     get ratcheted upward every few months, which is the habit the budgets
     elsewhere exist to prevent. The constraint that matters at this level is
     admission: what belongs, not how big it got. -->


# Cyber skills

Several skills ship together. They share a release, a publication pipeline, and
nothing else. Each carries its own contract, and no skill's doctrine applies to
another.

| Directory | What it is | Context | Channel |
| --- | --- | --- | --- |
| [aesthetic/](aesthetic/) | Design and art direction, ranked against evidence | Design-Inference | alpha |
| [genesis/](genesis/) | Spec-driven build discipline and the files it keeps state in | its own, unrelated | alpha |
| [knowledge/](knowledge/) | External sources distilled into a cited OKF bundle | its own, unrelated | alpha |
| [ora/](ora/) | Spanish conclusion voice | its own, unrelated | main |
| [silly/](silly/) | Installs the second names other skills declare | its own, unrelated | alpha |
| [kit/](kit/) | Operating guide for the harness that installs everything else | its own, unrelated | main |
| [starter-pack/](starter-pack/) | A shipped alias, so `kit`'s original name keeps working | none; it holds no instructions | main |
| [tools/](tools/) | Builds the published trees from `dev` | Repo-Dev | fog |
| [assets/](assets/) | README imagery | neither; nothing reads it at runtime | main |

The [README](README.md) indexes **every** skill in this table, alpha included.
A skill nobody can install yet is still a skill someone reads about before
deciding to. Where a skill is indexed says which channel it is on, so the
placement is checked rather than trusted — see the index gate below.

## Who reads the README

**The final user is a designer who does not code.** Not a beginner developer: a
person who has never opened a terminal on purpose and will judge this package in
about fifteen seconds. They are the audience for the first screen and for
`INSTALL`, and nothing else in the repository is written for them.

That is an argument about *sequence*, never about depth. This package stays
highly technical — flags, contracts, byte budgets, doctrine — because the people
who stay are technical by the time they need any of it. The rule is only that
technical writing never arrives first:

| Where | Written for | Test |
| --- | --- | --- |
| Header, opening lines, `INSTALL` | The designer | No jargon that is not defined in the same sentence. One command to copy. Nothing to decide. |
| Skill cards | Both | What it does for you, then what it needs from you |
| `<details>` blocks | The technical reader | Everything needed to decide, and a link to the skill's own index for the exhaustive list |
| Every heading | Both | Carries an emoji, so the page can be navigated by shape before it is read |
| Everything under a skill directory | Agents and contributors | As dense as it needs to be |

No em dashes, anywhere in a README, and the gate enforces it. A reader who is
not a native speaker parses one clause at a time, and an em dash is a clause
boundary that does not say what kind it is. A colon, a full stop, or a pair of
commas each say so.

Depth goes behind a `<details>` rather than into a second explanation. One
block per skill, holding what a reader needs in order to choose it. An
exhaustive enumeration is not that: a table listing every reference file a
skill owns is a directory listing the skill already publishes, and copying it
here is how the README drifts. Link to the skill's own `references/index.md`
and let it stay authoritative.

The same file has to work for an agent reading the repository cold, which wants
the opposite of a marketing page: stable headings, real links, one table per
fact. The two audiences agree more than they look like they do — both are served
by short declarative rows and no prose that could be a table.

## The index gate

```bash
python3 tools/index_gate.py
```

What it refuses. An em dash in any README. A skill directory with no README
entry. A skill whose section disagrees with `ALPHA_SKILLS`: alpha work
advertised as stable, or a graduated skill still filed under `EXPERIMENTS`. A
translation offered in the language header that is missing, or that has fallen
a skill behind the English. An index table whose rows are not one per skill in
the order `GROUPS` declares. And a second name a skill declares but cannot
answer to.

The README's three H1 sections are fixed: `INSTALL`, `SKILL PROMPTS`,
`EXPERIMENTS`. Translations rename them, so the gate compares by position.
Promotion out of `EXPERIMENTS` is the same edit as publication: remove the
skill from `ALPHA_SKILLS`, move its section, and the gate agrees again.

### Groups

`GROUPS` in `index_gate.py` orders the index by the moment a reader needs a
skill: set something up, plan a project, run a session, or nothing in
particular. Every skill belongs to exactly one group, and the table lists them
in that order in every language. Grouping by channel was the alternative and it
answers a question nobody arrives with.

### What a translation may not translate

```bash
python3 tools/loanwords.py
```

Some nouns name parts of the machinery, and the machinery is in English
everywhere the reader will meet it again: the flag is `--skill`, the file is
`SKILL.md`, the folder is `~/.claude/skills/`, and the assistant's own
settings screen says "skills". A Spanish reader who learns `habilidad` has
learned a synonym for the word they actually need, and can search for none of
it. So `skill` stays `skill`, and `LOANWORDS` in `tools/loanwords.py` is the
list: currently `skill`, `agent`, `prompt`, and `token`.

This is narrower than a style rule and deliberately so. `asistente` for
"assistant" is fine, because no flag, path, or screen ever says "assistant"
back at the reader. The test is not "is this a technical word" but "will the
reader see the English form somewhere else and need to connect the two".

`index_gate.py` runs this check, so the one command still covers everything.

### Second names

A skill may declare its own name in another language, or a playful one, in its
`SKILL.md` frontmatter:

```yaml
translations:
  es: enciclopedia
aliases:
  - nerd-mode
```

The declaration lives on the skill being renamed, never in a central registry,
so gaining a name touches one file. The gate insists each declared name is a
usable command, is unique across the package, appears in that skill's own
`description`, and that a translated README indexes the skill under it. The
last two are the ones that matter: a name absent from every description is a
name the assistant has never heard of, and a Spanish README advertising an
English command is a promise nobody can keep.

[silly/](silly/) installs them, into an assistant's own skills folder and only
when asked. Nothing about a second name reaches a published tree.

## Two contexts, and why the split is load-bearing

**Design-Inference Context** is an agent running a skill to produce creative
decisions. **Repo-Dev Context** is an agent changing a skill's own code,
contracts, or tests.

They use vocabulary that looks alike and means different things. A root cause is
an engineering finding; a Direction is a creative thesis. A budget is a byte
limit; a Burndown is unresolved creative scope. Reading one context's records
while working in the other produces confident, wrong work — an agent that has
just read an incident log starts triaging a design instead of directing it.

So: `BUGS.md`, `ROADMAP.md`, `CHANGELOG.md`, and `.audit/` are **Repo-Dev
Context only**. They are development records, never Preference Evidence and
never Golden Rule Evidence, whatever their rows look like. `.audit/` in
particular is an append-only ledger shaped much like a skill's own scope events
and is not one.

None of them reach a published tree — see `tools/fog.py`, which is the list, and
`tools/CONTEXT.md`, which explains why generating `main` beats curating it.

## Channels

`main` is the stable channel: what an agent gets by default. `alpha` carries the
same tree plus the skills that are not ready to be defaulted into. Both are
generated, both drop fog; they differ only by `ALPHA_SKILLS` in `tools/fog.py`.

A skill starts on `alpha` and graduates by leaving that tuple. Unpublishing one
is the same edit backwards, which is the point of keeping the channel in a list
rather than in a branch someone has to prune.

```bash
python3 tools/publish.py --out /tmp/published --check
python3 tools/publish.py --out /tmp/alpha --channel alpha --check
```

## Adding a skill

Give it a directory, a `SKILL.md`, and a `CONTEXT.md`. Add a row above, a
`## /name` section under `EXPERIMENTS` in the [README](README.md) and in every
translation it offers, its name to `ALPHA_SKILLS` until it has earned `main`,
and its name to a group in `GROUPS`. Nothing else in this repository should
need to know it exists.

```bash
python3 aesthetic/scripts/contracts.py --root .
python3 tools/index_gate.py
```
