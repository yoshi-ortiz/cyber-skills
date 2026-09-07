---
type: Reference
title: Quality improvement methods for project QA
description: A bounded guide to using Lean flow, quality-management principles, and statistical control in project assurance.
status: stable
resource: https://www.toyota-global.com/company/history_of_toyota/75years/data/automotive_business/production/system/change.html
tags:
  - project-management
  - quality-assurance
  - lean
  - quality-management
  - statistical-process-control
generated:
  by: codex/gpt-5
  at: 2026-09-06T00:00:00-06:00
sources:
  - resource: https://www.toyota-global.com/company/history_of_toyota/75years/data/automotive_business/production/system/change.html
    title: Toyota Production System: Basic concept
    author: Toyota Motor Corporation
  - resource: https://www.iso.org/obp/ui?_escaped_fragment_=iso%3Astd%3Aiso%3A9001%3Adis%3Aed-6%3Av1%3Aen
    title: ISO 9001 draft edition 6 preview, quality-management principles and process approach
    author: International Organization for Standardization
  - resource: https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc16.htm
    title: NIST/SEMATECH e-Handbook, What is Process Capability?
    author: National Institute of Standards and Technology
  - resource: https://www.itl.nist.gov/div898/handbook/ppc/section4/ppc45.htm
    title: NIST/SEMATECH e-Handbook, Assessing Process Stability
    author: National Institute of Standards and Technology
  - resource: https://www.itl.nist.gov/div898/handbook/ppc/section4/ppc47.htm
    title: NIST/SEMATECH e-Handbook, Checking Assumptions
    author: National Institute of Standards and Technology
---

# Quality improvement methods for project QA

## Purpose

The supplied Lean, total-quality-management, and Six Sigma articles point to
three different concerns. They should not be treated as one framework. For a
project QA loop, use each where its evidence fits:

| Method | QA question it answers | Evidence it needs |
| --- | --- | --- |
| Lean / Toyota Production System | Where does work wait, rework, or lose flow? | A visible work path and observations of queues, handoffs, or defects |
| Quality-management system | Are quality responsibilities, customer requirements, improvement, and decisions managed as a system? | Defined process ownership, acceptance requirements, measures, and review records |
| Statistical control / Six Sigma techniques | Is a measured process stable and capable of meeting a stated limit? | Operational definition, time-ordered observations, specification limits, and justified statistical assumptions |

Toyota describes its production system through Just-in-Time and jidoka.
Just-in-Time provides what is needed in the needed quantity at the needed time;
jidoka stops work when a problem is found. ISO quality-management principles
cover customer focus, leadership, people’s engagement, a process approach,
improvement, and evidence-based decision making. NIST defines process
capability as comparison of an in-control process with specification limits.

## Practical project QA loop

This application to project work is an inference from those sources, rather
than a claim that they prescribe a software process.

1. Define the customer-visible outcome and its acceptance limits. Record the
   owner, the measure, and what counts as conforming work.
2. Map the path from request through review, test, and release. Treat recurring
   waiting, unnecessary handoffs, and rework as flow problems to investigate.
3. Make a quality stop visible: a failed acceptance condition blocks the next
   step until its cause and correction are recorded.
4. Monitor a small number of measures over time. Establish stability before
   drawing capability conclusions, then compare the stable process with its
   stated limits.
5. Change one cause, repeat the same measure, and preserve the before/after
   evidence. The improvement is credible only if the acceptance limit and
   measurement method did not move to make it pass.

## Statistical boundary

A bell curve is a model, not a default fact about project data. NIST states
that capability indices compare process variation with specification limits and
that common indices such as `Cp` and `Cpk` rely on normal-distribution
assumptions. NIST also states that stability comes first: a stable process has
constant mean, variance, and distribution over time. Non-normality can result
from mixed sources, instability, or a process that is inherently non-normal.

Therefore, do not report a sigma level, capability index, or defects-per-million
figure for a project metric until its unit, opportunity count, specification
limits, sample independence, time ordering, and distributional assumptions are
documented. For sparse release incidents or ordinal review scores, trend and
cause analysis may be more defensible than a capability index.

## Boundaries

Lean flow does not prove statistical capability. Statistical capability does
not create management commitment or process ownership. A quality-management
system can define those responsibilities but still needs observed flow and
measured results. Keep the three evidence types separate in plans, dashboards,
and acceptance records.

The historical TQM and commercial Six Sigma material supplied with this request
is useful reading context. This note grounds its actionable claims in Toyota,
ISO, and NIST sources instead.
