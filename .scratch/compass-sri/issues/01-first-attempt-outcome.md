# Define positive feedback for first-attempt success

Label: wayfinder:grilling
Mode: HITL
Parent: [Build the complete Compass and SRI architecture report](../map.md)
Status: resolved
Assignee: user / Codex
Blocked by: none

## Question

Does explicit user acceptance itself satisfy “positive user feedback,” or must
an independently recorded positive sentiment also be present?

Recommendation: explicit acceptance counts as positive feedback, provided there
is no negative sentiment, correction, rejection or restart in that attempt's
history. This avoids requiring users to say the same approval twice. If separate
sentiment is required, missing sentiment remains unknown; it is never inferred.

The user's goal already requires first-attempt delivery with zero corrections.
An accepted retry and a later-resolved correction do not meet that goal. Technical
proof and hard vetoes still apply; current Item closure retains its own semantics.

Review these examples: “ship it” with no sentiment field; acceptance with explicit
neutral sentiment; acceptance after a correction; praise without acceptance;
acceptance after an earlier rejection on the same Shot.

Asset: [Build specification and plan](../../../roadmap/sri-compass.md).

## Resolution comment — 2026-09-07

The user answered the live clarification: “Require acceptance and separate
positive sentiment.” Both are required, independently recorded with user
provenance. Acceptance alone is insufficient. Missing sentiment is unknown;
explicit neutral sentiment does not qualify. The original question and
recommendation above remain as history, superseded by this answer.
