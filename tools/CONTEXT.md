---
purpose: build the fog-free trees that main and alpha publish, and run every gate that verifies the repository
admits: publication tooling, the single fog list it shares, the channel split, the index gate, the one runner over every gate, and measurement that judges the package rather than verifying it
refuses: skill logic, doctrine, anything a published tree needs at runtime
max_file_bytes: 12000
---

# Tools

`dev` is where the work happens. Every published tree is generated from it by
`publish.py`, carrying the skills and nothing else.

```bash
python3 tools/check.py
```

`check.py` runs every gate this repository has: the publication and index gates
here, and the contract, unit-test, and self-test gates in `aesthetic/AGENTS.md`.
Those two lists never referenced each other, so running either one in full still
missed half the board. Run a subset by name: `python3 tools/check.py publish`.

`fog.py` holds the list once so `publish.py` and `check_publication.py` cannot
disagree about what fog is. It also holds `ALPHA_SKILLS`: a skill named there is
fog on `main` and shipped on `alpha`, `KEEP_ALWAYS` included. That override is
deliberate — `KEEP_ALWAYS` protects a skill's payload from the fog rules, not
from a decision that the skill is not ready to ship. Generating the tree rather than curating it is the
point: a rule that says "remember not to commit the roadmap to main" is a rule
someone forgets on a tired evening.

`index_gate.py` reads the same `ALPHA_SKILLS` and checks the README against it:
what the tooling publishes and what the README advertises come from one list, so
they cannot drift apart in the one place a reader would notice first.

`trace_preview.py` renders one compiler trace as a page, and that page loads a
real tokenizer from a CDN to count what the estimate only approximates. The
count belongs here rather than in the skill for two reasons. A skill that
shipped a tokenizer would carry a dependency to answer a question no run asks,
and the answer is only ever advice: the page changes no declaration, no budget,
and no admission. On this repository's own `proposal` pass, `Xenova/gpt-4`
charges 8,013 tokens where `bytes/4` estimated 8,818, so the estimate is
conservative by about nine percent.

```bash
python3 tools/trace_preview.py --project-root . --pass proposal --out /tmp/trace.html
```

`--serve` turns that page into a review session on loopback. Each chunk carries
three controls, and no one of them implies another: context utility, semantic
group, and contamination risk. That is the same rule the companion contract puts
on stars, thumbs, and the completed tick, and for the same reason. A chunk can be
expensive and essential, or cheap and a derail, and one score would make those
indistinguishable.

```bash
python3 tools/trace_preview.py --project-root . --pass proposal --serve
python3 tools/trace_preview.py --project-root . --pass proposal --review
```

Every change appends one line to `context-tags-inbox.jsonl`, never batched and
never deduplicated, each line carrying the exact token cost the browser measured.
Two clicks on one signal are two rows; the later one wins on replay and touches
no other signal. `--review` reads them back and says what they imply. It edits
nothing, because a reviewed judgement becomes a declaration when a maintainer
writes it, not when a tool infers it.

The route is not in `server.cjs`. That file ships on alpha and sits at 37 KB of a
40 KB budget, so a dev-only review surface there would publish a maintainer tool
with the skill. The companion contract allows any surface that satisfies it.

`.claude/skills/check-transformers-neural-network/` is the one command that starts it, for an agent
working on this repository. It declares `disable-model-invocation: true`, so it
costs a session nothing until someone types it, and `.claude/` is fog: a
consuming agent installs skills from a published tree and does not inherit the
ones that build it.

Its test builds the page and reaches no network. The tokenizer is fetched by
the browser, when a maintainer asks for it, and never by a gate.

This directory is itself fog. It builds `main`; it does not ship on it.
