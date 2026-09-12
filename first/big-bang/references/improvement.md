---
type: Playbook
title: Focused cleanup and improvement
description: Use delivery evidence to improve code and reviewed instructions without expanding the active Item.
status: stable
---

# Focused cleanup and improvement

Compass selects work. The improvement loop uses observed results to propose,
verify and retain a better implementation or instruction. Here RSI means
recursive self-improvement of the workflow, called SRI in this repository;
it changes project artifacts and reviewed instructions, not model weights.

1. **Observe.** Record the concrete failure, correction or maintenance obstacle,
   the affected acceptance criterion and its reproduction. Separate observed
   evidence from hypotheses. Done when the problem can be checked independently
   of the proposed fix.
2. **Bound.** Include cleanup when it is needed to deliver the selected Item.
   For broader cleanup, create a separately selectable roadmap Item with scope,
   preserved behavior and proof. Load owning code, callers and relevant tests;
   expand context to resolve specific dependency or behavior questions. Done when
   the intended change has a bounded surface and a baseline.
3. **Repair.** Remove verified dead paths, consolidate duplicated ownership or
   simplify the responsible module as the evidence warrants. Check callers and
   public compatibility before deletion. Verify preserved behavior through the
   existing public checks and reproduce the original failure after the fix.
   Done when the cause is addressed and applicable regression checks pass.
4. **Evaluate.** For repeated agent failures, propose one instruction or fixture
   change tied to the observed cause. Compare a frozen baseline and candidate on
   comparable tasks with fixed model, harness, budget and acceptance criteria.
   Keep evaluation tasks separate from tasks used to tune the candidate. Count
   failed attempts, corrections and cumulative cost; missing usage stays unknown.
   Preserve required-context coverage and accepted outcomes. Done when evidence
   supports promotion or the candidate is explicitly rejected or unevaluated.
5. **Retain.** Apply instruction changes within the authorized scope and required
   project review process. Keep acceptance, sentiment and technical proof separate;
   fixtures cannot establish user satisfaction. Record the evidence and update
   the single owning instruction, test or source file. Leave speculative lessons
   as proposals. Done when the change is traceable and reversible.

At handoff, retain the Item ID, contract and owner paths, decisions, current
proof, blockers and next action. Refer to source files instead of carrying full
logs or unrelated modules forward. Optimize measured delivery cost while keeping
required context; a smaller prompt alone is not evidence of better results.
