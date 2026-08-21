---
type: Contract
title: Companion contract
description: Durable independent feedback signals and browser surface requirements.
status: stable
generated:
  by: codex/gpt-5
  at: 2026-08-20T23:57:30-05:00
---

# Companion contract

## After a proposal

`doctor --quiet` confirms the path. Each link fails silently:

| Link | Fails as |
| --- | --- |
| Server process | dead; URL looks fine, nothing responds |
| Served screen | `/` serves **only the newest-mtime file** — a later write silently redirects the user |
| Scoring rows | screen has no `data-element` |
| Star + verdict controls | no `data-rank` / `data-verdict` on the row |
| Stale injected helper | page looks right, clicks dropped — restart after editing `helper.js` |
| Component graphic | rows show ids, not the thing being judged |
| Invisible graphic | markup present, renders at 0px or as a fragment — host CSS beat the stylesheet |
| Socket round trip | clicks land nowhere — a `file://` tab does this silently |

## Routing: newest mtime wins

`/` serves **only the newest-mtime file** in the session's `content/`. Write the scoring screen last, or `touch` it afterwards; any later write silently sends the user somewhere else.

## A file:// tab is not the companion

`helper.js` is injected only into served pages; clicks on a `file://` copy go nowhere. Generated controls carry an offline banner that hides once the helper connects.

Any browser surface may serve as the companion if it satisfies this contract.
`companion/` vendors one. Otherwise fall back to terminal `decide`; never invent
or remember clicks.

## What the companion must provide

1. **A durable ledger, outside any session directory.** Append-only JSONL, and a restarted companion must append to the same file. Anything scoped to one server run is orphaned on restart and is not a record.
2. **Design-element ids on every interactive control**, taken from the harness ledger — never invented per screen.
3. **Independent signals** per element, none implying another: a 0–5 star rank (`data-rank`, where **the zero is `data-rank="0"`** — a rank like any other), an encouragement thumb (`data-sentiment`), and a `completed` toggle (`data-verdict`).
4. **One line appended per interaction** — no batching, debouncing or deduplication. Replay order is the harness's job, not the companion's.
5. **A refresh must not discard what the user clicked.** The served screen is a baked snapshot: without this the user scores twenty rows, reloads, and watches every one revert to what the agent last published. The generated controls carry their own rehydrator — a companion must not strip inline scripts from the screens it serves.

### The zero is a rank, not a reset

Emitting the zero as `data-reset` is the one shape this contract forbids: the obvious handler for a control named *reset* clears the row, and that destroys the thumb and the tick, two signals a score may never touch. Routed through `data-rank="0"` it scores 0 and changes nothing else, as §Deterministic semantics requires of every score.

Two observed traps:

- **Do not light the zero from `rank <= stars`.** It is true for every score, so a 5-star row draws `0 1 2 3 4 5` all lit at once. The zero is on only when the score *is* zero.
- **Do not place the zero inside the star strip.** Unlabelled and a pixel from the first star, it collects the clicks meant for a 1 — and before the point above was fixed, a mis-hit zero also wiped the thumb.

## Event schema

One JSON object per line. Unknown fields are ignored; these are the contract.

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

At least one of `stars`, `verdict` or `sentiment` must be present. An interaction with none, or with no `element`, **cannot bind** — the harness skips it and reports the count. Fix that by giving the control an id, never by guessing one.

```json
{"element":"cover.layout.two-column","stars":5,"text":"user: 'c2'","timestamp":1786745271000}
{"element":"cover.ring.kicker","sentiment":"like","timestamp":1786745272000}
```

## Deterministic semantics

**A score never changes state.** Stars rate execution; only an explicit verdict
moves lifecycle. Never map `stars: 0` to `rejected`.

| Signal | Effect on state | Effect on rank |
| --- | --- | --- |
| `stars: n` (0–5) | **none** — stays where it is; a new element arrives `proposed` | `n` |
| `reset` (the zero control) | **none** | `0` — judged, and judged bad |
| `sentiment: like` / `dislike` | **none** — recorded as encouragement only | unchanged |
| `verdict: completed` | → `completed` (a toggleable status, *not* a lock) | `stars` when present, else unchanged |
| `verdict: approved` / `rejected` | as given | `stars` when present, else unchanged |

`0` and "unrated" are different things and the number does not distinguish them — `scored` does. An element nobody has touched is `scored: false`; one scored zero is `scored: true, stars: 0` and counts toward coverage. It has been judged.

A `rejected` or `superseded` element stays in that lifecycle when it receives a
fresh score. Rank measures execution and cannot express renewed scope. Sentiment
never supersedes or rejects anything; replacing one element with another is a
deliberate `decide --supersedes`.

Replay is ordered by `(timestamp, file position)`, so adopting a ledger twice is byte-identical — `adopt` is idempotent and safe to re-run.

### Groups

Rows group by lifecycle and **nothing is ever hidden**:

| Group | Label | States |
| --- | --- | --- |
| `brainstorming` | Lluvia de ideas | `proposed` |
| `developing` | En desarrollo | `completed`, `approved` |
| `rejected` | Descartado | `rejected`, `superseded` |

Rejected work stays on screen, dimmed, with live controls. A rejection is undone by clicking, never by editing JSON.

### `polish`

An element with a `like` and a low star rank is **`polish`**, not a conflict: the idea is good, the execution is not there yet. Redraw it. Never drop it.

## Generating the controls

Never hand-author element ids into a screen: emit them from the ledger with `controls`, or better `embed`, which fills `data-dh-controls` placeholders in place and is idempotent (see `commands.md`). The markup carries `data-element`, `data-stars`, `data-rank` (including the zero), `data-sentiment`, `data-verdict` and `data-group`, renders every element including rejected ones, and is byte-stable for a given ledger.

The generator owns the strip's design. Do not restyle it in a project: local CSS outranks the generator's and is how the controls went invisible before.

## Wiring a companion that lacks handlers

A companion with no rank/sentiment handling needs a listener that appends one line per click to the durable ledger:

```js
document.addEventListener('click', (e) => {
  const holder = e.target.closest('[data-element]');
  if (!holder) return;
  const star = e.target.closest('[data-rank]');
  const mood = e.target.closest('[data-sentiment]');
  const mark = e.target.closest('[data-verdict]');
  if (!star && !mood && !mark) return;
  send({
    element: holder.dataset.element,
    stars: star ? Number(star.dataset.rank) : undefined,
    sentiment: mood ? mood.dataset.sentiment : undefined,
    verdict: mark ? mark.dataset.verdict : undefined,
    text: holder.dataset.label || null,
    timestamp: Date.now(),
  });
});
```

`send` is whatever reaches the durable ledger. The only hard requirement is that the line lands outside the session directory.

## Adopting

Run `adopt` (see `commands.md`) in the same turn the feedback arrives. Feedback that is not adopted is lost at the next session boundary.

## Theme controls

Keep **Agent settings** collapsed in the status aid. **Update app theme** is off by default. **Saved themes**, **Reset theme**, and **Save** use `spec/design-harness/theme.json`. An unsafe color or font change rolls back one setting at a time, never the whole theme.

## Provenance

Everything `adopt` ingests is recorded `source: user`. Anything the agent types with `decide` is `source: agent`, stored at 0★ until the user ranks. That distinction is the point: before it existed, a user's click and an agent's guess were indistinguishable in the ledger.
