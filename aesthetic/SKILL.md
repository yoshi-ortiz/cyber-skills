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
| Stale injected helper | served page looks right, clicks dropped — restart after editing `helper.js` |
| Component graphic | rows show ids, not the thing being judged |
| Invisible graphic | markup present, renders at 0px or as a corner fragment — host CSS beat the stylesheet |
| Socket round trip | clicks land nowhere — a `file://` tab does this, silently |

`doctor` red means stop and fix. Do not write another screen. Do not restate the URL.

Then read `spec/design-harness/DECISIONS.md` before proposing anything.

## What the signals mean

Read this before touching anything. Getting it wrong has cost whole sessions and destroyed approved work.

| Signal | Means | Does **not** mean |
| --- | --- | --- |
| **★ 1–5** | **Graphic execution quality** — how well the thing is drawn, ugly → beautiful. 1 is the worst execution. | Confidence, priority, or whether to do it at all |
| **↺ reset** | Clear the rating: "I have not judged this yet" | A score of zero. Clearing and "worst execution" are different statements |
| **👍 green** | This direction is right, keep going | That the drawing is good |
| **👎 red** | Not this direction | That the drawing is bad |
| **☑ reviewed** | "I have looked at this." A toggleable **status** | Approval, and it does **not** freeze the element — iteration continues after it |

**👍 with 2 stars is the most useful state in the system**, not a contradiction: *good idea, badly drawn yet*. The response is to **improve the drawing**. Never drop, supersede, or reject an element because its execution score is low — `stats` reports these under `polish`, not `conflicts`.

**A score never changes state.** Only an explicit verdict does. Reading a low score as "delete this" already destroyed work the user wanted kept.

## Feedback is captured, never inferred

Ranks come from user clicks, adopted:

```bash
python3 scripts/bootstrap_harness.py adopt --project-root . \
  --companion-ledger .superpowers/brainstorm/decisions.jsonl
```

`adopt` reporting `0 adopted` means **no feedback was captured** — say so plainly rather than moving on.

`decide` is for agent inference only and is **capped at 1 star** by the tool. A higher rank must come from a click. Record what you built so the row can say it:

```bash
python3 scripts/bootstrap_harness.py decide --project-root . \
  --element cover.ring.kicker --verdict proposed --stars 1 \
  --evidence "agent inference: corpus suggests a ring" \
  --implemented "ring at 96px with the kicker on the arc" --source agent
```

## Statistics

```bash
python3 scripts/bootstrap_harness.py stats --project-root .
```

Deterministic — same ledger, same numbers. Lead with **coverage**: the fraction of standing elements carrying a signal the user actually set. A high star average means nothing at 20% coverage, because the rest is agent inference. `conflicts` surfaces what an average hides (liked but scored low, disliked but still standing); `unscored` names exactly what still needs clicks.

## Scoring lives inside the prototype

Score the design where the user can see it. Put a placeholder naming the elements a section scores:

```html
<div data-dh-controls="cover.layout.two-column,cover.spine.right"></div>
```

Fill it and serve it — two commands, never by hand. `--pin` puts this turn's work on top:

```bash
python3 scripts/bootstrap_harness.py embed --project-root . --screen <screen>.html \
  --bg "#ffebb8" --ink "#111" --accent "#d9482a" --pin cover.spine.right
python3 scripts/bootstrap_harness.py publish --project-root . --screen <screen>.html
```

`embed` is **idempotent** — safe to re-run on a filled screen. It refuses a screen with no placeholder and refuses ids not in Standing. `publish` stamps the screen a clear margin ahead of every other, because the companion serves **only the newest-mtime file**.

**The skill owns the scoring UI. Never write scoring CSS in a project.** Every local patch has produced specificity fights and unusable controls. If a control looks wrong, fix `FEEDBACK_STYLE` in the generator so every project gets the fix — do not patch the screen.

Rows sort automatically: pinned first, then unresolved → reviewed → approved, best execution first inside each group. Each row shows the graphic, the proposal (`--evidence`) and what was built (`--implemented`).

**Write the scoring screen last, or re-run `publish`.**

## After editing the companion's own code

The companion caches `helper.js` at boot. If you change it, **restart the companion** — otherwise the served page carries a stale helper and every click is dropped while the page looks fine. `doctor` fetches the served page over HTTP and fails when the live flag is missing, so it catches this; the file on disk cannot tell you.

## Evidence: cheap first

Look before you extract. A screenshot of two or three pages answers most questions:

```bash
sips -s format png --resampleWidth 1400 file.pdf --out /tmp/p.png   # then read the image
```

Byte-level extraction — parsing content streams, installing packages, hashing every page — is an **escalation the user opts into**, not the default. It is infeasible on small models and usually answers a question nobody asked. Corpus files are hashed once at `init`; that is the only automatic hashing.

## "continue prototype" means the /prototype skill

When the user says **continue prototype**, they mean the `/prototype` skill driving the brainstorming companion — not "keep editing harness screens". Invoke it. This skill supplies the ledger, the scoring rows and `publish`; `/prototype` drives what gets built. They compose; they do not compete.

## Every turn must produce a design improvement

The user's measure: *sessions should be short and produce great design output on each input.* A turn spent fixing the scoring UI is a failed turn. If a control is broken, fix it **in this skill**, once, and move on — do not ask the user to re-specify what a star means.

## Working rules

- **Change only the elements this iteration names.** Rebuilding a screen from scratch silently drops every element it carried. If a change would drop one, record the supersede first.
- **Never substitute for approved artwork** — no emoji standing in for a drawn object, no placeholder where a ranked element exists.
- **Counting markup is not verification.** Every graphic that vanished in this project passed a string count: a stylesheet that never injected, a host rule with higher specificity, artwork scaled into a corner. `doctor` now requires each graphic to carry its own inline sizing and to contain real artwork — but when a screen looks wrong, **screenshot it** before claiming anything.
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
