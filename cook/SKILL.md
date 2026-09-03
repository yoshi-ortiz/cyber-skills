---
name: cook
disable-model-invocation: true
description: Dev-only. Run this repository's skills against a throwaway project and assert what the person who ran it would actually see, so a success-shaped exit code cannot stand in for a working screen. Also reads a finished run back against what the user asked for, to catch a round that heard a complaint or a correction and changed nothing.
---

# Cook

Food Product development: run the skill the way a user runs it, then check the page,
not the exit code.

## Who "the user" is

Whoever ran the skill. Designers and people with no coding background are the
main target and set the bar -- if the failure is only legible as a stack trace,
it is not reported. But nothing here is written *down* to them: a highly
technical user gets the same run, and every finding names the file, the check
and the exact command that reproduces it. One report, no beginner mode.

Say "the user". `cook` runs skills that are not about design, and "designer"
smuggles one skill's audience into a loop meant for all of them.

## What is skill-agnostic, and what is not

| Command | Reach |
| --- | --- |
| `feedback` | any skill -- it reads the transcript and git, nothing else |
| `route`, `deliver` | any skill -- they resolve names and read git, and own no rules |
| `run`, `doctor`, `prove` | `aesthetic` only, today |

`run` and `doctor` drive `bootstrap_harness.py` and parse its companion markup
(`dh-fb`, `data-rank`, `dh-shot`), so they are aesthetic-shaped by construction.
That is not a defect to fix in advance: no second skill in this catalog serves a
screen. When one does, the split to make is the parser, and `feedback` already
shows the shape -- read what is universal, refuse to learn one skill's files.

Fog. `cook` ships on no channel; it is registered in `tools/fog.py` FOG_DIRS
and `tools/skill_discovery.py` SKIP. Do not index it in any README.

## Run it

```bash
python3 cook/cook.py run    --project-root /tmp/cook-run   # open a round, then check it
python3 cook/cook.py doctor --project-root /tmp/cook-run   # check an existing round
python3 cook/cook.py clean  --project-root /tmp/cook-run
python3 cook/cook.py feedback --project-root .             # the real project, read-only
python3 cook/cook.py feedback --project-root . --session <file.jsonl>
python3 cook/cook.py feedback --project-root . --invocation aesthetic@<stamp>
python3 cook/cook.py route                                 # do the routed skills resolve
python3 cook/cook.py prove   --project-root /tmp/cook-prove  # the real path, with a Shot
python3 cook/cook.py deliver --project-root .              # the release boundary, reported
```

## The route

A round walks `zoom-out`, then `diagnosing-bugs`, then `ponytail-review`, and
stops at reviewed commit and push. `route` resolves those three against the
installed skills directory and fails naming any that are missing, because a
route that only resolves on the machine that wrote it is not a route.

Each step is a name, a path and one line saying why it is there. **Cook owns
the ordering and nothing else.** The moment a step carries the routed skill's
rules, those rules live in two places and the copy here is the one that goes
stale. `cook/route.py` is the table; the doctrine stays in the skill it points
at.

`zoom-out` is in no install manifest today (R-43), so on a clean host expect it
to be the one that does not resolve. That is a real finding, not a bug in the
resolver.

## One run, one identity

A transcript holds many runs. Each is bounded at both ends by the start of the
next one, and carries a `run_id` of `skill@timestamp`. That id scopes the turns,
the working tree and the commits, and it is what a Shot records in
`inputs.invocation`, so the session, the artifact, the table and the feedback
all join by one identity rather than by "most recent".

`git status --porcelain` carries no clock, so before this a tree that was
already dirty counted as the run having changed something, and a round that
heard a complaint and edited nothing passed on somebody else's work.

`feedback` is the only command that reads the repository, because the thing it
reads -- the transcript of the run and what that run changed -- exists nowhere
else. It writes nothing.

