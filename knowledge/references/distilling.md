---
type: Playbook
title: Distilling a source into a concept
description: What survives the cut from a scraped page to a knowledge file, and what does not.
status: stable
generated:
  by: claude/opus-5
  at: 2026-08-23T12:20:00-05:00
---

# Distilling a source into a concept

The extract is raw material. A concept file is what is left after you decide
what this project will act on.

## The cut

Keep the shape that survives a version bump and the details this project calls.
Drop everything that is true of the source rather than of the work.

| Keep | Drop |
| --- | --- |
| The exact signature, flag, or schema you will call | The tour of everything else the library offers |
| The constraint that will bite: limits, ordering, idempotency, auth | Marketing copy, adoption numbers, testimonials |
| Failure modes and their error text | Changelogs, migration notes for versions you do not run |
| The version the claim held for | Anything you did not read in the extract |

A concept file that is longer than a careful reading of the source is not a
distillation, it is a copy with extra steps.

## One concept per file

Split when a file starts answering two questions. `prisma-migrate.md` and
`prisma-client-queries.md` beat `prisma.md`, because the next agent loads one
and pays for one. The join between them is `index.md`, not a heading.

## Every claim traces

If a sentence in the body is not supported by something in the extract, it does
not go in the file. Recall is not a source. When you need a fact the extract
does not carry, fetch a second source and add it to `sources`, rather than
filling the gap from memory and leaving the file looking cited.

Product and competitor research follows the same rule. What a competitor's page
claims is a claim, and the file says so: "their pricing page states X as of
`<date>`", never "their product does X".

## Trust boundary

Every row in `index.md` names what the concept may be used to decide. A
standards document and a vendor blog post are both sources, and they carry
different weight. Say which is which where the reader looks first:

| Concept | Purpose | Trust boundary |
| --- | --- | --- |
| [http-caching.md](http-caching.md) | Cache-Control semantics | RFC 9111, normative |
| [vendor-cdn-notes.md](vendor-cdn-notes.md) | One provider's defaults | Vendor documentation, may change without notice |

## Staleness

A version-bound claim gets `stale_after`. A file that outlives its dependency
is worse than no file, because it reads as verified. When a source moves,
re-run `okf.py new --force`, keep the old `sources` entry beside the new one,
and record in the body what changed. History in the file beats a silent
overwrite.
