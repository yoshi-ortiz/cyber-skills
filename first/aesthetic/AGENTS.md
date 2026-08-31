# Working on this skill

For *using* the skill, read `SKILL.md`. This file is for changing it.

## The loop

Work one directory at a time.

```bash
python3 ../tools/check.py     # every gate in the repository, this skill's included
python3 scripts/golden_rules.py --design <spec.json> --min-coverage 0.8
```

`golden_rules` stays separate: it grades one design spec, so it needs a file
argument and has no repository-wide form for the runner to call.

| Step | Answers |
| --- | --- |
| `contracts` | does every directory honour its contract and budget? |
| `unittest` | does the behaviour claimed actually hold? |
| `self-test` | are ledger invariants intact? |
| `golden_rules` | what fraction of decisions are rule-pinned vs improvised? |

## Two metrics, deliberately separate

**Entry cost** — bytes of `SKILL.md`, paid every invocation.

**Golden-rule coverage** — determinism, not quality. A fully-declared wrong design repeats; an undeclared one re-rolls.

**Ledger coverage** — user-set ranks over standing elements. See `references/stats.md`. Not proof a round improved.

## Editing the article front end

Load `modern-web-guidance` before changing article CSS or script.

- **Measure the rendered page, never the source.**
- **Controls stylesheet ships after the article's.** Double `.dh-fb` to outrank.
- **Round zone inverts ground.** Build from the row's own ground, never `transparent`.

## Rules

- Red before green. Assert parsed structure, not generated substrings — see `references/verification.md`.
- Before adding SKILL.md prose, ask whether a tool could enforce it.
- This repository copy is canonical. Propagate it with the verified install command after editing.
- Restart the companion after editing `helper.js` or `frame-template.html`.

## Known debt

`bootstrap_harness.py` is over the 30 KB budget: 210 KB, down from 297 KB once the
browser assets moved to `screen/`. Split before adding to it — do not widen the
budget to silence the check.
