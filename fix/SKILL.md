---
name: fix
description: Something is broken. Restore it, then return to the family that owns it. Routes diagnosing-bugs and systematic-debugging for a defect in the code, and poteto-mode when the session itself has derailed. Use when the user says fix, rail, unstick, or fix-context-derail, reports a crash, a regression, or a failing test, or says the agent has lost the plot and is working on the wrong thing.
disable-model-invocation: true
anchors:
  fix-context-derail: Fix the rail
aliases:
  - rail
  - unstick
---

# Fix

A bare on-ramp. Fix is entered from outside the sequence, at the moment
something stops working, and it ends by handing the restored path back to the
family that owns it.

| Say | Do |
| --- | --- |
| `fix` | Read the symptom, then pick the section it belongs to |
| `rail`, `unstick`, `fix-context-derail` | Fix the rail. The code is fine and the session is not |

Two different breakages, one reflex. The code is wrong, or the work is. Both are
a write, which is why the rail lives here and not in `check`.

An installation or collection problem is not this skill. A skill that arrived
wrong, a domain that never synced, two skills colliding: that is `kit`, which
answers to `doctor`, `repair`, `troubleshoot`, and `conflict`.

## Fix the code

| Reach for | For |
| --- | --- |
| **diagnosing-bugs** | A reported defect. Reproduce, minimise, hypothesise, instrument, fix, regression-test |
| **systematic-debugging** | The same loop when the first pass did not reach a root cause |

Reproduce before you theorise. A fix written against a symptom you have not
seen fail is a guess that happens to be committed.

Trace each symptom to its cause and keep asking why until the answer stops
being a restatement of the symptom. A patch at the point of the error, when the
error came from three frames up, moves the bug rather than removing it.

The fix ends with the failing case as a test. In this repository the incident
and its root cause go to `BUGS.md`, and the work that follows goes back to
`build`.

## Fix the rail

The code runs. The session has drifted: the agent is working on something
nobody asked for, has lost the accepted contract, or is patching around a
decision instead of applying it.

| Reach for | For |
| --- | --- |
| **poteto-mode** | Re-entering a disciplined run with the principles and the playbook made explicit again |

Stop first. More output on a derailed session buys nothing, and a long stretch
of work in the wrong direction is more expensive to unpick than to abandon.

Then re-read the record rather than the conversation. The accepted spec, the
roadmap item, and the state of the work as written down outrank anything either
side remembers about it.

Return to the family the work belonged to when it derailed. Fix restores the
path. It does not take ownership of the work that was travelling on it.
