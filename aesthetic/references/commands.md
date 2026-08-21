---
type: Playbook
title: Command reference
description: Supported commands for evidence, feedback, editorial scope, and rendering.
status: stable
generated:
  by: codex/gpt-5
  at: 2026-08-20T23:57:30-05:00
---

# Commands

Every verb takes `--project-root` and answers `--help`. Read `--help` before asking the user anything about flags.

## Sentiment and editorial data

The small data module owns corpus inventory, element-level preference analysis,
explicit epic scope, append-only burndown events, and theme candidates. It does
not render a second website.

```bash
python3 scripts/editorial_workflow.py observe --project-root . --source-root /absolute/corpus
python3 scripts/editorial_workflow.py preferences --project-root . \
  --out /tmp/aesthetic-preferences.json
python3 scripts/editorial_workflow.py direction --project-root . \
  --spec /tmp/aesthetic-art-direction.json
python3 scripts/editorial_workflow.py scope --project-root . \
  --spec /tmp/editorial.json
python3 scripts/editorial_workflow.py advance --project-root . \
  --event /tmp/editorial-event.json
python3 scripts/editorial_workflow.py status --project-root .
```

`advance` appends one validated scope event. An existing event id changes
nothing. The established `bootstrap_harness.py article` renders the burndown.

## Opening the page

```bash
python3 scripts/bootstrap_harness.py open --project-root .
```

Prints the URL. Starts the companion if it is down. First command of every continue. Chat replies with that URL; nothing else from this verb belongs there.

## Recording decisions

```bash
# agent proposal -- stored at 0★ until the user ranks; pass the HTML comp, not the PNG
python3 scripts/bootstrap_harness.py decide --project-root . \
  --element cover.ring.kicker --verdict proposed --stars 0 --source agent \
  --preview content/cover.ring.kicker.html \
  --description "anillo con el antetítulo alrededor del objeto" \
  --evidence "user: 'kinda fine'" \
  --implemented "anillo a 96px sobre la retícula"
```

Three text fields, each with one job. All optional, all shown on the scoring row:

| Flag | Holds |
| --- | --- |
| `--description` | what the component **is**, in plain words |
| `--evidence` | why it exists, using **verbatim** user words and never a paraphrase |
| `--implemented` | what was actually **built** this round |

A row with no `--description` shows only its dotted id, which is what made earlier screens unrankable.

To relabel an element the **user** already ranked, use `describe`, never `decide`:

```bash
python3 scripts/bootstrap_harness.py describe --project-root . \
  --element cover.ring.kicker --description "..." --implemented "..."
```

`decide` demands a verdict and a rank. Relabelling a user-ranked row would mean retyping the user's stars, which the 1-star cap exists to prevent. `describe` touches text only.

## Adopting clicks

```bash
python3 scripts/bootstrap_harness.py adopt --project-root . \
  --companion-ledger .superpowers/brainstorm/decisions.jsonl
```

`0 adopted` means **no feedback was captured**. Say so plainly rather than moving on.

## Putting scoring inside the prototype

Place a placeholder naming the elements a section scores:

```html
<div data-dh-controls="cover.layout.two-column,cover.spine.right"></div>
```

Fill it and serve it with three commands. Never do this by hand.

```bash
python3 scripts/bootstrap_harness.py article --project-root . \
  --out <screen>.html --cohort "..." --round-label "Micrófono" \
  --agent "Composer" --agent-url "<deep link to this session>"
python3 scripts/bootstrap_harness.py embed --project-root . --screen <screen>.html \
  --bg "#ffebb8" --ink "#111" --accent "#d9482a" --pin cover.spine.right
python3 scripts/bootstrap_harness.py publish --project-root . --screen <screen>.html
```

`embed` is **idempotent** and safe to rerun. If output changes on a second run, that is a bug. It refuses a screen with no placeholder and refuses ids not in standing. `--pin` puts this turn's work in a group on top. `publish` stamps the screen a clear margin ahead of every other because the companion serves **only the newest-mtime file**. Write the scoring screen last, or rerun `publish`.

## Statistics

See [stats.md](stats.md) for field semantics, cohort selection, and the command.

## Init and validate

```bash
python3 scripts/bootstrap_harness.py init --project-root . \
  --source-root /absolute/inspiration --profiles art-direction,composition

python3 scripts/bootstrap_harness.py validate --project-root .
python3 scripts/bootstrap_harness.py self-test          # after changing this skill
```

Profiles are listed in [domain-profiles.md](domain-profiles.md); adapters and design MCP servers in [design-tools.md](design-tools.md). Record what you actually observed with `preflight`, and never narrate a tool you did not run.

The user names the corpus path. Never assume its directory name. It is read-only. `validate` reports ledger health and corpus drift **separately**. Drift is usually the user reorganising files and does not block design work. A regenerated preview is a note, not a failure.
