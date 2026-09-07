# Choose the field cohort and promotion rule

Label: wayfinder:grilling
Mode: HITL
Parent: [Build the complete Compass and SRI architecture report](../map.md)
Status: open
Assignee: unassigned
Blocked by: [Define positive feedback for first-attempt success](01-first-attempt-outcome.md)

## Question

Which real invocation and user-reviewed task cohort will evaluate the chosen
first-attempt outcome, and what sample, observation window and comparison rule
are sufficient to promote one instruction change?

Recommendation: start with the existing Aesthetic moodboard invocation and a
fixed baseline/candidate instruction pair. Use disjoint tasks for development and
held-out evaluation, retain all assigned outcomes, and predeclare the cohort and
decision rule before inspecting held-out results. Choose a second real invocation
only when its evidence is available; do not build hypothetical adapters.

Set the assignment method, cohort inclusion/exclusion rules, sample size,
feedback window, treatment of pending/abandoned attempts, acceptable recall floor,
and uncertainty reporting. Hold the model, harness, tokenizer profile, criteria
and relevant budget fixed within comparisons. Identify the actual reviewer and
available telemetry. Never choose a sample size from how many favorable outcomes
already exist.

The final criterion uses the outcome settled in the prerequisite ticket. Field
evidence may be unavailable; record that condition without inventing observations
or blocking the deterministic implementation work.

Asset: [Build specification and plan](../../../roadmap/sri-compass.md).