Only Claude Code's transcript directory is wired in, because it is the only
layout with a session here to test against. Every other agent app arrives
through `--session`, which is a path you can verify, rather than a guess about
somebody's filesystem that silently matches nothing.

Exit 0 means a user opening that URL sees a rankable screen. Exit 1 names
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
| `preview-renders` | every ranked row's graphic actually draws, and points inside the served document |

The first reads the filesystem and the second reads HTTP, on purpose. They fail
independently, so a green pair is two witnesses rather than one restated twice.

`preview-renders` exists because the other three passed a row that was
structurally perfect and visually empty: its only graphic was `<img
src="../shots/...">`, and the companion serves from its own session directory,
so the path resolved to nothing and the user scored a white rectangle.
Rankable markup is not a visible proposal.

## The second goal: did the run absorb what the user said

`doctor` answers one question -- can the user see a working screen. This
answers a different one with different evidence, and a round can pass either
while failing the other.

```bash
python3 cook/cook.py feedback --project-root .
```

Eating your own food is not only checking that the page renders. It is checking
the render against the brief and against what the user told you, which is why
this reads two sources and compares them:

| Source | What it carries |
| --- | --- |
| the agent transcript | the user's own words, questionnaire answers included |
| git | what the run actually changed -- edits and commits since it began |

Those two, and nothing else. `feedback` reads no skill's state files: the moment
it knows what `decisions.json` means, cook stops being a loop any skill can run
and becomes part of one project's shot. A skill that wants its own ledger
checked owns that check.

The read is **scoped to the skill run**. A transcript opens with the skill's own
payload, and that marker names the skill directory and the moment it started;
complaints logged before it are about something else, and a transcript in which
no skill ran is not evidence about a skill at all.

Git is the universal half. Two of the three skills in this catalog keep no
project state by contract, so "did this run change anything" has to be
answerable without a ledger -- edits **and** commits since the run began,
because a committed fix leaves the working tree clean and used to read as
"changed nothing".

## Complaints, and the corrections that matter more

A complaint is a symptom: *"it's broken"*. A **correction** names an
instruction the run did not follow: *"I asked for X"*, *"you did not Y"*,
*"it should be Z"*. The second is the harder failure, because the run can look
busy while the requirement stays outstanding.

Whether an instruction was satisfied is a judgement cook cannot make. That the
user had to give it twice is a fact, and it is the same evidence: **an
instruction restated is an instruction that did not land**, and it fails the
round on its own, however many files moved.

Frustration keywords are English and imperfect, so they never fail a round
alone -- only together with an unchanged tree.

Questionnaire answers arrive as tool results rather than user turns. Dropping
them loses exactly the sentence where a user says the round is wrong, so they
are extracted too.

## Why this exists

`bootstrap_harness.py open` returns a live URL and exit 0 whether or not a
screen was ever published, while its docstring promises it "restores the last
ranking page". `user-communication.md` then requires the agent to lead its
first reply with that URL. The result is a user handed a link to
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
review the diff. `cook deliver` reports that boundary: the four reviews R-74
names, which of them you have confirmed, and the tree state a reviewer needs.
It reads git and writes nothing, and **there is no flag that commits, pushes or
publishes** -- the same way `run` has no flag to open the repository as a
project root. Report the exact checks and ask the user to confirm. After
approval: commit the reviewed files, push the current branch, verify the remote
contains the commit.

**Pushing `dev` installs nothing.** `kit sync` clones the channel branches, so
a `dev` commit is invisible to it until a channel carries it. Verifying the
installed copies straight after a `dev` push asserts something that cannot be
true yet, and the honest read of a clean sync there is "nothing new was
published", not "the release worked".

Publishing a channel is a second decision, and which channel is a third:
`main` is what every user installs. Name the channel, get it confirmed, then
`python3 tools/release.py --channel <name> --push`, then `kit sync
cyber-skills`, then verify the installed copies carry that commit's behavior.
The work is finished only after those facts are reported; a local green tree
is ready to release, not released.
