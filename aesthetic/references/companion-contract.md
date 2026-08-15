# Companion contract

## Health-check first, always

```bash
python3 scripts/bootstrap_harness.py doctor --project-root .
```

Six links, each fails silently. Never claim the companion works on the strength of an earlier check.

## Routing: newest mtime wins

`/` serves **only the newest-mtime file** in the session's `content/`. Writing any screen after the scoring screen silently sends the user somewhere else. Write the scoring screen last, or `touch` it afterwards.

## A file:// tab is not the companion

`helper.js` is injected only into served pages. Clicks on a `file://` copy go nowhere and look identical. Generated controls carry a red offline banner that only hides once the helper connects — never remove it.


The harness does not ship a companion and does not require a particular one. It requires any browser surface that shows screens and returns feedback to satisfy the contract below. If the available companion cannot satisfy it, say so and fall back to `decide` in the terminal — never approximate it by remembering what the user clicked.

## What the companion must provide

1. **A durable ledger, outside any session directory.** Append-only JSONL. A companion that restarts must append to the same file. Anything scoped to one server run is orphaned on restart and is not a record.
2. **Design-element ids on every interactive control**, taken from the harness ledger — never invented per screen.
3. **Two independent signals** per element: a 1–5 star rank and a like/dislike sentiment.
4. **One line appended per interaction**, with no batching, debouncing, or deduplication. The harness is responsible for replay order, not the companion.

## Event schema

One JSON object per line. Unknown fields are ignored; the fields below are the contract.

| Field | Required | Meaning |
| --- | --- | --- |
| `element` | yes | Stable dotted design-element id, e.g. `cover.layout.two-column` |
| `stars` | one of | Integer 0–5. **0 means kill it** — a real score, not a missing value |
| `verdict` | one of | `approved` or `rejected`, set by an explicit control |
| `sentiment` | one of | `like` or `dislike`, the direction of the decision |
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

Stars and sentiment are deliberately separate: **stars carry strength, sentiment carries direction.**

| Signal | Verdict | Rank |
| --- | --- | --- |
| `stars: 0` | `rejected` | `0` |
| `stars: n` (n≥1) | `approved` | `n` |
| `verdict: approved` / `rejected` | as given | `stars` when present |
| `sentiment: like` | `approved` | `4`, or `stars` when both are present |
| `sentiment: dislike` | `rejected` | `1`, or `stars` when both are present |

The defaults are fixed constants, not judgement. Replay is ordered by `(timestamp, file position)`, so adopting a ledger twice produces a byte-identical result — `adopt` is idempotent and safe to re-run.

Sentiment never supersedes another element. A dislike rejects the element it names and nothing else; replacing one element with another is a `decide --supersedes`, which is a deliberate act.

## Generating the controls

Never hand-author element ids into a screen. Emit them from the ledger:

```bash
python3 scripts/bootstrap_harness.py controls --project-root . --out /tmp/controls.html
```

The markup carries `data-element`, `data-stars`, `data-rank` and `data-sentiment`, includes only elements in standing, and is byte-stable for a given ledger. Paste it into the screen, or inline it into a template.

## Wiring a companion that lacks handlers

If the companion has no rank/sentiment handling, add a listener that appends one line per click to the durable ledger:

```js
document.addEventListener('click', (e) => {
  const holder = e.target.closest('[data-element]');
  if (!holder) return;
  const star = e.target.closest('[data-rank]');
  const mood = e.target.closest('[data-sentiment]');
  if (!star && !mood) return;
  send({
    element: holder.dataset.element,
    stars: star ? Number(star.dataset.rank) : undefined,
    sentiment: mood ? mood.dataset.sentiment : undefined,
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
