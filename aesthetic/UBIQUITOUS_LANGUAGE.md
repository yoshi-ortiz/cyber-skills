# Ubiquitous Language

## Scoring and ledger

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Element** | A stable dotted design decision, e.g. `cover.layout.two-column` | Component, layer, widget |
| **Standing** | An element in `proposed` or `approved` state. It is live on the page. | Active, current |
| **Rank** | User-set star score 0 to 5 for graphic execution | Rating, score alone |
| **Sentiment** | 👍 or 👎 on the *idea*. It never moves lifecycle state. | Verdict, approval |
| **Coverage** | User-set ranks ÷ standing elements | Completion, progress |
| **Polish** | 👍 sentiment with 2 stars or fewer. Redraw it. Do not drop it. | Fix, iterate |
| **Conflict** | 👎 sentiment with ≥4 stars | Contradiction |
| **Unscored** | Standing element with no user-set rank yet | Unranked (ambiguous with star 0) |

## Art direction and editorial work

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Corpus item** | One inspectable text or image source recorded in `corpus.json` | Hash, asset |
| **Observation** | A concrete statement about what a corpus item does | Vibe, filename |
| **Direction** | A thesis, signature move, visual system, and grounded evidence | Theme, style option |
| **Agent rank** | The agent's ordered comparison of three directions | Stars, user rank |
| **Execution stars** | A user's 0 to 5 judgment of one built element | Agent rank, direction score |
| **Work item** | A selected-direction deliverable with points and an acceptance check | Element, task card |
| **Work event** | An append-only move to Backlog, Doing, Review, or Done | Mutable status |
| **Burndown** | Remaining work-item points derived from work events | Coverage, completion guess |

## Corpus and knowledge

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Corpus** | Read-only inspiration folder the user named | Dataset, folder, sources |
| **OKF index** | `{corpus}/INDEX.md`. It catalogs claim ids and clusters. | Table of contents, manifest |
| **Claim id** | Stable citation key listed in INDEX.md → file#anchor | Fact, bullet |
| **Knowledge-index** | Text corpus routed through OKF + IA, not visual draw | Content library |
| **IA** | Information architecture: program → series → post | Layout, wireframe |

## Branches

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Continue** | Open the live page and advance a ranked design round | Resume, next |
| **Critique** | Judge standing work without setting ranks | Review, feedback |
| **Prototype** | Throwaway comp answering one question, with no cohort | Draft, mock |
| **Observe** | Read-only corpus interpretation | Analyze, ingest |

## Relationships

- A **Rank** never moves **Element** lifecycle; only an explicit **Verdict** does.
- **Agent rank** selects art direction. **Execution stars** judge built elements. They never share a field or file.
- A **Burndown** comes from **Work events**. User stars and ledger coverage cannot reduce it.
- **Sentiment** and **Rank** are independent signals on the same **Element**.
- **Coverage** counts **Rank** only, not **Sentiment**.
- **OKF index** precedes opening numbered corpus files; **Claim id** must exist in INDEX.md before citation.
- **Knowledge-index** stops at **IA**; visual foundations use the art path prefixes.

## Example dialogue

> **Agent:** "Coverage is 22%. **Polish** lists `cover.ring.kicker` at 👍 and 2 stars. Should this **continue** round redraw that id or pick **unscored** foundations first?"
>
> **Designer:** "Polish the ring. One redraw under `<cover.ring.kicker>.tighter`."
>
> **Agent:** "Recorded as agent **rank** 0 until you click. **Sentiment** stays yours. I won't set stars."
>
> **Designer:** "For the text folder, don't read every markdown file."
>
> **Agent:** "I'll read **OKF index** only, cluster **claim ids**, then open just the files INDEX points at for those clusters."

## Flagged ambiguities

- "Done" sometimes meant green unit tests. Canonical meaning is that the user has a PNG to compare and something to **rank**.
- "Harness" and "skill" differ. The skill is read-only during design. Project writes go through verbs on `spec/design-harness/`.
- "Quality", **coverage**, and golden-rule coverage are three different metrics. Only user judgment measures aesthetic quality.
