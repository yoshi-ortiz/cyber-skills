# Companion contract

## Health-check first, always

```bash
python3 scripts/bootstrap_harness.py doctor --project-root .
```

Never claim the companion works on the strength of an earlier check. Each link fails silently:

| Link | Fails as |
| --- | --- |
| Server process | dead; URL looks fine, nothing responds |
| Served screen | `/` serves **only the newest-mtime file** — write any screen after the scoring one and you have silently redirected the user |
| Scoring rows | screen has no `data-element` |
| Star + verdict controls | no `data-rank` / `data-verdict` |
| Stale injected helper | served page looks right, clicks dropped — restart after editing `helper.js` |
| Component graphic | rows show ids, not the thing being judged |
| Invisible graphic | markup present, renders at 0px or as a corner fragment — host CSS beat the stylesheet |
| Socket round trip | clicks land nowhere — a `file://` tab does this, silently |

## Routing: newest mtime wins

`/` serves **only the newest-mtime file** in the session's `content/`. Writing any screen after the scoring screen silently sends the user somewhere else. Write the scoring screen last, or `touch` it afterwards.

## A file:// tab is not the companion

`helper.js` is injected only into served pages. Clicks on a `file://` copy go nowhere and look identical. Generated controls carry a red offline banner that only hides once the helper connects — never remove it.


The harness does not ship a companion and does not require a particular one. It requires any browser surface that shows screens and returns feedback to satisfy the contract below. If the available companion cannot satisfy it, say so and fall back to `decide` in the terminal — never approximate it by remembering what the user clicked.

## What the companion must provide

1. **A durable ledger, outside any session directory.** Append-only JSONL. A companion that restarts must append to the same file. Anything scoped to one server run is orphaned on restart and is not a record.
2. **Design-element ids on every interactive control**, taken from the harness ledger — never invented per screen.
3. **Four independent signals** per element, none of which implies another: a 0–5 star rank (`data-rank` for 1–5, `data-reset` for the zero), an encouragement thumb (`data-sentiment`), and a `completed` status toggle (`data-verdict`).
4. **One line appended per interaction**, with no batching, debouncing, or deduplication. The harness is responsible for replay order, not the companion.

## Event schema

One JSON object per line. Unknown fields are ignored; the fields below are the contract.

| Field | Required | Meaning |
| --- | --- | --- |
| `element` | yes | Stable dotted design-element id, e.g. `cover.layout.two-column` |
| `stars` | one of | Integer 0–5: **graphic execution quality only**. `0` is a real score and it is the worst one — "this is bad" |
| `verdict` | one of | `completed`, `approved` or `rejected`, set by an explicit control. **Only a verdict moves state** |
| `sentiment` | one of | `like` or `dislike` — encouragement for the *idea*. Never moves state |
| `reset` | one of | `true` (or `type: "reset"`) is the **zero-star control**: it scores the element 0, it does not erase the score |
| `text` | no | Verbatim user words, used as the evidence excerpt |
| `timestamp` | no | Epoch millis; fixes replay order. Absent sorts as `0` |
| `type` | no | Free label for logging (`rank`, `sentiment`, `click`) |

At least one of `stars`, `verdict` or `sentiment` must be present. An interaction with neither, or with no `element`, **cannot bind** — the harness skips it and reports the count. Fix that by giving the control an id, never by guessing one.

```json
{"element":"cover.layout.two-column","stars":5,"text":"user: 'c2'","timestamp":1786745271000}
{"element":"cover.ring.kicker","sentiment":"like","timestamp":1786745272000}
{"element":"cover.background.black","sentiment":"dislike","timestamp":1786745273000}
```

## Deterministic semantics

**A score never changes state.** Stars rate how well a thing is *drawn*; they say nothing about whether it should exist. Only an explicit verdict control moves an element between groups. This is the single most important rule in this file: an earlier version mapped `stars: 0 → rejected`, and an element the user rated 0 was auto-rejected and its work deleted from the design.

