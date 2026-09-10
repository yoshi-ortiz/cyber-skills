---
name: fix
description: Restore broken code, decontaminate session context and set up missing agent tools. Use fix, rail, unstick or fix-context-derail to reread derailment evidence through Tokens QA, repair the cause and resume the active goal.
disable-model-invocation: true
exits: kit, owner
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
| `rail`, `unstick`, `fix-context-derail` | Fix the rail, then restore any tools blocking the next action |

Repair the observed cause: code, context or missing tools. Several may apply.
Use the target project's conventions and available session evidence; a repository,
roadmap and installed skill collection are optional. Keep repairs bounded to the
active goal, then return to its owner with a verified next action.

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

1. Pause the derailed action. Re-read the user's current instructions, earlier
   accepted decisions and the relevant project record. Reconcile stale records
   with actual user steering. Bind the goal, scope, failed attempt and missing
   evidence. Done when the intended next outcome is explicit.
2. Reuse [Tokens QA's command reference](../check/tokens-qa/commands.md). Resolve
   its installed script and call `shot-audit` on a JSON evidence bundle shaped
   as `{"turns": ["verbatim user turn", "later correction"]}`. Keep source turn
   references alongside the bundle. Include relevant corrections in chronological
   order, with any known omissions stated. This command calls the existing
   `feedback.audit()` module; keep classification rules in that owner.

   From this skill's directory in the package checkout:

   ```sh
   python3 ../check/tokens-qa/scripts/tokens_qa.py shot-audit --evidence /path/to/turns.json --json
   python3 ../check/tokens-qa/scripts/tokens_qa.py observe /path/to/shot.json --json
   python3 ../check/tokens-qa/scripts/tokens_qa.py correction /path/to/shot.json --json
   ```

   Run `observe` and `correction` when the corresponding Shot exists; use the
   bounded correction bundle for repair. Audit matches are advisory, so check
   each against the source words. When tools or records are absent, read the
   available evidence directly and mark automated analysis unavailable. Done
   when each derailment finding has a source, affected scope and repair target.
3. Decontaminate the next context load. Correct the owning stale pointer,
   conflicting instruction or admission declaration within authorized scope.
   Assemble the minimum continuation context: current goal, accepted decisions,
   relevant source paths, unresolved corrections, proof and next action. Keep
   unrelated material outside the next load and preserve original evidence.
   Existing conversation tokens cannot be erased by rewriting a file; when a
   fresh context is needed, prepare that handoff and use a supported reset or
   new-session mechanism only within existing authorization.
4. Retry the bounded action with available tools and inspect the resulting
   output and admitted-context evidence. Re-run `shot-audit` when new feedback
   arrives; a repeated correction remains history even after its cause is fixed.
   Done when the original failure is resolved with proof, or its precise blocker
   and next resolution step are recorded. Never infer hidden context is clean.

## Restore missing agent tools

1. Identify the capability required by the next action. Inspect available tools,
   executables and configuration before installing anything. Distinguish a missing
   tool from a disabled integration, expired authentication or wrong invocation.
   Done when the smallest required setup change is identified.
2. Set up that capability through its supported installer or configuration path,
   using current official documentation for the installed version. Reuse an
   existing equivalent when it satisfies the task. Keep setup local to the
   project or agent where possible and respect the host's permission boundaries.
   For managed skill installation, source sync or collection collisions, read
   [Kit](../kit/SKILL.md) and use its existing workflow; then return here to verify.
   Missing runtimes, CLI tools and MCP integrations use their own supported setup
   path. Record required credentials or user actions as blockers without guessing
   them. Done when configuration is applied or the exact blocking step is known.
3. Verify the capability from the agent's actual execution environment with a
   minimal representative operation, then retry the blocked action. If tool
   discovery requires restarting the session, save the focused handoff first.
   Installation success alone is insufficient. Done when the agent can use the
   tool for the intended action, or verification is explicitly pending.

## Resume and report

Return to the active goal using [Tokens QA's session compass](../check/tokens-qa/SKILL.md).
Report what changed, checks actually run, unresolved corrections and the next
bounded action. Use its closing RSI gains table; absent baseline or usage data
stays unknown. User acceptance remains distinct from technical verification.
