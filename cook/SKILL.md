---
name: cook
description: Dev-only. Run this repository's skills against a throwaway project and assert what a designer would actually see, so a success-shaped exit code cannot stand in for a working screen.
---

# Cook

Food Product development: run the skill the way a user runs it, then check the page,
not the exit code.

Fog. `cook` ships on no channel; it is registered in `tools/fog.py` FOG_DIRS
and `tools/skill_discovery.py` SKIP. Do not index it in any README.

## Run it

```bash
python3 cook/cook.py run    --project-root /tmp/cook-run   # open a round, then check it
python3 cook/cook.py doctor --project-root /tmp/cook-run   # check an existing round
python3 cook/cook.py clean  --project-root /tmp/cook-run
```

Exit 0 means a designer opening that URL sees a rankable screen. Exit 1 names
what they would see instead. Exit 2 means the round was refused before it ran.

## The two rules

**A project root inside this repository is refused, with no flag to open it.**
A Food Product round writes corpus, ledger, renders, and companion sessions. Writing
them beside the skill source that produced them puts the **skill package** and
one project's **shot tests** in one tree, and an agent reading that tree cannot
tell which it is in. That is the context derail in the root `CONTEXT.md`,
arriving through the filesystem instead of a document.

**A page `cook` cannot read is a failure, never a pass.** Default deny. The
first version of `not-placeholder` parsed `/?key=`, which is only a redirect
shim, found no heading, concluded "not the placeholder", and went green against
the exact empty page it existed to catch. An assertion that cannot see the page
has not checked it.

## What it checks

| Check | Green when |
| --- | --- |
| `screen-published` | some session's `content/` holds an html the companion can serve |
| `not-placeholder` | the served document is a screen, not the empty-companion shell or a key refusal |
| `screen-is-rankable` | a real decision row carries its own `data-rank` control |

The first reads the filesystem and the second reads HTTP, on purpose. They fail
independently, so a green pair is two witnesses rather than one restated twice.

## Why this exists

`bootstrap_harness.py open` returns a live URL and exit 0 whether or not a
screen was ever published, while its docstring promises it "restores the last
ranking page". `user-communication.md` then requires the agent to lead its
first reply with that URL. The result is a designer handed a link to
"Waiting for the agent to push a screen...", with every gate in the repository
green, because every one of them reads an exit code.

`open` starts a server. `article` then `publish` put something on it.

## Diagnose red rounds

Use an available diagnostic skill before proposing a cause. Prefer
`diagnosing-bugs` (including Matt Pocock's diagnostic skill when installed),
then `systematic-debugging`. Give it the exact failing Cook command and keep
that command as the feedback loop. A generic button, a zero exit code, or a
plausible theory is not evidence that the visible workflow works.

## Finish the Food Product release

After Cook is green, run the affected tests and `python3 tools/check.py`, then
review the diff. Report the exact checks and ask the user to confirm commit and
push. Do not silently cross that release boundary. After approval: commit the
reviewed files, push the current branch, verify the remote contains the commit,
run `kit sync cyber-skills`, and verify the installed Cook/Aesthetic copies
contain that commit's behavior. The work is finished only after those facts are
reported; a local green tree is ready to release, not released.
