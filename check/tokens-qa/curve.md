# Curve: feedback per Shot

Use this module after each observed user response to a Shot, or for `tokens-qa
curve`. It is a reporting module, not an additional installed Shot CLI command.

1. Bind the response to a Shot ID and cite its actual text or retained source.
   Preserve feedback events in order. Report acceptance, correction and pending
   status using the parent skill's rules. Never manufacture a response.
2. Build a table of Shot, response source, feedback, observed numeric score,
   score rubric and comparable cohort. Use a declared user rating when available;
   otherwise leave the numeric score `not_observed`. A task outcome remains
   categorical unless an explicit scoring rubric defines a numeric reward.
3. Show the per-response points in order. Where at least two comparable numeric
   observations have positive sample variance, overlay a Gaussian reference:
   `mu = mean(scores)`, `sigma = sample standard deviation(scores)` and
   `density(x) = exp(-0.5*((x-mu)/sigma)^2)/(sigma*sqrt(2*pi))`.
   Calculate with deterministic tooling. Label axes, sample count, rubric, mean
   and spread. Label the overlay **descriptive Gaussian reference**, not evidence
   of normality or an estimate of acceptance probability. With insufficient data
   or zero variance, show points and the reason the curve is unavailable.
4. Render with available plotting tools or a labeled text plot; retain the input
   table beside it. Update after each response, keeping changed rubrics or
   model/harness/task cohorts separate. Report missing observations explicitly.
   Done when every observed response is represented and the curve is reproducible
   from cited data, or its unavailable status is explicit.

“Reinforcement learning” here describes the feedback loop used to revise agent
instructions. This module performs no weight training. User acceptance and the
existing closure gate retain authority regardless of scores or curve shape.
