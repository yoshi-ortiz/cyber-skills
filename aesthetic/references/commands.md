# Commands

Every verb takes `--project-root` and answers `--help`. Read `--help` before asking the user anything about flags.

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
| `--evidence` | why it exists — **verbatim** user words, never a paraphrase |
| `--implemented` | what was actually **built** this round |

A row with no `--description` shows only its dotted id, which is what made earlier screens unrankable.

To relabel an element the **user** already ranked, use `describe`, never `decide`:

```bash
python3 scripts/bootstrap_harness.py describe --project-root . \
  --element cover.ring.kicker --description "..." --implemented "..."
```

`decide` demands a verdict and a rank, so relabelling a user-ranked row means retyping the user's stars — exactly the invention the 1-star cap exists to prevent. `describe` touches text only.

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

Fill it and serve it — three commands, never by hand:

```bash
python3 scripts/bootstrap_harness.py article --project-root . \
  --out <screen>.html --cohort "..." --round-label "Micrófono" \
  --agent "Composer" --agent-url "<deep link to this session>"
python3 scripts/bootstrap_harness.py embed --project-root . --screen <screen>.html \
  --bg "#ffebb8" --ink "#111" --accent "#d9482a" --pin cover.spine.right
python3 scripts/bootstrap_harness.py publish --project-root . --screen <screen>.html
```

`embed` is **idempotent** — safe to re-run; if output changes on a second run, that is a bug. It refuses a screen with no placeholder and refuses ids not in standing. `--pin` puts this turn's work in a group on top. `publish` stamps the screen a clear margin ahead of every other, because the companion serves **only the newest-mtime file** — so write the scoring screen last, or re-run `publish`.

## Statistics

```bash
python3 scripts/bootstrap_harness.py stats --project-root .
```

Deterministic — same ledger, same numbers. Lead with **coverage**: the fraction of standing elements carrying a signal the user actually set. A high star average means nothing at 20% coverage, because the rest is agent inference. `polish` is liked-but-scored-low: redraw it, never drop it. `unscored` names exactly what still needs clicks.

## Init and validate

```bash
python3 scripts/bootstrap_harness.py init --project-root . \
  --source-root /absolute/inspiration --profiles art-direction,composition

python3 scripts/bootstrap_harness.py validate --project-root .
python3 scripts/bootstrap_harness.py self-test          # after changing this skill
```

Profiles are listed in [domain-profiles.md](domain-profiles.md); adapters and design MCP servers in [design-tools.md](design-tools.md). Record what you actually observed with `preflight`, and never narrate a tool you did not run.

The user names the corpus path; never assume its directory name. It is read-only. `validate` reports ledger health and corpus drift **separately** — drift is usually the user reorganising files and does not block design work. A regenerated preview is a note, not a failure.
