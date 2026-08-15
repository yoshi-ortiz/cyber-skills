---
name: aesthetic
description: Evidence-backed design harness that keeps user decisions from being lost or invented. Use when starting design work from an inspiration corpus, when resuming a project that already has spec/design-harness/, or when collecting ranked design feedback from a browser companion. Covers art-direction, frontend, product, physical-space, copywriting, motion, composition and mockup-layering.
---

# Aesthetic

Design work fails in two ways: decisions get lost between sessions, and the agent invents feedback the user never gave. This harness exists to stop both. Everything else is optional.

**The one metric: did a rank the user actually set reach the ledger?** If no user click has landed, the session produced nothing, however many screens were made.

## Every session starts here

```bash
python3 scripts/bootstrap_harness.py doctor --project-root .
```

This sends a real click through a real socket and confirms it lands. It is the only statement about the companion you may make. **Never tell the user the companion works because you started it earlier** — check again, every time, before pointing them at a URL. The path has six links and each fails silently:

| Link | Fails as |
| --- | --- |
| Server process | dead; URL looks fine, nothing responds |
| Served screen | `/` serves **only the newest-mtime file** — write any screen after the scoring one and you have silently redirected the user |
| Scoring rows | screen has no `data-element` |
| Star + verdict controls | no `data-rank` / `data-verdict` |
| Component graphic | rows show ids, not the thing being judged |
| Socket round trip | clicks land nowhere — a `file://` tab does this, silently |

`doctor` red means stop and fix. Do not write another screen. Do not restate the URL.

Then read `spec/design-harness/DECISIONS.md` before proposing anything.

## Feedback is captured, never inferred

Ranks come from user clicks, adopted:

```bash
python3 scripts/bootstrap_harness.py adopt --project-root . \
  --companion-ledger .superpowers/brainstorm/decisions.jsonl
```

`adopt` reporting `0 adopted` means **no feedback was captured** — say so plainly rather than moving on.

Four signals, all user-set, each meaning one thing:

| Control | Meaning |
| --- | --- |
| **0 stars** | kill it — a real score, not a missing value |
| **1–5 stars** | strength |
| **👍 / 👎** | affinity, recorded independently of the verdict |
| **✓ check** | approve — locks the element into Standing |

Affinity is kept separate from verdict so "I like it but it is not settled" stays expressible. Never derive any of the four from prose.

`decide` is for agent inference only and is **capped at 1 star** by the tool. A higher rank must come from a click. If you catch yourself typing `--stars 4` from something the user said in chat, that is the bug this cap exists to prevent — ask them to click it instead.

```bash
python3 scripts/bootstrap_harness.py decide --project-root . \
  --element cover.ring.kicker --verdict proposed --stars 1 \
  --evidence "agent inference: corpus suggests a ring" --source agent
```

## Statistics

```bash
python3 scripts/bootstrap_harness.py stats --project-root .
```

Deterministic — same ledger, same numbers. Lead with **coverage**: the fraction of standing elements carrying a signal the user actually set. A high star average means nothing at 20% coverage, because the rest is agent inference. `conflicts` surfaces what an average hides (liked but scored low, disliked but still standing); `unscored` names exactly what still needs clicks.

## The scoring screen

Generate it. Never hand-write scoring markup — every hand-rolled variant so far has silently dropped the component graphic:

```bash
python3 scripts/bootstrap_harness.py controls --project-root . \
  --bg "#ffebb8" --ink "#111" --accent "#d9482a" --out controls.html
```

Every row carries the graphic being judged (`decide --preview`), zero-through-five, approve/reject, and a red banner that appears when the page is not wired to the companion — so a `file://` tab announces itself instead of eating clicks.

**Write the scoring screen last.** Anything written after it steals the `/` route.

## Evidence: cheap first

Look before you extract. A screenshot of two or three pages answers most questions:

```bash
sips -s format png --resampleWidth 1400 file.pdf --out /tmp/p.png   # then read the image
```

Byte-level extraction — parsing content streams, installing packages, hashing every page — is an **escalation the user opts into**, not the default. It is infeasible on small models and usually answers a question nobody asked. Corpus files are hashed once at `init`; that is the only automatic hashing.

## Working rules

- **Change only the elements this iteration names.** Rebuilding a screen from scratch silently drops every element it carried. If a change would drop one, record the supersede first.
- **Never substitute for approved artwork** — no emoji standing in for a drawn object, no placeholder where a ranked element exists.
- **Verify by looking.** "Verified structurally" is not verification. Render the screen and measure it: `file://` in a browser pane plus computed styles catches layout bugs a grep cannot. (`file://` tests layout only, never the scoring path — that is what `doctor` is for.)
- **Answer the question asked.** If the user repeats a complaint, you fixed something adjacent. Re-read their words before touching anything.
- Every visual move traces to a corpus cluster or a verbatim excerpt. Anything else is inference: label it, 1 star. See [anti-slop.md](references/anti-slop.md).

## Starting from scratch

```bash
python3 scripts/bootstrap_harness.py init --project-root . \
  --source-root /absolute/inspiration --profiles art-direction,composition
```

The user names the corpus path; never assume its directory name. It is read-only. Profiles are in [domain-profiles.md](references/domain-profiles.md); adapters and design MCPs in [design-tools.md](references/design-tools.md) — record what you actually observed with `preflight`, and never narrate a tool you did not run.

## Validation

```bash
python3 scripts/bootstrap_harness.py validate --project-root .
```

Reports ledger health and corpus drift **separately**. Corpus drift is usually the user reorganising files and does not block design work. A regenerated preview is a note, not a failure — re-record it when convenient.

For skill changes: `python3 scripts/bootstrap_harness.py self-test`.

## References

- [companion-contract.md](references/companion-contract.md) — what any companion must provide
- [anti-slop.md](references/anti-slop.md) — constraints against generic output
- [design-tools.md](references/design-tools.md) — adapters and design MCP servers
- [domain-profiles.md](references/domain-profiles.md), [sourcing-policy.md](references/sourcing-policy.md)
