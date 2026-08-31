---
type: Playbook
title: Visual verification
description: Browser-visible checks for generated screens and feedback controls.
status: stable
generated:
  by: codex/gpt-5
  at: 2026-08-20T23:57:30-05:00
---

# Verification

Every graphic that ever vanished in this project passed a string count first. This file is the list of ways that happened, so the next one is recognised instead of rediscovered.

## Counting markup is not verification

| What passed the check | What the user saw |
| --- | --- |
| `if "dh-fb{" not in html` — dedupe guard | host screen contained `.rev18 .dh-fb{`, so the whole stylesheet was skipped |
| `.dh-fb` (0,1,0) in the generator | host's `.rev18 .dh-fb` (0,2,0) won; controls unstyled |
| SVG present in the row | 170×220 artwork inside an 850×1100 transform frame — a corner fragment |
| `'data-rank="5"' in markup` | opening tag never closed; five controls, every attribute intact, **nothing drawn** |
| grep confirming a patch "landed" | the grep matched CSS selector *names*, not markup; the patch had silently no-opped |

## The rule

**A test that asserts on a string the generator just built proves only that the generator meant well.** Assert on what a parser builds from it.

`visible_controls()` in `bootstrap_harness.py` is the seam: it walks markup as a browser would and returns the text each control actually draws. `self-test` and `doctor` both use it. Substring checks belong alongside it, never instead of it.

## When a screen looks wrong

1. **Screenshot it.** Do not grep, do not reason about the CSS.
2. `doctor` fetches the **served page over HTTP**, not the file on disk — the server injects and caches `helper.js` at boot, so a correct file can be served with a stale helper that drops every click while looking fine. **Restart the companion after editing its code.**
3. `file://` tests layout only, never the scoring path.
4. Scripted measurement in a browser pane is unreliable — `javascript_tool` frequently runs against a stale `data:` tab. Verify which page you are on before trusting a number. Screenshots do not lie.

## Patching this skill's own code

Heredocs and Python f-strings collide badly. Write patch scripts to a file rather than piping them, and `assert` every anchor exists before `.replace()` — several patches have silently no-opped this way.

## Other working rules

- **Change only the elements this iteration names.** Rebuilding a screen from scratch silently drops every element it carried. If a change would drop one, record the supersede first.
- **Never substitute for approved artwork** — no emoji standing in for a drawn object, no placeholder where a ranked element exists.
- **Answer the question asked.** If the user repeats a complaint, you fixed something adjacent. Re-read their words before touching anything.