| Signal | Effect on state | Effect on rank |
| --- | --- | --- |
| `stars: n` (0–5) | **none** — stays where it is; a new element arrives `proposed` | `n` |
| `reset` (the zero control) | **none** | `0` — judged, and judged bad |
| `sentiment: like` / `dislike` | **none** — recorded as encouragement only | unchanged |
| `verdict: completed` | → `completed` (a toggleable status, *not* a lock) | `stars` when present, else unchanged |
| `verdict: approved` / `rejected` | as given | `stars` when present, else unchanged |

`0` and "unrated" are different things and the number does not distinguish them — `scored` does. An element nobody has touched is `scored: false`; an element scored zero is `scored: true, stars: 0` and counts toward coverage. It has been judged.

A `rejected` or `superseded` element that receives a fresh score returns to `proposed` rather than staying buried — a rank is a sign of renewed interest.

The defaults are fixed constants, not judgement. Replay is ordered by `(timestamp, file position)`, so adopting a ledger twice produces a byte-identical result — `adopt` is idempotent and safe to re-run.

Sentiment never supersedes another element, and never rejects one. Replacing one element with another is a `decide --supersedes`, which is a deliberate act.

### Groups

Rows render grouped by lifecycle, and **nothing is ever hidden**:

| Group | Label | States |
| --- | --- | --- |
| `brainstorming` | Lluvia de ideas | `proposed` |
| `developing` | En desarrollo | `completed`, `approved` |
| `rejected` | Descartado | `rejected`, `superseded` |

Rejected work stays on screen, dimmed, carrying live controls. A rejection is undone by clicking, never by editing JSON.

### `polish`

An element with a `like` and a low star rank is **`polish`**, not a conflict: the idea is good and the execution is not there yet. The correct response is to redraw it. Never drop it.

## Generating the controls

Never hand-author element ids into a screen. Emit them from the ledger:

```bash
python3 scripts/bootstrap_harness.py controls --project-root . --out /tmp/controls.html
```

The markup carries `data-element`, `data-stars`, `data-rank`, `data-sentiment`, `data-verdict`, `data-reset` and `data-group`, renders every element including rejected ones, and is byte-stable for a given ledger. Prefer `embed`, which fills `data-dh-controls` placeholders in place and is idempotent — re-running it is a byte-identical no-op.

The generator owns the strip's design. Do not restyle it in a project: local CSS outranks the generator's and is how the controls went invisible before.

## Wiring a companion that lacks handlers

If the companion has no rank/sentiment handling, add a listener that appends one line per click to the durable ledger:

```js
document.addEventListener('click', (e) => {
  const holder = e.target.closest('[data-element]');
  if (!holder) return;
  const star = e.target.closest('[data-rank]');
  const mood = e.target.closest('[data-sentiment]');
  const mark = e.target.closest('[data-verdict]');
  const zero = e.target.closest('[data-reset]'); // legacy attribute; this scores 0
  if (!star && !mood && !mark && !zero) return;
  send({
    element: holder.dataset.element,
    stars: star ? Number(star.dataset.rank) : undefined,
    sentiment: mood ? mood.dataset.sentiment : undefined,
    verdict: mark ? mark.dataset.verdict : undefined,
    reset: zero ? true : undefined,
    text: holder.dataset.label || null,
    timestamp: Date.now(),
  });
});
```

`send` is whatever the companion uses to reach its durable ledger. The only hard requirement is that the line lands outside the session directory.

## Adopting

```bash
python3 scripts/bootstrap_harness.py adopt --project-root . \
  --companion-ledger <path>/decisions.jsonl
```

Run it in the same turn the feedback arrives. Feedback that is not adopted is lost at the next session boundary.

## Provenance

Everything `adopt` ingests is recorded `source: user`. Anything the agent types with `decide` is `source: agent` and capped at 1 star. That distinction is the point: before it existed, a user's click and an agent's guess were indistinguishable in the ledger.
