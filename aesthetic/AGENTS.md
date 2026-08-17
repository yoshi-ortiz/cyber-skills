# Working on this skill

For *using* the skill, read `SKILL.md`. This file is for changing it.

The failure mode this workflow exists to break: the skill only ever learned by hurting the user. Every defect was found because a user hit it, never because a test caught it — `doctor` went green immediately before rejection five times in one session, and the majority of that session's turns were the user doing QA on the harness instead of reviewing design.

## The loop

Work one directory at a time. Never open more than the directory you are changing.

```bash
python3 scripts/contracts.py --root .          # 1. does every dir honour its contract?
python3 -m unittest discover -s scripts -p 'test_*.py'   # 2. red -> green
python3 scripts/bootstrap_harness.py self-test # 3. harness invariants
python3 scripts/golden_rules.py --design <spec.json> --min-coverage 0.8
```

Each step answers a different question, and none substitutes for another:

| Step | Answers |
| --- | --- |
| `contracts` | is this directory still what it says it is, and within budget? |
| `unittest` | does the behaviour I just claimed actually hold? |
| `self-test` | are the ledger's invariants intact? |
| `golden_rules` | how much of a design is pinned by a rule vs. improvised? |

## Every directory declares itself

Each directory carries a `CONTEXT.md` with `purpose`, `admits`, `refuses` and `max_file_bytes`. `contracts.py` validates one directory against its own contract and does not descend — that is what makes this incremental.

Adding a file is a two-part act: write the file, and check it against the contract of the directory you put it in. If it does not fit, the answer is usually a different directory, not a wider contract.

**Budgets are load-bearing.** `SKILL.md` reached 18,121 bytes (~4,493 tokens, loaded on *every* invocation) because nothing bounded it. It is now ~3,263 bytes (~816 tokens). Knowledge-index interpret lives in `references/interpret-knowledge.md`. Visual interpret lives in `references/interpret-art.md`. Comparators: `prototype` ~738 tokens, `modern-web-guidance` ~1,406, `ponytail` ~1,659.

## Two metrics, deliberately separate

**Entry cost** — bytes of `SKILL.md`, paid every invocation. Bounded by the root contract.

**Golden-rule coverage** — what fraction of a design's decisions are pinned by a checkable rule rather than improvised. This is the determinism metric. It is *not* a quality score: a fully-declared design can be fully wrong, and that is a good outcome, because a wrong answer that repeats is one you can fix. An undeclared decision varies per run and cannot be fixed, only re-rolled.

Raising coverage makes runs agree. Fixing failures makes them good. Do not conflate them.

## Rules for changing this skill

- **Red before green.** The regression test goes in first and you watch it fail. A test written after the fix asserts what the fix does, not what the bug was.
- **Assert on parsed structure, never a substring of generated output.** Every graphic that vanished here passed a string count first. `visible_controls()` is the seam. See `references/verification.md`.
- **Before adding prose to `SKILL.md`, ask whether a tool could enforce it.** Prose that duplicates tool behaviour drifts out of sync with the tool — that is how `companion-contract.md` came to contradict `SKILL.md` and nearly reintroduced a bug that deleted the user's work.
- **Canonical is the iCloud copy.** rsync to `~/.agents/skills/aesthetic/` after editing, then commit. Two copies have already shipped contradictory behaviour.
- **Restart the companion after editing its code** — `helper.js` is cached at boot, and a stale helper drops every click while the page looks correct.

## Known debt

`scripts/bootstrap_harness.py` is 83 KB against a 30 KB budget and `contracts.py` reports it on every run. That is deliberate: the deep module inside it is the ledger, while `init`/`preflight`/`validate` are scaffolding. Split it before adding to it — do not widen the budget to silence the check.
